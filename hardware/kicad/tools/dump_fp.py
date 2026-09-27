import pcbnew, json, sys
LIB="/usr/share/kicad/footprints"
fps = json.load(open(sys.argv[1]))['comps']
seen={}
for ref,d in fps.items():
    lib,name=d['fp'].split(':')
    if name in seen: continue
    fp = pcbnew.FootprintLoad(f"{LIB}/{lib}.pretty", name)
    seen[name]=1
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    pads = sorted(fp.Pads(), key=lambda p: p.GetNumber())
    print(f"--- {name}  bbox {bb.GetWidth()/1e6:.2f} x {bb.GetHeight()/1e6:.2f} mm")
    for p in pads:
        pos=p.GetPosition(); sz=p.GetSize()
        print(f"    pad {p.GetNumber():>3s} at ({pos.x/1e6:+7.3f},{pos.y/1e6:+7.3f}) size {sz.x/1e6:.2f}x{sz.y/1e6:.2f}")
