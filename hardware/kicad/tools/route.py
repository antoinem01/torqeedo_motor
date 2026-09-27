import pcbnew, numpy as np, sys, json, math, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # router.py sits next to this file
from router import *

S = sys.argv[1]
IN, OUT = sys.argv[2], sys.argv[3]
BW, BH = 100.0, 80.0
HOLES = [(5,5),(95,5),(5,75),(95,75)]

board = pcbnew.LoadBoard(IN)
g = Grid(BW, BH, HOLES)

# ---------- obstacles from pads ----------
padinfo = {}          # net -> list of (x, y, layers, cellcenter)
padcells = {}         # net -> set of (layer,i,j)
inpad = np.zeros((g.ny, g.nx), bool)
for fp in board.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        x0,y0,x1,y1 = bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6
        net = p.GetNetname()
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            net = '__hole__'
        layers = []
        if p.IsOnLayer(pcbnew.F_Cu): layers.append(F)
        if p.IsOnLayer(pcbnew.B_Cu): layers.append(B)
        if not layers: layers = [F, B]
        g.add_rect(net, x0, y0, x1, y1, layers)
        i0 = max(int((x0-0.1)/CELL),0); i1 = min(int((x1+0.1)/CELL)+1, g.nx)
        j0 = max(int((y0-0.1)/CELL),0); j1 = min(int((y1+0.1)/CELL)+1, g.ny)
        inpad[j0:j1, i0:i1] = True
        if net.startswith('/'):
            pos = p.GetPosition()
            cx, cy = pos.x/1e6, pos.y/1e6
            ci, cj = g.cell(cx, cy)
            padinfo.setdefault(net, []).append((cx, cy, tuple(layers), (ci, cj), f"{fp.GetReference()}.{p.GetNumber()}"))

tracks = []   # (net, layer, (x0,y0), (x1,y1), width)
vias   = []   # (net, x, y)

def commit(net, path, blk=None, exact_start=None, exact_end=None):
    w = float(wof(net))
    runs = simplify(path)
    pts_all = []
    for L, pts in runs:
        if blk is not None and len(pts) > 2:
            pts = taut(blk, L, pts)
        coords = [(float(i)*CELL, float(j)*CELL) for (i, j) in pts]
        pts_all.append((L, coords))
    if exact_start: pts_all[0][1][0] = exact_start
    if exact_end:   pts_all[-1][1][-1] = exact_end
    covered = set()
    def cells_on(L, a, b):
        i0, j0 = int(round(a[0]/CELL)), int(round(a[1]/CELL))
        i1, j1 = int(round(b[0]/CELL)), int(round(b[1]/CELL))
        di, dj = i1-i0, j1-j0
        n = max(abs(di), abs(dj))
        for k in range(n+1):
            t = k/n if n else 0.0
            covered.add((L, int(round(i0+di*t)), int(round(j0+dj*t))))
    for k, (L, coords) in enumerate(pts_all):
        for a, b in zip(coords, coords[1:]):
            if a != b:
                tracks.append((net, L, a, b, w))
                g.add_seg(net, a[0], a[1], b[0], b[1], w/2, [L])
                cells_on(L, a, b)
        if k + 1 < len(pts_all):
            vx, vy = coords[-1]
            vias.append((net, float(vx), float(vy)))
            g.add_circ(net, vx, vy, VIA_D/2, [F, B])
            ci, cj = int(round(vx/CELL)), int(round(vy/CELL))
            covered.add((F, ci, cj)); covered.add((B, ci, cj))
    return covered

# ---------- ground: drop a via from every SMD GND pad into the B.Cu plane ----------
t0 = time.time()
gnd_ok = gnd_fail = 0
for (cx, cy, layers, (ci, cj), name) in padinfo.get('/GND', []):
    if len(layers) == 2:            # THT pad: already meets the plane
        continue
    blk = g.blocked_for('/GND', CLEAR + wof('/GND')/2)
    vb  = g.blocked_for('/GND', CLEAR + VIA_D/2)
    viaok = (~vb[F]) & (~vb[B]) & (~inpad)
    targets = np.zeros((2, g.ny, g.nx), bool)
    targets[B] = ~blk[B]            # anywhere on the back plane will do
    path = astar(g, blk, viaok, [(layers[0], ci, cj)], targets)
    if path is None:
        print(f"  GND via FAILED for {name}"); gnd_fail += 1; continue
    commit('/GND', path, blk=blk, exact_start=(cx, cy))
    gnd_ok += 1
print(f"GND stitching vias: {gnd_ok} placed, {gnd_fail} failed  ({time.time()-t0:.1f}s)")

# ---------- signal nets ----------
ORDER = ['/XTAL1','/XTAL2','/AREF','/AVCC',
         '/RS485_DI','/RS485_RO','/RS485_DE',
         '/TERM_MID','/BIASA_MID','/BIASB_MID','/BUS_A','/BUS_B',
         '/ESTOP','/DMAN','/DTR','/UART_TX','/UART_RX',
         '/+12V_IN','/+12V_PROT','/+5V','/POT_A0',
         '/ISP_MISO','/ISP_SCK','/ISP_MOSI','/RESET']

failures = []
for net in ORDER:
    pads = padinfo.get(net, [])
    if len(pads) < 2:
        continue
    t0 = time.time()
    hw = wof(net)/2
    connected = [pads[0]]
    remaining = pads[1:]
    netcells = set()   # cells already carrying this net
    for L in pads[0][2]:
        netcells.add((L, pads[0][3][0], pads[0][3][1]))
    while remaining:
        # nearest remaining pad to the connected set
        def d(p):
            return min((p[0]-q[0])**2 + (p[1]-q[1])**2 for q in connected)
        remaining.sort(key=d)
        tgt = remaining.pop(0)
        blk = g.blocked_for(net, CLEAR + hw)
        vb  = g.blocked_for(net, CLEAR + VIA_D/2)
        viaok = (~vb[F]) & (~vb[B]) & (~inpad)
        targets = np.zeros((2, g.ny, g.nx), bool)
        for (L, i, j) in netcells:
            targets[L, j, i] = True
        starts = [(L, tgt[3][0], tgt[3][1]) for L in tgt[2]]
        path = astar(g, blk, viaok, starts, targets)
        if path is None:
            failures.append((net, tgt[4])); connected.append(tgt); continue
        endL, endi, endj = path[-1]
        exact_end = None
        for q in connected:
            if q[3] == (endi, endj):
                exact_end = (q[0], q[1]); break
        netcells |= commit(net, path, blk=blk, exact_start=(tgt[0], tgt[1]), exact_end=exact_end)
        connected.append(tgt)
    print(f"  {net:14s} {len(pads):2d} pads  {time.time()-t0:5.1f}s")

# ---------- emit copper ----------
nets = {}
for i in range(board.GetNetCount()):
    ni = board.FindNet(i)
    if ni: nets[ni.GetNetname()] = ni
for (net, L, a, b, w) in tracks:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(LAYER[L]); t.SetNet(nets[net])
    board.Add(t)
for (net, x, y) in vias:
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(VIA_D)); v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets[net])
    board.Add(v)

# ---------- ground zones ----------
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(nets['/GND'])
    z.SetAssignedPriority(0)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetLocalClearance(pcbnew.FromMM(0.3))
    z.SetMinThickness(pcbnew.FromMM(0.2))
    z.SetThermalReliefGap(pcbnew.FromMM(0.25))
    z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
    o = z.Outline()
    o.NewOutline()
    for (px, py) in [(0.3,0.3),(BW-0.3,0.3),(BW-0.3,BH-0.3),(0.3,BH-0.3)]:
        o.Append(pcbnew.FromMM(px), pcbnew.FromMM(py))
    board.Add(z)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())

board.Save(OUT)
print(f"\ntracks {len(tracks)}  vias {len(vias)}")
if failures:
    print("UNROUTED:")
    for n, p in failures: print(f"   {n} -> {p}")
else:
    print("all nets routed")
