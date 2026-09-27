# -*- coding: utf-8 -*-
"""Emit the 1:1 measurement sheet as static SVG (1 user unit = 1 mm)."""
W, H = 180.0, 235.0
o = []
A = o.append

def line(x1,y1,x2,y2,w=0.2,cls="l"):
    A(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke-width="{w}" class="{cls}"/>')
def rect(x,y,w_,h_,sw=0.3,fill="none",cls="l"):
    A(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w_:.2f}" height="{h_:.2f}" fill="{fill}" stroke-width="{sw}" class="{cls}"/>')
def txt(x,y,s,size=2.6,anchor="start",cls="t",weight=None,mono=True):
    f = 'gm' if mono else 'gs'
    wt = f' font-weight="{weight}"' if weight else ''
    A(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" class="{cls} {f}"{wt}>{s}</text>')
def hole(cx,cy,r=0.5):
    A(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="none" stroke-width="0.2" class="l"/>')
    line(cx-1.4,cy,cx+1.4,cy,0.15); line(cx,cy-1.4,cx,cy+1.4,0.15)

# ---- sheet border ----
rect(3,3,W-6,H-6,0.5)
line(3,15,W-3,15,0.5)
txt(6,11.5,"PS1 BUCK MODULE &#8212; MEASUREMENT GAUGE",4.4,weight="700",mono=False)
txt(W-6,11.5,"PRINT AT 100%  &#183;  DO NOT SCALE",3.0,anchor="end")

def head(y,n,s):
    txt(6,y,n,3.0,weight="700")
    txt(6+len(n)*1.85+3,y,s,2.4,cls="t2")
    line(6,y+1.6,W-6,y+1.6,0.15)

# ---- 1. calibration bar ----
head(24,"1  CALIBRATION","this bar must measure exactly 100.0 mm")
BX,BY = 14,32
line(BX,BY,BX+100,BY,0.35)
for i in range(11):
    x = BX+i*10
    h_ = 4.0 if i in (0,10) else (3.0 if i==5 else 2.0)
    line(x,BY,x,BY-h_,0.25 if i in (0,5,10) else 0.15)
    if i%5==0: txt(x,BY-5.2,f"{i*10}",2.4,anchor="middle")
txt(BX+104,BY+0.9,"&#8592; 100.0 mm",2.6)
txt(BX,BY+5.5,"If it reads short, your printer scaled the page. Re-print with scaling set to 100% / Actual size.",2.3,cls="t2")

# ---- 2. ruler ----
head(48,"2  RULER","for direct centre-to-centre measurement")
RX,RY = 14,64
line(RX,RY,RX+150,RY,0.3)
for i in range(151):
    x=RX+i
    h_ = 4.0 if i%10==0 else (2.6 if i%5==0 else 1.4)
    line(x,RY,x,RY-h_,0.22 if i%10==0 else 0.12)
    if i%10==0: txt(x,RY-5.0,f"{i}",2.3,anchor="middle")
txt(RX,RY+4.2,"millimetres",2.3,cls="t2")

# ---- 3. coordinate grid ----
head(76,"3  HOLE-POSITION GRID","align the module to the corner, read each hole as (x, y)")
GX,GY,GW,GH = 16,86,70,50          # origin at bottom-left (GX, GY+GH)
for i in range(GW+1):
    x=GX+i
    hv = 0.34 if i%10==0 else (0.22 if i%5==0 else 0.1)
    line(x,GY,x,GY+GH,hv)
for j in range(GH+1):
    y=GY+GH-j
    hv = 0.34 if j%10==0 else (0.22 if j%5==0 else 0.1)
    line(GX,y,GX+GW,y,hv)
for i in range(0,GW+1,10): txt(GX+i,GY+GH+4.2,f"{i}",2.4,anchor="middle")
for j in range(0,GH+1,10): txt(GX-2.2,GY+GH-j+0.9,f"{j}",2.4,anchor="end")
line(GX,GY+GH,GX+13,GY+GH,0.7); line(GX,GY+GH,GX,GY+GH-13,0.7)
txt(GX+1.5,GY+GH-15,"0,0",2.6,weight="700")
txt(GX+GW+4,GY+4,"Lay the module",2.5,cls="t2")
txt(GX+GW+4,GY+7.5,"flat on the grid,",2.5,cls="t2")
txt(GX+GW+4,GY+11,"bottom-left corner",2.5,cls="t2")
txt(GX+GW+4,GY+14.5,"on 0,0. Read the",2.5,cls="t2")
txt(GX+GW+4,GY+18,"centre of each of",2.5,cls="t2")
txt(GX+GW+4,GY+21.5,"the four holes.",2.5,cls="t2")
txt(GX+GW+4,GY+27,"Heavy lines = 10 mm",2.3,cls="t2")
txt(GX+GW+4,GY+30.5,"Medium = 5 mm",2.3,cls="t2")
txt(GX+GW+4,GY+34,"Fine = 1 mm",2.3,cls="t2")

# ---- 4. module outlines ----
head(148,"4  WHICH MODULE?","lay yours on each outline to confirm the family")
rect(16,156,22,17,0.45); txt(27,166.5,"22 &#215; 17",3.0,anchor="middle",weight="700"); txt(27,170.5,"MP1584EN",2.3,anchor="middle")
rect(52,156,17,11,0.45); txt(60.5,162.2,"17 &#215; 11",2.8,anchor="middle",weight="700"); txt(60.5,165.8,"Mini-360",2.2,anchor="middle")
rect(82,156,43,21,0.45); txt(103.5,166.5,"43 &#215; 21",3.0,anchor="middle",weight="700"); txt(103.5,170.5,"LM2596",2.3,anchor="middle")
txt(16,181,"Outlines are the board edge, not the holes. A close-but-not-exact fit is normal &#8212; sellers vary by a millimetre or two.",2.3,cls="t2")

# ---- 5. what to send back ----
head(190,"5  SEND BACK","four coordinates and which pad is +")
for i,(lbl) in enumerate(["IN+","IN&#8722;","OUT+","OUT&#8722;"]):
    y = 198+i*7
    txt(16,y,lbl,2.8,weight="700")
    txt(30,y,"x =",2.6,cls="t2"); line(38,y+0.8,54,y+0.8,0.25)
    txt(58,y,"y =",2.6,cls="t2"); line(66,y+0.8,82,y+0.8,0.25)
    txt(86,y,"mm",2.4,cls="t2")

# ---- title block ----
TBX,TBY,TBW,TBH = 100,196,77,33
rect(TBX,TBY,TBW,TBH,0.5)
rows=[("PROJECT","Torqeedo 1103 CL besturing"),("BOARD","torqeedo_pcb  rev A"),
      ("PART","PS1  buck 12 V &#8594; 5 V"),("SCALE","1:1   SHEET 1/1")]
for i,(k,v) in enumerate(rows):
    y=TBY+(i+1)*(TBH/4)
    if i<3: line(TBX,y,TBX+TBW,y,0.2)
    txt(TBX+2.5,y-(TBH/4)+5.2,k,2.2,cls="t2")
    txt(TBX+24,y-(TBH/4)+5.4,v,2.7)
line(TBX+21,TBY,TBX+21,TBY+TBH,0.2)

STYLE = (
  '<style>'
  '.sheet-svg{background:#fff}'
  '.sheet-svg .l{stroke:#151515;fill:none}'
  '.sheet-svg .t{fill:#151515;stroke:none}'
  '.sheet-svg .t2{fill:#5a5a5a;stroke:none}'
  '.sheet-svg .gm{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace}'
  '.sheet-svg .gs{font-family:"Saira Condensed","Arial Narrow",Helvetica,sans-serif}'
  '</style>')
BG = f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff" stroke="none"/>'
SVG = (f'<svg class="sheet-svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" '
       f'xmlns="http://www.w3.org/2000/svg" role="img" '
       f'aria-label="One-to-one printable measurement gauge for the PS1 buck module">\n'
       + STYLE + "\n" + BG + "\n" + "\n".join(o) + "\n</svg>")
open(__import__('sys').argv[1],"w").write(SVG)
print(f"svg: {len(SVG)} bytes, {len(o)} elements")
