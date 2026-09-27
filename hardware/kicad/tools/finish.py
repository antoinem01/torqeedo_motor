import pcbnew, sys
IN, OUT = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(IN)
def mm(v): return pcbnew.FromMM(v)
def VP(x,y): return pcbnew.VECTOR2I(mm(x), mm(y))
fps = {f.GetReference(): f for f in b.GetFootprints()}

# ---- reference designators that landed on pads / on each other ----
REPOS = {
    'Y1':      (22.0, 44.6,  0),
    'J_RS485': (10.0, 22.5,  0),
    'R6':      (48.0, 27.3,  0),
    'L1':      (48.0, 40.6,  0),
    'C10':     (48.0, 48.4,  0),
    'R4':      (33.0, 50.7,  0),
    'C3':      (22.0, 31.5,  0),
    'TVS1':    (13.0, 26.0,  0),
    'R1':      (13.5, 37.7,  0),
    'R2':      (13.5, 42.7,  0),
}
for ref, (x, y, rot) in REPOS.items():
    t = fps[ref].Reference()
    t.SetPosition(VP(x, y))
    t.SetTextAngleDegrees(rot)

# ---- functional silkscreen ----
def text(s, x, y, size=0.9, rot=0, just='C', layer=pcbnew.F_SilkS, bold=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s); t.SetPosition(VP(x, y)); t.SetLayer(layer)
    t.SetTextSize(VP(size, size)); t.SetTextThickness(mm(size*0.16))
    t.SetBold(bold)
    t.SetTextAngleDegrees(rot)
    t.SetHorizJustify({'L': pcbnew.GR_TEXT_H_ALIGN_LEFT,
                       'C': pcbnew.GR_TEXT_H_ALIGN_CENTER,
                       'R': pcbnew.GR_TEXT_H_ALIGN_RIGHT}[just])
    b.Add(t)

LABELS = [
    # power in
    ("+12V", 78.00, 4.6), ("GND", 72.92, 4.6),
    # RS485 bus out
    ("A",   12.0, 27.00, 'L'), ("B", 12.0, 34.30, 'L'), ("GND", 12.0, 39.50, 'L'),
    # potmeter
    ("GND", 52.5, 66.00, 'L'), ("POT", 52.5, 68.54, 'L'), ("+5V", 52.5, 71.08, 'L'),
    # e-stop / dead man
    ("E-STOP", 10.6, 52.00, 'L'), ("GND", 10.6, 54.54, 'L'),
    ("DODE MAN", 10.6, 60.00, 'L'), ("GND", 10.6, 62.54, 'L'),
    # buck module pins
    ("IN+",  86.3, 30.00, 'R'), ("IN-",  86.3, 32.54, 'R'),
    ("+5V",  86.3, 35.08, 'R'), ("GND",  86.3, 37.62, 'R'),
    # jumpers
    ("TERM", 22.0, 35.30), ("BIASA", 22.0, 42.30), ("BIASB", 22.0, 49.30),
]
for item in LABELS:
    if len(item) == 4: s, x, y, j = item
    else:              s, x, y = item; j = 'C'
    text(s, x, y, 0.9, 0, j)

# FTDI pin legend
for s, x in zip(["DTR","TX","RX","5V","G","G"], [24.0, 26.54, 29.08, 31.62, 34.16, 36.70]):
    text(s, x, 9.6, 0.8)

# ---- reserved area for the buck module (it overhangs its 1x4 header) ----
for (x0,y0,x1,y1) in [(78,26,98,26),(98,26,98,42),(98,42,78,42),(78,42,78,26)]:
    g = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
    g.SetStart(VP(x0,y0)); g.SetEnd(VP(x1,y1))
    g.SetLayer(pcbnew.F_SilkS); g.SetWidth(mm(0.12))
    b.Add(g)
text("BUCK 12V -> 5V", 88.0, 23.4, 0.9)
text("ruimte vrijhouden", 88.0, 25.0, 0.8)

# ---- board identification + safety note ----
text("TORQEEDO 1103 CL  -  BESTURING", 50.0, 74.2, 1.6, bold=True)
text("rev A  -  logica + RS485", 50.0, 76.3, 1.0)
text("GEEN 29,6V MOTORPAD OP DEZE PRINT", 50.0, 78.0, 1.0)
tb = pcbnew.PCB_TEXT(b)
tb.SetText("TORQEEDO BESTURING rev A"); tb.SetPosition(VP(55.0, 60.0))
tb.SetLayer(pcbnew.B_SilkS); tb.SetTextSize(VP(1.6, 1.6)); tb.SetTextThickness(mm(0.25))
tb.SetMirrored(True); tb.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
b.Add(tb)

b.Save(OUT)
print("finished ->", OUT)
