#!/usr/bin/env bash
# Rebuild torqeedo_pcb.kicad_pcb from the schematic: place -> route -> finish -> verify.
#
#   ./tools/regenerate.sh            # build into a temp dir, verify, do NOT install
#   ./tools/regenerate.sh --install  # also copy the result over torqeedo_pcb.kicad_pcb
#
# WARNING: --install OVERWRITES the board file. Anything you changed by hand in
# the KiCad GUI is lost. The scripts are the source of truth only until someone
# opens pcbnew and drags something; after that, edit the board, not the scripts.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="PYTHONPATH=/usr/lib/python3/dist-packages python3"     # pcbnew lives in dist-packages
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT   # kept only on success; failures copy out what matters
echo "==> workdir $W"

echo "==> netlist from schematic"
kicad-cli sch export netlist --format kicadsexpr -o "$W/netlist.net" torqeedo_pcb.kicad_sch
eval $PY tools/parse_net.py "$W/netlist.net" "$W/net.json" > "$W/netlist.txt"
echo "    $(grep -c . "$W/netlist.txt") lines; net.json written"

echo "==> place"   ; eval $PY tools/place.py  "$W" "$W/board.kicad_pcb"  | grep -E "saved|!!"
echo "==> route"
eval $PY tools/route.py "$W" "$W/board.kicad_pcb" "$W/routed.kicad_pcb" | tee "$W/route.log" \
  | grep -E "tracks|all nets|UNROUTED|GND stitch|->"
if grep -q "UNROUTED" "$W/route.log"; then
  echo
  echo "!! The router did not finish every net. See the list above."
  echo "!! Results vary between runs (see tools/README.md); just run this again."
  exit 1
fi
echo "==> finish"  ; eval $PY tools/finish.py "$W/routed.kicad_pcb" "$W/final.kicad_pcb" | grep -E "finished"

echo "==> DRC"
kicad-cli pcb drc --severity-error --severity-warning -o "$W/drc.rpt" "$W/final.kicad_pcb" \
  | grep -iE "overtreding|violation|onverbonden|unconnected"
if ! grep -qE "^\*\* Found 0 DRC violations" "$W/drc.rpt" \
  || ! grep -qE "^\*\* Found 0 unconnected pads" "$W/drc.rpt"; then
  echo "!! DRC is not clean - refusing to go further. Report: $W/drc.rpt"
  cp "$W/drc.rpt" ./regenerate-drc.rpt; echo "!! copied to ./regenerate-drc.rpt"
  exit 1
fi

echo "==> netlist board vs schematic"
eval $PY - "$W" <<'PYEOF'
import pcbnew, json, sys
W = sys.argv[1]
d = json.load(open(f"{W}/net.json"))
sch = {(r, p): n for n, nodes in d['nets'].items()
       if not n.startswith('unconnected-') for r, p in nodes}
b = pcbnew.LoadBoard(f"{W}/final.kicad_pcb")
pcb, fps = {}, {}
for fp in b.GetFootprints():
    r = fp.GetReference()
    if r.startswith('H') and len(r) == 2 and r[1].isdigit():
        continue
    fps[r] = fp.GetFPIDAsString()
    for p in fp.Pads():
        if p.GetNetname():
            pcb[(r, p.GetNumber())] = p.GetNetname()
bad = sum(1 for r in d['comps'] if fps.get(r) != d['comps'][r]['fp'])
print(f"    connections match: {sch == pcb} ({len(sch)})   footprint mismatches: {bad}")
assert sch == pcb and bad == 0, "board does not match the schematic"
PYEOF

if [ "${1:-}" = "--install" ]; then
  cp "$W/final.kicad_pcb" torqeedo_pcb.kicad_pcb
  echo "==> installed over torqeedo_pcb.kicad_pcb"
else
  echo "==> not installed (pass --install to overwrite the board)"
fi
