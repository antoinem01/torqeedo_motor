import pcbnew, sys, math
from collections import defaultdict
b = pcbnew.LoadBoard(sys.argv[1])
L = {pcbnew.F_Cu:'F.Cu', pcbnew.B_Cu:'B.Cu'}

length = defaultdict(float); vias = defaultdict(int); segs = defaultdict(int)
blen = defaultdict(float)
tr_by_net = defaultdict(list)
for t in b.GetTracks():
    n = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        vias[n] += 1; continue
    s, e = t.GetStart(), t.GetEnd()
    d = math.hypot(e.x-s.x, e.y-s.y)/1e6
    length[n] += d; segs[n] += 1
    if t.GetLayer() == pcbnew.B_Cu: blen[n] += d
    tr_by_net[n].append((s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6))

print(f"{'net':14s} {'mm':>7s} {'segs':>5s} {'vias':>5s} {'on B.Cu mm':>11s}")
tot = 0
for n in sorted(length, key=lambda k: -length[k]):
    print(f"{n:14s} {length[n]:7.1f} {segs[n]:5d} {vias[n]:5d} {blen[n]:11.1f}")
    tot += length[n]
print(f"{'TOTAL':14s} {tot:7.1f} {sum(segs.values()):5d} {sum(vias.values()):5d}")

print("\n--- ground zones ---")
for z in b.Zones():
    ly = z.GetLayer()
    poly = z.GetFilledPolysList(ly)
    area = poly.Area()/1e12
    print(f"  {L.get(ly,ly):5s} net={z.GetNetname():5s} filled {area:6.1f} mm^2 "
          f"({100*area/(100*80):4.1f}% of board), {poly.OutlineCount()} island(s)")

# analog isolation: distance from POT_A0 copper to the switching side
def segdist(a, p):
    x0,y0,x1,y1 = a; px,py = p
    dx,dy = x1-x0, y1-y0; l2 = dx*dx+dy*dy
    t = 0 if l2==0 else max(0, min(1, ((px-x0)*dx + (py-y0)*dy)/l2))
    return math.hypot(px-(x0+t*dx), py-(y0+t*dy))
def netmin(n1, n2):
    best = 1e9
    for a in tr_by_net[n1]:
        for c in tr_by_net[n2]:
            for p in [(c[0],c[1]),(c[2],c[3])]:
                best = min(best, segdist(a, p))
            for p in [(a[0],a[1]),(a[2],a[3])]:
                best = min(best, segdist(c, p))
    return best
print("\n--- analog / switching separation ---")
for other in ['/+12V_IN','/+12V_PROT','/+5V']:
    print(f"  POT_A0 to {other:12s}: {netmin('/POT_A0', other):5.2f} mm")
ps1 = [fp for fp in b.GetFootprints() if fp.GetReference()=='PS1'][0]
p = ps1.GetPosition(); px,py = p.x/1e6, p.y/1e6
d = min(segdist(a,(px,py)) for a in tr_by_net['/POT_A0'])
print(f"  POT_A0 to PS1 (buck)     : {d:5.2f} mm")
print(f"\n--- crystal ---")
for n in ['/XTAL1','/XTAL2']:
    print(f"  {n}: {length[n]:.1f} mm, {vias[n]} vias")
