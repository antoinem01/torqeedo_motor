import pcbnew, json, sys
LIB = "/usr/share/kicad/footprints"
S = sys.argv[1]
OUT = sys.argv[2]
d = json.load(open(f"{S}/net.json"))
comps, nets = d['comps'], d['nets']

BW, BH = 100.0, 80.0          # board size mm
HOLES = [(5,5),(95,5),(5,75),(95,75)]

def mm(v): return pcbnew.FromMM(v)
def VP(x,y): return pcbnew.VECTOR2I(mm(x), mm(y))

# ref -> (origin_x, origin_y, rotation_deg)
PLACE = {
  # ---- MCU ----
  'U2':      (36.00, 22.00,   0),
  # ---- power block, top right ----
  'J_PWR':   (78.00, 10.00, 180),
  'D1':      (78.00, 18.00,   0),
  'C1':      (64.00, 22.00,   0),
  'PS1':     (88.00, 30.00,   0),
  'C2':      (73.00, 33.00,   0),
  # ---- reset + FTDI, top left ----
  'J_FTDI':  (24.00,  7.00,  90),
  'SW1':     (10.00, 14.00,   0),
  'R8':      (30.00, 21.00,   0),
  'C13':     (22.00, 11.00, 180),
  # ---- RS485 transceiver + bus chain, left ----
  'U1':      (28.00, 31.00, 180),
  'C3':      (22.00, 33.00, 180),
  'J_RS485': ( 7.00, 28.00, 270),
  'TVS1':    (13.00, 30.50,   0),
  'R1':      (13.50, 36.00,   0),
  'JP_TERM': (18.00, 34.00,   0),
  'R2':      (13.50, 41.00,   0),
  'JP_BA':   (18.00, 41.00,   0),
  'R3':      (13.50, 47.50, 180),
  'JP_BB':   (18.00, 48.00,   0),
  # ---- MCU decoupling + crystal ----
  'C9':      (32.80, 37.00, 180),
  'C12':     (28.00, 37.00, 180),
  'Y1':      (31.50, 42.15, 270),
  'C7':      (26.00, 42.15, 180),
  'C8':      (26.00, 47.03, 180),
  # ---- e-stop / dead man ----
  'R4':      (33.00, 52.00,   0),
  'R5':      (33.00, 55.00,   0),
  'C5':      (28.00, 52.00, 180),
  'C6':      (28.00, 55.00, 180),
  'J_ESTOP': ( 8.00, 52.00,   0),
  'J_DMAN':  ( 8.00, 60.00,   0),
  # ---- analog + AVCC + ISP, right ----
  'R6':      (48.00, 29.00, 180),
  'C4':      (48.00, 32.00,   0),
  'R7':      (48.00, 35.00,   0),
  'C11':     (48.00, 39.00,   0),
  'L1':      (48.00, 43.00, 180),
  'C10':     (48.00, 46.50,   0),
  'J_ISP':   (53.00, 44.00,   0),
  'J_POT':   (50.00, 66.00,   0),
}

board = pcbnew.BOARD()
board.SetCopperLayerCount(2)


# ---- footprints ----
placed = {}
for ref, (x, y, rot) in PLACE.items():
    lib, name = comps[ref]['fp'].split(':')
    fp = pcbnew.FootprintLoad(f"{LIB}/{lib}.pretty", name)
    if fp is None:
        sys.exit(f"could not load {comps[ref]['fp']} for {ref}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(ref)
    fp.SetValue(comps[ref]['value'])
    fp.SetPosition(VP(x, y))
    if rot: fp.SetOrientationDegrees(rot)
    fp.SetPath(pcbnew.KIID_PATH(f"/{comps[ref]['uuid']}"))
    r = fp.Reference()
    r.SetTextSize(VP(0.8, 0.8)); r.SetTextThickness(mm(0.12))
    fp.Value().SetVisible(False)
    board.Add(fp)
    placed[ref] = fp

# ---- nets ----
nm = board.GetNetInfo()
for netname, nodes in nets.items():
    if netname.startswith('unconnected-'):
        continue
    ni = pcbnew.NETINFO_ITEM(board, netname)
    board.Add(ni)
    for ref, pin in nodes:
        pad = placed[ref].FindPadByNumber(pin)
        if pad is None:
            print(f"  !! {ref} pad {pin} not found")
            continue
        pad.SetNet(ni)

# ---- board outline ----
pts = [(0,0),(BW,0),(BW,BH),(0,BH)]
for i in range(4):
    seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(VP(*pts[i])); seg.SetEnd(VP(*pts[(i+1)%4]))
    seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1))
    board.Add(seg)

# ---- M3 mounting holes ----
for i,(hx,hy) in enumerate(HOLES):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(f"H{i+1}")
    fp.Reference().SetVisible(False)
    fp.SetPosition(VP(hx,hy))
    pad = pcbnew.PAD(fp)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(VP(3.2,3.2)); pad.SetDrillSize(VP(3.2,3.2))
    pad.SetLayerSet(pad.UnplatedHoleMask())
    pad.SetNumber("")
    fp.Add(pad)
    board.Add(fp)

board.Save(OUT)
print(f"saved {OUT}: {len(placed)} footprints, {board.GetNetCount()-1} nets")

# ---- verification dump: real pad coordinates ----
rows=[]
for ref, fp in sorted(placed.items()):
    for p in fp.Pads():
        pos = p.GetPosition()
        rows.append((ref, p.GetNumber(), pos.x/1e6, pos.y/1e6, p.GetNetname()))
json.dump(rows, open(f"{S}/pads.json","w"), indent=0)
print("--- connector / rotated part check ---")
for ref in ['J_PWR','J_RS485','J_FTDI','U1','J_ISP','J_POT','PS1','D1']:
    ps = [(p.GetNumber(), round(p.GetPosition().x/1e6,2), round(p.GetPosition().y/1e6,2), p.GetNetname())
          for p in sorted(placed[ref].Pads(), key=lambda q:q.GetNumber())]
    print(f"{ref:9s}", ps)
