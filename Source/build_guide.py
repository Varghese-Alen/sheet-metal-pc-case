#!/usr/bin/env python3
"""Generate client guide from sibling kit data; never writes CAD or geometry.
Run with Python3 and PyMuPDF installed: python3 Source/build_guide.py
SPDX-License-Identifier: CERN-OHL-P-2.0
Optional: PC_CASE_GUIDE_FONT=/path/to/DejaVuSans.ttf; PC_CASE_GUIDE_PROOFS=/path/to/proofs
PDF vector paths are evaluated from analytic LINE/ARC/CIRCLE entities; circular
arcs use PDF cubic Beziers (<=22.5 degree spans), not sampled polylines.
"""
import sys, json, csv, math, re, argparse, os
from pathlib import Path
sys.path.insert(0,'/work/tools/pdf')
try:
 import pymupdf as f
except ImportError:
 import fitz as f
K=Path(__file__).resolve().parent.parent
OUT=K/'Sheet Metal PC Case Drawings and Build Guide.pdf'
PROOF=Path(os.environ.get('PC_CASE_GUIDE_PROOFS',str(K/'Preview'/'drawing-proofs')))
def load(n): return json.loads((K/(n+'.json')).read_text())
def csvload(n): return list(csv.DictReader((K/(n+'.csv')).open()))
P=load('panels'); D=load('drawing-geometry'); SUP=load('supplemental-blanks'); J=load('joint-schedule'); C=load('component-clearances'); EV=load('io-export-validation'); DV=load('dxf-validation'); DEV=load('development-check'); FH=load('folded-hole-alignment'); REFS=load('references')
IO=load('io-interfaces'); IC=load('io-clearance-check'); IS=load('io-source-validation')
NOTES=(K/'ASSEMBLY-NOTES.md').read_text(); BENDS=csvload('bend-schedule'); BOM=csvload('sheet-parts-bom'); HW=csvload('hardware-bom'); BUY=csvload('purchased-components')
FONT=Path('/nix/store/1nnsca2xfhhz8xkadcpy4hv2kwffs0zy-dejavu-fonts-minimal-2.37/share/fonts/truetype/DejaVuSans.ttf')
FONT=Path(os.environ.get('PC_CASE_GUIDE_FONT',str(FONT)))
if not FONT.exists(): FONT=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
font=f.Font(fontfile=str(FONT)) if FONT.exists() else f.Font('helv')
doc=f.open(); W,H=1190.551,841.89
ink=(.12,.16,.19); muted=(.35,.40,.43); teal=(.0,.40,.43); sand=(.78,.65,.45); pale=(.94,.95,.94); orange=(.67,.24,.08)
checks=[]; marks={}
def clean(t):
 t=str(t).replace('..','…')
 # Legacy sources sometimes omit spacing; only automatic BOM display cleanup.
 t=re.sub(r'(?<=[a-z])(?=[0-9])',' ',t)
 t=re.sub(r'(?<=[0-9])(?=[a-z])',' ',t)
 return t

def txt(p,x,y,t,size=11,color=ink):
 p.insert_text((x,y),str(t).replace(' • ', '. '),fontname='DV',fontsize=size,color=color)

def box(p,x,y,w,h,t,size=11,color=ink):
 r=f.Rect(x,y,x+w,y+h)
 rem=p.insert_textbox(r,str(t).replace(' • ', '. '),fontname='DV',fontsize=size,lineheight=1.3,color=color)
 checks.append({'page':p.number+1,'rect':list(r),'remaining':rem,'text':str(t)[:90]})
 if rem < -0.01: raise RuntimeError(f'Text overflow page {p.number+1}: {t[:90]} ({rem})')
 return y+h

def page(title,sub='',tag=None):
 p=doc.new_page(width=W,height=H); p.insert_font(fontname='DV',fontbuffer=font.buffer)
 p.draw_rect(f.Rect(0,0,W,10),color=None,fill=teal)
 txt(p,38,46,'Sheet Metal PC Case engineering build guide',10,teal)
 txt(p,38,83,title,25)
 if sub: box(p,39,98,1110,35,sub,10,muted)
 p.draw_line((38,790),(1152,790),color=sand,width=.8)
 txt(p,38,813,'Unprototyped design. Check fabrication and fit before cutting. Dimensions in mm. CERN-OHL-P-2.0.',9,muted)
 txt(p,1085,813,f'{p.number+1:02d}',10,teal)
 if tag: marks[tag]=p.number
 return p

def head(p,x,y,t): txt(p,x,y,t,14,teal)
def para(p,x,y,w,title,t,h=105):
 head(p,x,y,title); box(p,x,y+12,w,h,t,11)

def table(p,x,y,widths,headers,rows,size=10,minrow=25):
 total=sum(widths); yy=y
 for ri,row in enumerate([headers]+rows):
  lines=[]
  for val,ww in zip(row,widths):
   words=str(val).split(); ll=['']
   for word in words:
    test=(ll[-1]+' '+word).strip()
    if font.text_length(test,fontsize=size)>ww-16 and ll[-1]: ll.append(word)
    else: ll[-1]=test
   lines.append(ll)
  rh=max(minrow,max(map(len,lines))*size*1.3+12)
  p.draw_rect(f.Rect(x,yy,x+total,yy+rh),color=None,fill=teal if ri==0 else (pale if ri%2 else (1,1,1)))
  xx=x
  for ll,ww in zip(lines,widths):
   box(p,xx+8,yy+5,ww-16,rh-6,'\n'.join(ll),size,(1,1,1) if ri==0 else ink); xx+=ww
  yy+=rh
 if yy>777: raise RuntimeError(f'table overrun page {p.number+1}: {yy}')
 return yy

def image(p,name,rect): p.insert_image(f.Rect(*rect),filename=str(K/'Preview'/name),keep_proportion=True)
def fmt(n): return f'{n:.4f}'.rstrip('0').rstrip('.')

def vector(p,id,rect,bends=None,rot=False,dimensions=True):
 g=D[id]; x,y,w,h=rect; gw,gh=g['width'],g['height']; dw,dh=(gh,gw) if rot else (gw,gh)
 s=min((w-95)/dw,(h-90)/dh,5.5); ox=x+45+(w-95-dw*s)/2; oy=y+45+(h-90-dh*s)/2+dh*s
 def q(a):
  u,v=a
  if rot: u,v=v,gw-u
  return f.Point(ox+u*s,oy-v*s)
 sh=p.new_shape()
 def arc(c,r,a,b):
  sweep=(b-a)%360
  if abs(sweep)<1e-10: sweep=360
  n=math.ceil(sweep/22.5)
  for i in range(n):
   aa=math.radians(a+sweep*i/n); bb=math.radians(a+sweep*(i+1)/n); k=4/3*math.tan((bb-aa)/4)
   v1=(c[0]+r*math.cos(aa),c[1]+r*math.sin(aa)); v4=(c[0]+r*math.cos(bb),c[1]+r*math.sin(bb))
   v2=(v1[0]-k*r*math.sin(aa),v1[1]+k*r*math.cos(aa)); v3=(v4[0]+k*r*math.sin(bb),v4[1]-k*r*math.cos(bb))
   sh.draw_bezier(q(v1),q(v2),q(v3),q(v4))
 for e in g['entities']:
  if e['type']=='LINE': sh.draw_line(q(e['p']),q(e['q']))
  else: arc(e['c'],e['r'],e.get('a',0),e.get('b',360))
 sh.finish(color=ink,width=.55,closePath=False); sh.commit()
 if bends:
  for i,b in enumerate(bends):
   for a,z in b['flat_bend_lines_DXF_mm']:
    p.draw_line(q(a),q(z),color=teal,width=.8,dashes='[4 3] 0')
   # No crowding labels on wrap: numbered on dedicated forming table.
   if id!='W01':
    a,z=b['flat_bend_lines_DXF_mm'][0]; pt=q(z); txt(p,pt.x+5,pt.y-4,f'B{i+1}',9,teal)
 if dimensions:
  # Displayed extents are actual blank dimensions, independent of rotation.
  p.draw_line((ox,oy+11),(ox+dw*s,oy+11),color=muted,width=.6)
  for xx in [ox,ox+dw*s]: p.draw_line((xx,oy+6),(xx,oy+16),color=muted,width=.6)
  txt(p,ox+dw*s/2-35,oy+26,fmt(dw)+' mm',10)
  p.draw_line((ox-18,oy),(ox-18,oy-dh*s),color=muted,width=.6)
  txt(p,ox,oy-dh*s-17,('DXF width ' if rot else 'DXF height ')+fmt(dh)+' mm',10)
  o=q((0,0)); p.draw_circle(o,2,color=teal,width=.7)
  # local axes at separate keyed origin to avoid detail collisions
  txt(p,x+4,y+h-6,('ROTATED: +DXF X ↓, +DXF Y →' if rot else '+DXF X →, +DXF Y ↑')+'  |  O = lower-left DXF (0,0)',9,teal)
 return q,s

def bendrows(panel):
 out=[]
 for i,b in enumerate(panel['bends']):
  lines='; '.join(f'({fmt(a[0])}, {fmt(a[1])}) → ({fmt(z[0])}, {fmt(z[1])})' for a,z in b['flat_bend_lines_DXF_mm'])
  out.append([f'B{i+1} / {b["suggested_forming_step"]}',fmt(b['angle_deg'])+'°',f'{fmt(b["inside_radius_mm"])} / {b["K"]} / {fmt(b["BA_mm"])}',lines])
 return out

# 01 cover
p=page('Sheet Metal PC Case','Approved appearance • Current engineering kit • Prototype documentation, not a tested product',tag='cover')
image(p,'front.png',(635,135,1150,755))
para(p,40,162,565,'A physical prototype still needs testing','The files have been checked in CAD. A physical build still needs tests to confirm fabrication, component fit and electrical safety. This is not a certified product.',74)
p.draw_rect(f.Rect(38,265,604,418),color=None,fill=pale)
head(p,52,290,'Front connections and power button')
box(p,52,304,535,100,'The I01 fascia and concealed I03 plate support two USB-C ports, two USB-A ports, stereo audio and a power button. Clearances use supplier dimensions and conservative allowances. The actual hardware still needs fit and electrical tests.',12)
table(p,40,445,[270,290],['Key envelope','Current nominal dimensions'],[['Main shell / sled','302 W × 410 D × 520 H'],['With ordinary heads / PCI rail','306.8 W × 422 D × 520 H'],['Upper outside width','290'],['Main sheet set','19 instances / 18 IDs; 3 optional'],['Ancillary / test cut set','10 shims + 1 gasket; 29 DXFs total']],11)
box(p,40,675,565,94,'The 2.4 mm screw heads add 2.2 mm to the earlier width estimate without moving the sides or changing the case outline. The handles are not load rated. Use them for an empty case only until tested. Check the power switch and all purchased hardware for fit.',11)
# Purchased components and current assembly orientation
p=page('Purchased components & assembly orientation','Current model views show the approved architecture; component envelopes are not detailed OEM replicas.')
pr=[['PV0F24011 + supplied nut / O-ring','1','Insulated PWR_SW pair'],['Newnex U4S5C01C08-010 / 1 m','2','Panel-C female → C male'],['Delock 67234','2','One Type-E host per C'],['Newnex USR2-AA-1M / 1 m','2','Panel-A female → A male'],['Delock 82941 / 45 cm','1','19-pin → two A females'],['FRONTX P0902_036 / 914.4 mm','1','Rear stereo pass-through'],['140 × 140 × 25 fans, 124.5 pitch','2','Bottom and rear targets'],['120 × 120 × 25 fan, 105 pitch','1','Optional F01 module'],['Real full-height PCI blank covers','7 less occupied','Gauge tips and notches'],['Releasable 2.5 mm ties / broad straps','8 / 6','Cushion + abrasion sleeves'],['Bonding lug / contact hardware','1 set','Electrical qualification'],['1 mm fascia back pads, 2 × 12','4','Captive; no structural glue'],['2 mm GPU pad, 12 × 20 nominal','1','Optional contact gate']]
table(p,40,145,[280,100,220],['Purchased item','Quantity','Status / gate'],pr,10,30)
box(p,40,680,595,85,'Fasteners, shims, gasket, bosses and standoffs are on the hardware / cut BOM pages. The current carrier uses ordinary M3×10 through-bolts; no welding is needed. The full I/O BOM is the default; mutually exclusive variants change quantities as tabulated later.',11)
image(p,'internal.png',(690,140,1145,434))
image(p,'exploded.png',(690,457,1145,752))
txt(p,690,451,'INTERNAL / EXPLODED: CURRENT MODEL',9,teal)
# 02 compatibility
p=page('Compatibility targets: not qualified combinations','Retail examples below illustrate individual dimensions only; they are not approved bills of computer components.')
table(p,40,145,[180,310,335,285],['System','Target / reserve','Retail dimensional example','Selection gate'],[
['Motherboard','ATX 304.8 × 243.84; microATX; Mini-ITX','Select the actual board drawing and mounting subset.','Socket, RAM, VRM, rear shield and header locations.'],
['GPU','340 length × 150 projection × 65 thick; 35 connector reserve','NVIDIA RTX 4080 Founders Edition: 304 × 137 × 61 mm (maker dimensions).','Real bracket gauge, plug bend radius and support contact.'],
['CPU cooler','170 height target from board component envelope','Noctua NH-D15 165 mm height with fans (maker nominal).','RAM clearance may raise fans; check socket position.'],
['PSU','ATX, 140–180 depth + 60 front cable reserve','Corsair RM750e (2023): 150 × 86 × 140 mm.','Exact revision, rear hole hand and allowed screw penetration.'],
['Fans','Two 140 × 140 × 25; optional 120 × 120 × 25','Noctua NF-A14 PWM: 140 × 140 × 25, 124.5 pitch.','Actual hole passage, head size and finished stack.'],
['SSD','One 7 mm-class 2.5-inch; 69.85 × 100 body envelope','Samsung 870 EVO: 100 × 69.85 × 6.8 mm.','Bottom boss pattern, screw limit, plug size and seating.']],11)
para(p,40,620,530,'Electrical resources are not interchangeable','Two Type-C ports require TWO independent Type-E / Key-A headers or a qualified add-in controller. No passive Y splitter. No Thunderbolt, USB4 or Power Delivery claim.',100)
para(p,620,620,530,'Check before ordering','Use exact product revision drawings and samples. Retail dimensions above do not establish combined fit, cooling, cable routing or a modern GPU bracket interface. See references and the physical qualification checklist.',100)
# 03 cut BOM
p=page('Cut-part bill of materials','Cut-only DXFs in millimetres. Optional parts are included in the 18 IDs / 19 instances, not added to that count.')
rows=[]
for b in BOM:
 id=b['ID']; rows.append([id,b['quantity'],b['material'],b['thickness_mm'],f'{float(b["flat_width_mm"]):.4f} × {float(b["flat_height_mm"]):.4f}', 'Optional' if id in ['F01','G01','G02'] else 'Main'])
y=table(p,40,142,[125,55,260,85,330,255],['ID','Qty','Material','t (mm)','Blank bounding size (mm)','Set'],rows,10,24)
box(p,40,y+18,1100,100,'Ancillary: SH01, quantity 10, conductive shim stock, nominal 0.2 mm (Ø8 / Ø3.4). GSK01, quantity 1, closed-cell elastomer, nominal 0.5 mm. Choose one fascia: main full I01 or C1, power-only, fully blank alternatives. Total 29 DXFs = 18 main + 3 alternatives + 6 process coupons + 2 ancillary. Materials and quantities: supplemental-blanks.json. Finish: sand sleds / charcoal wrap; mask required contacts.',11)
# 04 / 05 hardware exact descriptions with separate qualification notes
for chunk in range(math.ceil(len(HW)/32)):
 p=page(f'Hardware bill of materials: {chunk+1} / {math.ceil(len(HW)/32)}','Quantities shown or required, including optional assemblies. Full per-item qualification remains in hardware-bom.csv.')
 entries=HW[chunk*32:(chunk+1)*32]
 # Two balanced columns, up to 16 entries each.
 for col in range(2):
  block=entries[col*16:(col+1)*16]
  table(p,40+col*570,145,[460,80],['Hardware description','Qty'],[[clean(b['description']),b['quantity_shown_or_required']] for b in block],10,25)
 box(p,40,728,1100,45,'Nominal fastener envelopes, not OEM models. Verify head height, usable thread and actual stack. PCB screw / locknut positions A,C,F,G,H,J,K,L,M are the depicted ATX subset; do not install unused standoffs.',10)
# 06 / 07 joints edited for readable precise text
jointrows=[
['Sides → wrap','10 M3×8; 10 RRE03-1; 10 shims','1.5 side + 0.7 head/shim gap + 1 flange; 4.8 useful engagement','Outside ±X. Qualify insert upset and finished shim stack.'],
['Rear → wrap via C clips','8 M3×8 / washers / nuts','Two 1 mm sheets + 0.5 washer + 2.4 nut; 3.1 tip','Roof, floor, rear and open sides.'],
['Tray flanges → wrap','4 M3×8 / washers / nuts','Two 1 mm sheets + 0.5 washer + 2.4 nut','External driver, left-side spanner. Nuts not captive.'],
['Tray → rear via T clips','4 M3×8 / washers / nuts','Two 1 mm sheets per joint + 0.5 washer + 2.4 nut','Rear / component side; cable-side nut.'],
['PCI rail → rear','2 M3×10; 2 mm spacers; washers / nuts','1 + 2 + 1 + 0.5 + 2.4 = 6.9; 3.1 tip','Rear access.'],
['M03 strip → M02','2 M3×5','1 rail + 3 tapped strip; 3 engagement / 1 tip','+X outside rail. Nine holes tapped M3×0.5.'],
['PCI covers / card → rail','7 M3×6; Ø7 washers','1 nominal cover + 0.5 washer + 1 rail + 3 strip = 5.5; 0.5 tip','+X rail. Real notch / locating-tip gauge first.'],
['Fascia capture','0.5 gasket; four 1 mm pads','Face Y−197.5…−196.5; pads to carrier Y−195.5','Remove carrier from right interior; no structural adhesive.'],
['I02 → wrap','2 ordinary M3×10; 2.5 spacers; washers / nuts','1 + 2.5 + 1 + 0.5 + 2.4 = 7.4; 2.6 tip','Front driver / right-side nut. NO WELDING.'],
['F01 → roof (optional)','2 M3×8 / washers / nuts','1 roof + 1 bracket + 0.5 washer + 2.4 nut','Roof driver / side spanner. Remove as module.'],
['120 fan → F01 (optional)','4 M4×35 / 0.8 washers / 3.2 nuts','25 + 1 + 0.8 + 3.2 = 30; 5 tip','Bench assembly. 3 mm head leaves 0.5 to side.'],
['G01 → floor (optional)','2 M4×10 / washers / nuts','1 floor + 3 foot + 0.8 + 3.2 = 8; 2 tip','Floor driver / open right side; shared 54 mm slot.'],
['G02 → G01 (optional)','2 M4×12 / washers / nuts','3 ledge + 3 post + 0.8 + 3.2 = 10; 2 tip','Open right side; 2 mm nonconductive contact pad.'],
['PSU supports → floor','4 M3×6; Ø8 × 8 blind-M3 bosses','1 floor + 5 thread; 6 bore depth / 2 top wall','Underside. Supports top Z34; never drill PSU.'],
['PSU → rear','4 #6-32 UNC × 1/4 inch','1 rear sheet; 5.35 nominal PSU penetration','Rear. Actual PSU permitted depth is mandatory.'],
['SSD → tray','4 M3×4','1 tray gives 3 nominal drive penetration','Before board. Check drive limit; no extra nuts.'],
['Standoffs → tray','9 male-M3×5; 9 locknuts','1 tray + 2.4 nut; 1.6 tip; 9.525 stand height','Cable side before board; only actual board subset.'],
['Board → standoffs','9 M3×6','1.6 PCB gives 4.4 female engagement','Component side; supplier bore / thread depth gate.'],
['Bottom 140 fan → floor','4 M4×35 / 0.8 washers / 3.2 nuts','1 + 25 + 0.8 + 3.2 = 30; 5 tip','Underside / open case.'],
['Rear 140 fan → rear','4 M4×30 / 0.8 washers / 3.2 plain nuts','1 + 25 + 0.8 + 3.2 = 30; nominal flush','No thick nyloc. M4×35 clashes with optional bridge.'],
['Bond lug → rear','M4×10; suitable conductive lug / washer / nut','Dedicated Ø4.5, X130 / Z250','Rear / open side. Check actual lug thickness and engagement.']]
for i in range(2):
 p=page(f'Fastener stacks & access: {i+1} / 2','All lengths and engagements are nominal millimetres; purchased hardware and finished stacks must be measured.',tag='joints' if i==0 else None)
 table(p,40,145,[180,255,370,305],['Joint','Hardware','Stack / engagement','Access / qualification'],jointrows[:11] if i==0 else jointrows[11:],10,42)
 box(p,40,735,1110,40,'Keep nuts and tool approach accessible during assembly. Isolate power before service. Use appropriate removable locking where specified; do not infer a universal tightening torque from the nominal CAD envelopes.',10)
# 08 assembly
p=page('Build sequence: qualify, form, assemble','Do not start a full case cut until the process and physical-interface gates pass.',tag='assembly')
steps=[('01  Qualify the process','Cut coupons in actual material, grain direction, tooling and finish. Establish inside radius, K, springback and joggle offsets. Verify segmented-tool access for the 1238.0503 mm wrap. Laser or CNC metal cutting requires suitable metal tooling, workholding and chip control, not a generic wood router.'),('02  Cut, deburr and form','Use the cut-only DXFs without scaling. Deburr handles, grille webs, cable exits and PCI pockets. Form opposite-handed sleds. Preform all ten wrap ears downward; then joggle, floor and roof. Form tray, clips, carrier and selected optional supports to their section views.'),('03  Prepare threads and finish','Finish-drill and tap all nine M03 holes M3×0.5 through 3 mm steel; do not use the 1 mm rail as a structural tap. Fit-test before coating. Mask shield bands and bonding contacts. Check finished Ø5 insert pilots and Ø12.1 power-switch hole.'),('04  Fit inserts while access is open','Set ten RRE03-1 inserts in the fixed wrap ears, never through removable sides. The CAD shows only unset envelopes. Qualify nose access, bulb formation, spin resistance, mandrel travel and repeated removal before closing the chassis.'),('05  Join the chassis','Bolt four C clips between rear and wrap. Attach tray flanges with four M3 joints and connect rear through two T clips. Keep side access for plain nuts. Install M03 behind M02, then attach rail to rear on its spacers; dry-gauge the real covers/card.'),('06  Fit supported components','Install PSU bosses and bottom fan, standoffs and SSD before the motherboard. Check screw penetration and seating. Use only the selected board mounting subset. Install rear fan with M4×30 plain-nut stack; longer rear screws interfere with the optional bridge.')]
for i,(title,text) in enumerate(steps):
 col=i//3; row=i%3; para(p,40+col*575,160+row*195,535,title,text,145)
# 09 assembly service
p=page('Complete the build & preserve service access','These sequences are practical access plans, not an automated assembly-sweep validation.')
para(p,40,157,535,'07  Complete I/O pod','Bench-assemble I03, USB modules and washers to I02; fit audio with its supplied nut and retain the power switch. Trial plug insertion and screw bottoming. Capture I01 with the 0.5 mm gasket and four 1 mm pads. Refit I02 on the existing two M3×10 joints at X68/132, Z336, with 2.5 mm spacers. See I/O stack sheets.',130)
para(p,40,325,535,'08  Optional modules and GPU','Bench-assemble the optional 120 mm fan to F01, then attach the whole unit to the roof. Install GPU / real bracket; adjust G01/G02 only to a stiff, nonfan card surface. A 2 mm insulating pad contacts the nominal Z195 underside. It is not a shipping restraint.',130)
para(p,40,493,535,'09  Wiring, bonding and closure','Strain-relieve harnesses at carrier Ø3 tie points. Keep leads clear of fans; verify SATA connector space above Z300. Preserve PSU earth; never open or drill the PSU. Test continuity of chassis, both sleds, tray and carrier after finish. Add serviceable bonding braids if the electrical review requires them.',140)
box(p,40,686,535,70,'Fit nominal 0.2 mm conductive shims over 0.5 mm insert heads to close the 0.7 mm side gap. Do not pull the sled planes inward to hide a bad coated stack.',11)
para(p,620,157,530,'Tray removal','Isolate power and disconnect external cables. Remove side panels, unplug internal leads and remove GPU/support as needed. Release rear shield and cables, the two T connections and four flange bolts. Move forward enough to disengage rear interfaces, then extract through the open side; never force a connected board sideways.',155)
para(p,620,350,530,'Fascia / fan service','With the right side off, hold the two front screw heads and undo interior carrier nuts. Unplug and release restrained leads; withdraw the cage/face inward and service all module screws and nuts on the bench. Remove optional fan roof connections and service the fan/bracket on the bench, rather than reaching through its frame.',140)
para(p,620,530,530,'Before energizing or handling','Check fastener tips, cable insulation, grommet retention, grounding and actual selected-component fit. Run controlled loaded thermal tests after electrical checks. Handles are UNRATED: empty-case handling only until a controlled proof/load programme establishes a limit.',140)
# 10 datums
p=page('Source interfaces & controlling assembly datums','Global axes: front −Y, rear +Y, up +Z, motherboard component side +X. Do not substitute aperture centres for retention axes.',tag='datums')
table(p,40,145,[65,150,150],['Hole','Y (global)','Z (global)'],[[h['name'],fmt(h['Y']),fmt(h['Z'])] for h in C['mounting_holes']],10,26)
box(p,40,560,365,140,'All 12 tray positions are retained. Depicted ATX installs A,C,F,G,H,J,K,L,M only. Historical B and microATX R/S are not populated under that board. Check the actual motherboard subset; unused standoffs can short a PCB.',11)
para(p,445,158,700,'ATX / shield interface','A = (Y189.7318, Z141.51), NOT Z146.51. PCB Z125…429.8; rear Y199.8918; rear inner Y202; gap 2.1082. Tray component face X−116.5; PCB underside X−106.975, top X−105.375; 9.525 standoff height.',90)
para(p,445,283,700,'Rear I/O opening','X−109.2102…−64.7602; Z273.4884…432.2384. Opening 44.45 × 158.75, corner R0.8 in 1 mm steel. Preserve ATX’s 2.54 mm clear band on BOTH faces and mask coating. Source opening tolerance ±0.2032 and datum-chain tolerances apply; no blanket shop tolerance overrides them.',110)
para(p,445,428,700,'PCI retention and physical gauge','Seven screw axes: Y206.1148, Z147.4841 + n × 20.32 (n = 0…6). Aperture centres instead use Z139.1656 + n × 20.32. M03 lies Y203…217, X−1.7677…1.2323; outer retention face X2.2323. End fixings: Y214, Z130 / 272. Rear slit: X1…4.2, Z124…277 for Ø7 washers. Original M02 bracket reliefs remain.',125)
para(p,445,590,700,'PSU handed pattern / gauge stop','External AC-face source maps as X = 95 − drawing X; Z = 34 + drawing Y. Global (X,Z): (−49,114), (89,114), (89,50), (−25,40). Do not flip the PSU and assume this asymmetric pattern still fits. PCI legacy setback chains differ 0.4572 mm: gauge real cover/card locating tips and notches; if failed, revise rear, rail and tray tip-pocket set together before cutting.',150)
# 11 clearance
p=page('Nominal clearances & physical fit gates','Values are current digital envelope separations, not tolerances or guarantees of detailed retail component fit.')
labels=['PCB rear → rear inner','PCB top → roof inner','GPU front → upper front inner','GPU 35 reserve → side inner','170 cooler tip → side inner','170 cooler tip → optional fan','170 cooler tip → optional bracket','Optional fan frame → rear fan frame','Optional fan pan head → side','Bottom fan → front inner','Bottom fan → PSU 60 reserve','SSD body → left side inner','GPU support foot → bottom fan (X)']
table(p,40,145,[425,120],['Measured nominal separation','mm'],[[lab,fmt(v)] for lab,v in zip(labels,C['clearances_mm'].values())],11,30)
para(p,625,160,520,'SSD: relocated clear of standoff L','Body Y60…129.85, Z200…300, X−124.5…−117.5; relocated 104.065 mm rearward. Bottom holes Y64.065 / 125.785, Z286 / 209.4: 61.72 × 76.6. Rows 14 / 90.6 from connector-end Z300. Inferred 4.065 edge offset and drive boss seating require a sample.',140)
para(p,625,342,520,'Fan: small finished clearance','Optional fan frame X115…140; bracket X114…115. Ordinary 3 mm heads reach X143, leaving only 0.5 mm to the inner side at X143.5 before finish. Verify actual heads, coating and fan thickness. Rear M4×30 stack must give full plain-nut engagement.',140)
para(p,625,524,520,'What remains unknown','PSU support contact passes digitally for 140 / 160 / 180 mm depth. No reserve collisions are reported. Real socket, RAM, VRM, plugs, cables and GPU contact surfaces require physical checks. Integrated I/O uses published bounds plus explicit allocations; these are not OEM-exact bodies. Four SSD and four PSU fastener intrusions are intentional reference-envelope overlaps, not waived penetration limits.',155)
# drawing sheets 12..28
notes={
'S01-S02':'Cut TWO identical blanks; form OPPOSITE hands. Right outside planes X151 / 145; left X−151 / −145. Preserve the 6 mm joggle and original handle / 546 grille bores per side. Handles are unrated.',
'W01':'One continuous wrap. All ten ears fold DOWN in the assembled case; roof ears lie below the roof. Form ears first, front joggle next, floor then roof. Detailed 14-bend schedule follows the main drawing sheets.',
'I01':'Full 2C/2A/stereo/power; 46 × 168 flange behind 42 × 164 shell opening. C14×8 R2; A20×12 R1 are designer access cuts. Audio Ø6.1; power Ø12.1. Finished audio panel STRICTLY <1.2. Global port centres and rear mounting on I/O sheets.',
'M01':'Plain clearance holes only; 9.525 mm standoffs need rear locknuts. Fit only actual board subset. SSD holes and all 12 board datums are maintained. Upper-flange reliefs clear downward wrap ears. Remove GPU / cables before tray extraction.',
'M02':'Keep original bracket-relief profiles. Seven retention axes Y206.1148, Z147.4841 + n20.32, not aperture centres. Two end-return bend segments share an axis. Real cover/GPU gauge is mandatory for the 0.4572 mm legacy discrepancy.',
'M03':'Finish-drill and tap all NINE Ø2.5 pilots M3×0.5 through 3 mm steel. Seven retention axes and two separate end fixings; strip lies entirely rearward at Y203…217. Do not tap the 1 mm rail as structure.',
'R01':'Rear inner plane Y202. Shield clear band 2.54 mm each face; mask coating. PCI clearance slit X1…4.2, Z124…277 clears Ø7 washers without moving apertures. Protected Ø12 audio exit X130/Z280 and bonding hole X130/Z250.',
'I02':'Existing shell joints X68/132,Z336 retained: two M3×10 with 2.5 spacers. Four added Ø3.4 holes X72/128,Z308/386 match I03. Neutral-strip mapping is in the hole schedule. No welding or additional shell holes.',
'I03':'One common 68×88×1 steel plate. R4.5 open-edge scallops at X68/132,Z336 clear existing cage hardware. Top 20×2 notch clears power-tool allocation. Twelve Ø3.4 holes; no taps or bends. See I/O matching-hole table and concealed button-head stacks.',
'F01':'OPTIONAL. Bench-mount 120 mm fan with four M4×35, then two M3 roof joints. Frame X115…140; ordinary head to side only 0.5 mm before finish. Remove whole module for service.',
'G01':'OPTIONAL. Two M4×10 floor bolts share a 54 mm adjustment slot. Foot starts X96, 6 mm clear of bottom fan. Test stiffness and card contact; no transport or lifting rating.',
'G02':'OPTIONAL. Clamp to G01 with two M4×12. Top Z193 + 2 mm insulating pad to nominal GPU underside Z195. Contact only a stiff nonfan surface; remove if unsuitable.',
}
for panel in P:
 id=panel['id']; shorttitle=panel['label'].split('—')[-1].strip()
 p=page(f'{id}  /  {shorttitle}',f'{panel["material"]}  •  t = {panel["thickness_mm"]} mm  •  quantity {panel["quantity"]}  •  DXF/{id}.dxf  •  dimensions are nominal; do not scale the PDF',tag=id)
 vector(p,id,(45,145,710,600),panel['bends'],rot=(id=='W01'))
 x=790
 head(p,x,157,'DATUM & CUT LEGEND')
 box(p,x,170,355,84,f'Raw local origin = ({fmt(panel["DXF_origin_mm"][0])}, {fmt(panel["DXF_origin_mm"][1])}). DXF = raw − origin.\n{panel["local_axes"]}',10)
 box(p,x,258,355,72,'Black = exact cut paths. Teal dashed = bend neutral-BA midlines (PDF only). DXF is cut-only. Full holes: flat-hole-schedule.csv / DXF. Display rounding does not change source geometry.',10)
 box(p,x,339,355,118,notes.get(id,'One M3 joint per leg, with through screws, washers and accessible nuts. Form to the assembled section shown; preserve the identified floor / roof / tray hand. See joint schedule for service access.'),11)
 bends=panel['bends']
 if bends and id!='W01':
  yy=table(p,x,464,[52,72,92,139],['B / step','Turn','R / K / BA','DXF axis'],[[r[0],r[1],r[2],r[3]] for r in bendrows(panel)],8.5,27)
 else:
  yy=464
  if not bends:
   head(p,x,481,'NO BENDS: FLAT PART'); yy=499
  else:
   box(p,x,464,355,55,'14 bends: see dedicated wrap forming sheet. The two opposed low-angle bends are closely spaced in this overview.',10); yy=523
 # Section generated directly from virtual midline data, with numeric path coordinates.
 bs=next((b for b in bends if 'cross_section_midline_virtual_points' in b),None)
 if bs and id!='W01':
  pts=bs['cross_section_midline_virtual_points']; axes='XZ' if id in ['S01-S02','F01','G01','G02','M01'] else ('XY' if id.startswith('T') or id=='I02' else 'YZ')
  top=max(yy+18,580); head(p,x,top,'ASSEMBLED SECTION / '+axes)
  # schematic section, same dimensional aspect except tiny joggle enhanced via coordinate table
  xx=[a[0] for a in pts]; zz=[a[1] for a in pts]; sx=125/max(max(xx)-min(xx),1); sy=100/max(max(zz)-min(zz),1)
  def sp(a): return (x+25+(a[0]-min(xx))*sx,top+125-(a[1]-min(zz))*sy)
  for a,b in zip(pts,pts[1:]): p.draw_line(sp(a),sp(b),color=teal,width=2)
  for i,a in enumerate(pts):
   pt=sp(a); p.draw_circle(pt,2,color=teal,fill=teal); txt(p,pt[0]+5,pt[1]+3,str(i+1),8)
  box(p,x+185,top+12,170,136,'Schematic, not to scale\nVirtual midline vertices\n'+ '\n'.join(f'{i+1}: {fmt(a[0])}, {fmt(a[1])}' for i,a in enumerate(pts))+'\nTangency radii per table.',8.5)
 elif id=='M02':
  head(p,70,177,'END-RETURN SECTION / XY: SCHEMATIC')
  p.draw_line((90,210),(90,275),color=teal,width=2)
  p.draw_bezier((90,275),(90,285),(95,290),(105,290),color=teal,width=2)
  p.draw_line((105,290),(250,290),color=teal,width=2)
  txt(p,105,218,'Rail web mid-plane X1.7323',10)
  txt(p,270,285,'Return toward +X; Y199…200',10)
  txt(p,70,315,'+X →   +Y ↑   /   rear wall inner Y202; 2 mm spacer to return',10,teal)
  box(p,x,yy+20,355,138,'FORM DIRECTION: rail web is the YZ plane at X1.7323 mid-thickness. End returns extend toward +X to meet the rear interface. Preserve native radiused ends and bracket reliefs. Use CAD/Sheet Metal PC Case.FCStd for the full formed interface and gauge the purchased bracket before cutting.',10)
 else:
  cir=[e for e in D[id]['entities'] if e['type']=='CIRCLE']
  if id=='R01': cir=[e for e in cir if e['r']>=2.25][:6]
  if id=='W01': cir=[e for e in cir if abs(e['r']-2.5)<.001][:6]
  if id=='I03':
   head(p,x,529,'ALL 12 HOLES / Ø3.4')
   table(p,x,544,[115,120,120],['Group','DXF X pair','DXF Y pair'],[['Attach','6 / 62','5 / 83'],['C module','24 / 44','57 / 77'],['A module','19 / 49','13 / 34']],9,27)
   box(p,x,670,355,65,'Each row is all four X × Y combinations. Global coordinates = DXF + (66,303). Matching carrier holes are on the neutral-developed I02 flat.',10)
  elif cir:
   table(p,x,max(yy+15,540),[115,120,120],['Ø','DXF X','DXF Y'],[[fmt(2*e['r']),fmt(e['c'][0]),fmt(e['c'][1])] for e in cir[:6]],9,23)
 if id in ['C01','C02','C03','C04','T01','T02']:
  cir=[e for e in D[id]['entities'] if e['type']=='CIRCLE']
  table(p,65,175,[58,73,83],['Ø','DXF X','DXF Y'],[[fmt(e['r']*2),fmt(e['c'][0]),fmt(e['c'][1])] for e in cir],9,26)
 # persistent forming convention
 box(p,45,751,1100,28,'B = sheet-local bend index. Turn is SIGNED PATH-TURN, not an automatic UP/DOWN code. Use assembled section, axes and mirror hand; R/K/springback require shop coupons.',9,teal)
# wrap forming
p=page('W01  /  Complete forming schedule','Four main bends + ten integral ears. R = inside radius; K = provisional neutral factor; BA = neutral allowance. All coordinates in the normalized DXF.',tag='wrap-form')
wp=next(x for x in P if x['id']=='W01')
rows=[]
for i,b in enumerate(wp['bends']):
 a,z=b['flat_bend_lines_DXF_mm'][0]
 name=('Ear '+str(i+1)+' / '+('left' if i<5 else 'right')+' / '+b['axis'].split('ear at ')[1]) if i<10 else 'Main '+str(i-9)
 rows.append([name,str(b['suggested_forming_step']),fmt(b['angle_deg']),f'{b["inside_radius_mm"]} / {b["K"]} / {fmt(b["BA_mm"])}',f'({fmt(a[0])}, {fmt(a[1])})',f'({fmt(z[0])}, {fmt(z[1])})'])
y=table(p,40,140,[265,60,90,175,260,260],['Axis / hand','Step','Turn °','R / K / BA','DXF start (X,Y)','DXF end (X,Y)'],rows,10,26)
para(p,40,590,650,'Actual assembled fold direction','All ten ears point DOWN (−Z), including those at the roof. Their opposite signed angles distinguish left/right path hand, not up/down. Fixed flange outer X planes are ±142.8 upper / ±148.8 lower. Ear pilots assemble at Y−165/0/165, Z448 upper and Y−165/+165, Z11 lower.',105)
box(p,40,722,650,48,'Form order: ears → lower joggle → upper joggle → floor → roof. Confirm brake / segmented-finger access before the full wrap cut. No weld studs are used.',10)
# assembled YZ section schematic, vertices explicitly labelled
pts=wp['bends'][-1]['cross_section_midline_virtual_points']; sc=.29
for a,b in zip(pts,pts[1:]): p.draw_line((860+a[0]*sc,752-a[1]*sc),(860+b[0]*sc,752-b[1]*sc),color=teal,width=2)
head(p,744,585,'YZ SECTION: +Y → / +Z ↑')
box(p,938,608,205,150,'Front planes Y−203 / −199\nFloor outside Z25\nRoof outside Z458\nLower width 298\nUpper width 286\nJoggle offset 4\nTaper only on straight inclined web.',10)
# Completed I/O: exact cut vectors, exploded stack, typed topology and allocation routes.
def arrow(p,a,b,color=teal):
 p.draw_line(a,b,color=color,width=1.2)
 dx,dy=b[0]-a[0],b[1]-a[1]; n=math.hypot(dx,dy); ux,uy=dx/n,dy/n
 p.draw_polyline([(b[0]-7*ux+3*uy,b[1]-7*uy-3*ux),b,(b[0]-7*ux-3*uy,b[1]-7*uy+3*ux)],color=color,width=1.2)

p=page('Front I/O: completed pod & matching interfaces','Exact vector cuts below come from current drawing-geometry.json; dimensions and global interfaces from io-interfaces.json. Do not scale the PDF.',tag='IO')
head(p,48,155,'I01 / FULL FASCIA')
vector(p,'I01',(40,170,265,490))
head(p,335,155,'I03 / COMMON CONCEALED PLATE')
vector(p,'I03',(320,175,425,460))
box(p,40,687,690,77,'I01 1 mm aluminium; finished audio panel STRICTLY <1.2 mm. I03 one 68 × 88 × 1 mm steel plate, no bends or taps. The top 20 × 2 notch and two R4.5 edge scallops are actual cut geometry, not separate crossbars.',11)
head(p,780,155,'GLOBAL MATCHING DATUMS / X,Z')
table(p,780,174,[165,200],['Interface','Centres / cut'],[
 ['I01, all X100','P400; C380 / 360; A337 / 316; audio281'],
 ['I02 ↔ I03','X72 / 128 × Z308 / 386; four Ø3.4'],
 ['I03 ↔ C flanges','X90 / 110 × Z380 / 360; four Ø3.4'],
 ['I03 ↔ A flanges','X85 / 115 × Z337 / 316; four Ø3.4'],
 ['Retained cage joints','X68 / 132, Z336; R4.5 scallops around hardware'],
 ['Top notch bounds','X90…110; Z389…391']],10,37)
para(p,780,535,365,'Plug access is a design allocation','C14 × 8 R2; A20 × 12 R1. Trial C hoods ≤12.2 × 6.4; A ≤18 × 10. C rectangular hood corners have ~0.37 mm nominal clearance, not a coated-tolerance guarantee. Larger / locking hoods need separate qualification.',133)
box(p,780,704,365,66,'I02 window X81…119 / Z260…412 and shell joints are unchanged. Full developed coordinates: panel sheets and flat-hole-schedule.csv.',10)

p=page('I/O exploded section: concealed ordinary hardware','Exploded offset-section schematic through mounting axes: spacing exaggerated; labelled global Y planes control. Heads are hidden by fascia / wrap in the assembled case.',tag='IO-stack')
# Exact planes in the labels; schematic exploded positions intentionally separate touching parts.
cols=[(70,'I01 / 1 mm Al','Y−197.5…−196.5'),(270,'I02 / 1 mm steel','Y−195.5…−194.5'),(470,'I03 / 1 mm steel','Y−194.5…−193.5'),(675,'Spacer washers','0.5 → flange Y−193'),(900,'USB module','Flange Y−193')]
for x,label,datum in cols:
 head(p,x,160,label); box(p,x,174,200,50,datum,10)
for x,color,intervals in [(100,sand,[(235,300),(350,420)]),(300,muted,[(235,275),(390,440)]),(500,teal,[(245,300),(350,425)])]:
 for ya,yb in intervals:p.draw_rect(f.Rect(x,ya,x+14,yb),color=color,fill=color)
# Nose and body are explicitly illustrative, not copies of supplier CAD.
p.draw_rect(f.Rect(910,270,925,395),color=teal,fill=pale)
p.draw_rect(f.Rect(925,303,1100,362),color=teal,fill=pale)
p.draw_rect(f.Rect(855,311,910,354),color=teal)
for yy in [286,375]:
 p.draw_rect(f.Rect(697,yy-10,704,yy+10),color=sand,fill=sand)
 p.draw_rect(f.Rect(450,yy-9,466,yy+9),color=ink,fill=pale)
 p.draw_line((466,yy),(540,yy),color=ink,width=2)
 p.draw_line((540,yy),(920,yy),color=muted,dashes='[3 3] 0',width=.7)
for a,b in [(155,265),(345,425),(555,650),(750,835)]:arrow(p,(a,335),(b,335))
box(p,65,451,240,48,'FRONT −Y  →  REAR +Y\nI02 window clears modules.',10,teal)
box(p,350,451,250,48,'Eight M3×4 button screws\nFront hex-key access on bench.',10)
box(p,660,451,235,48,'Eight 0.5 mm washers\nTwo under each module flange.',10)
box(p,930,451,210,48,'Reference body / nose\nNot an OEM-exact model.',10)
para(p,40,532,535,'Module stack / finish-sensitive gap','M3×4 ISO 7380-1: head max Ø5.7 × 1.65. I03 1 + washer 0.5 → 2.5 nominal engagement into embedded M3 nut. Head front Y−196.15 clears I01 back by only 0.35. C nose Y−196.2 gives 1.3 recess. A forward projection is unpublished: 4.5 is a RESERVE recess, not an OEM-exact setback.',130)
para(p,620,532,530,'I03 attachment stack / concealed by wrap','Four M3×6 ISO 7380-1 through I02 + I03, rear 0.5 washer + plain 2.4 nut: 4.9 stack / 1.1 tip. Head Y−197.15 clears wrap inner Y−198 by 0.85. R4.5 scallops clear retained carrier hardware by 1 nominal; the top notch clears the R10 power-tool allocation by 1.',130)
box(p,40,700,1100,72,'ASSEMBLY / SERVICE: deburr and trial first; attach I03 to removed I02, then modules; install audio / power on the removed face before closing the carrier. Capture I01 with existing gasket/pads, then refit carrier. Disconnect leads and release two existing I02 nuts to withdraw inward for bench service. Qualify coating, flatness, screw bottoming and actual power nut/tool; keep the Y−193 flange datum if factory screws/spacers are needed.',11,orange)

p=page('Typed electrical topology & mutually exclusive variants','Commercial passive extension / header-adapter architecture, NOT a direct harness or USB-IF-certified cable chain.',tag='IO-topology')
for i,(port,lead,adapt,host) in enumerate([
 ('C1 / Z380','U4S5C01C08-010 / 1 m\nPanel-C female → C male','67234\nC female → Type-E 20p male','Independent supported\nType-E host #1'),
 ('C2 / Z360','U4S5C01C08-010 / 1 m\nPanel-C female → C male','67234\nC female → Type-E 20p male','Independent supported\nType-E host #2'),
 ('A1 + A2','2 × USR2-AA-1M / 1 m\nPanel-A female → A male','82941 / 45 cm incl. ends\n2 A females → 19p female','One supported 19-pin\nhost header / two A ports'),
 ('Stereo','FRONTX P0902_036\n3.5 mm female → male / 914.4 mm','Protected rear exit\nSupplied nut at fascia','Actual rear stereo output\nNOT HD_AUDIO / headset mic / amp'),
 ('Power','PV0F24011 momentary\nExisting switch retained','Separate insulated pair\nNot mains or USB power','Actual motherboard\nPWR_SW pin pair')]):
  y=144+i*75
  for x,w,text in [(40,135,port),(200,340,lead),(580,285,adapt),(905,245,host)]:
   p.draw_rect(f.Rect(x,y,x+w,y+60),color=None,fill=pale)
   box(p,x+10,y+9,w-20,48,text,10)
  for a,b in [(175,198),(540,578),(865,903)]:arrow(p,(a,y+30),(b,y+30))
head(p,40,545,'ONE FASCIA PER CASE / QUANTITIES FOR EACH CONFIGURATION')
table(p,40,560,[250,185,90,185,200,200],['DXF fascia','C / A / audio / P','I03','67234 / 82941','M3×4 / spacers','I03 M3×6 / nut / washer'],[
 [v['fascia'],f'{v["C"]} / {v["A"]} / {v["audio"]} / {v["power"]}',str(v['I03']),f'{v["Delock67234"]} / {v["Delock82941"]}',f'{v["module_screws"]} / {v["module_washers"]}',f'{v["I03_attachment_screws"]} / {v["I03_attachment_nuts"]} / {v["I03_attachment_washers"]}'] for v in IO['variants']],9.5,27)
box(p,40,730,1100,48,'C1 keeps the upper C380; lower C360 is blank. Alternatives are under DXF/Alternatives. I02, gasket and pads remain. Omit absent-port cables / restraints. NO Y splitter, legacy-A-to-C-socket adapter or A-male/A-male cable. Standard 5 V only; no PD / Alt Mode / USB4 / Thunderbolt claim.',10,orange)

p=page('Cable paths, service loops & controlled rear exit','Construction paths are nonmaterial design allocations, excluded from solid STEP. They do not certify unplaced tails or vendor minimum bend radii.',tag='IO-routing')
head(p,40,158,'USB ENTRY + ONE LOOP / TOP VIEW (+X →, +Y ↑)')
# Exact entry and loop centre coordinates; same plan repeats at four independent Z levels.
def rp(x,y):return (245+x*2.5,455-(y+140)*2.5)
r=IO['routes'][0]; c=rp(*r['loop_center'][:2])
p.draw_rect(f.Rect(*rp(-55,-85),*rp(105,-195)),color=muted,dashes='[3 3] 0',width=.5)
# Open270deg arc: no closed ring crossing the entry.
for theta in [90,180,270]:
 a=math.radians(theta);b=a+math.pi/2;k=4/3*math.tan(math.pi/8);R=50
 p.draw_bezier(rp(R*math.cos(a),-140+R*math.sin(a)),rp(R*(math.cos(a)-k*math.sin(a)),-140+R*(math.sin(a)+k*math.cos(a))),rp(R*(math.cos(b)+k*math.sin(b)),-140+R*(math.sin(b)-k*math.cos(b))),rp(R*math.cos(b),-140+R*math.sin(b)),color=teal,width=2)
p.draw_line(rp(100,-155.5),rp(100,-140),color=teal,width=2)
# Quarter-circle, radius50 about (50,-140), exact cubic approximation.
p.draw_bezier(rp(100,-140),rp(100,-112.3857625),rp(77.6142375,-90),rp(50,-90),color=teal,width=2)
p.draw_line(rp(50,-90),rp(0,-90),color=teal,width=2)
p.draw_circle(c,2,color=teal,fill=teal)
box(p,178,405,135,46,'R50 / open 270°\nCentre X0 / Y−140',10,teal)
box(p,385,497,180,65,'Module relief exit\nX100 / C Y−155.5\nA Y−156.5',10)
arrow(p,rp(50,-140),rp(50,-105)) # pointer only; tail routing remains board dependent
box(p,45,208,390,75,'Flexible tail → actual supported host location\nHeader positions are BOARD DEPENDENT.\nRepeat at Z380, 360, 337 and 316.',11)
box(p,40,615,535,140,'USB swept loop bounds: X±55 / Y−195…−85. Reserve Ø10 around centreline; R50 and Ø10 are designer allocations, NOT OEM minimum bend / cable OD. Each OPEN 270° loop consumes 235.62 mm; ends X50/Y−140 without crossing its entry. A 1 m lead leaves ~619–620 mm after entry + loop; deduct provisional connector-end allowances of 85 C / 90 A → ~529–535 mm flexible tail, subject to actual length datum.',11)
para(p,625,158,520,'Secure the mating pairs and support the headers','Use existing I02 return holes: left X62 / Y−181,−177 / Z300,380 for a cushioned lacing spine. Four broad straps retain loops; two retain the A mated pairs in a tethered insulated cradle above the GPU. Supply 8 releasable 2.5 mm ties, 6 broad straps and protective sleeves. Support Type-E leads near actual headers; never lever the PCB sockets.',145)
para(p,625,343,520,'Audio / power lanes: right perimeter','Audio exits at (X100,Y−149.5,Z281), follows the protected right lane to rear X130/Z280 below the optional fan, then reaches the actual stereo output outside. Secure and sleeve the external run. Power has a separate insulated pair route to PWR_SW. Neither route is a safety-earth conductor.',118)
# Controlled order schematic, not a claim that a plug passes the grommet ID.
head(p,625,508,'REAR AUDIO: ASSEMBLE IN THIS ORDER')
for i,(title,text) in enumerate([('1  BARE Ø12','Remove split grommet; deburr. Pass hood ≤Ø11.'),('2  SPLIT ID9','Fit grommet around cable AFTER the plug passes.'),('3  RESTRAIN','Verify cable OD fit; sleeve and strain-relieve both sides.')]):
 x=625+i*177
 p.draw_rect(f.Rect(x,527,x+165,638),color=None,fill=pale)
 box(p,x+8,536,150,25,title,11,teal);box(p,x+8,565,149,68,text,10)
box(p,625,670,520,100,'Never force the plug through nominal ID9. Reject hoods >Ø11 under this design. Verify actual cable OD / bend radius, length and all final fan clearances. Continuous-route checks cover the shown allocations, not every board-specific tail; distribute slack in separate supported loops rather than tight coils.',11,orange)

p=page('I/O evidence, allocations & prototype acceptance','Public source links only. No supplier PDF / STEP is reproduced or relicensed; no dimensions are inferred by scaling photographs or drawings.',tag='IO-evidence')
table(p,40,145,[185,370,555],['Selected item','Published controlling information','Explicit allocation / physical acceptance'],[
 ['Newnex C\nU4S5C01C08-010','30 × 8 flange; M3 pitch20; 3.2 nose; rear37.5 incl. Ø9.3 relief; 1 m. Male hood35 × 12.2 × 6.4. CC/VCONN + four SS pairs in wire table.','C body/relief partition, corners, mouth detail and flange thickness are not OEM-exact. Confirm plug insertion, all 4 local C orientations (2 rear × 2 front) and actual thread bottoming. Nominal recess1.3; C hood limit12.2 × 6.4.'],
 ['Newnex A\nUSR2-AA-1M','Catalogue links USR2-A family: flange38.5 × 13.7; M3 pitch30; nose width17.8; body26.5 / rear36.5; 1 m.','Retail variant must match family drawing. Forward projection unpublished: zero projection allocated → 4.5 RESERVE recess, not OEM-exact. A relief diameter and detailed mouth are allocations.'],
 ['Delock 67234 / 82941','67234 approx18 × 15 × 7. 82941 dual A female / 19-pin female, 45 cm incl. connectors. Manufacturer-indexed data; direct downloads bot-challenged.','67234 + hood service reserve55 × 20 × 15; A cradle96 × 25 × 18. No OEM CAD or actual header positions claimed. Secure added connections and test the whole host chain.'],
 ['FRONTX P0902_036','36 in / 914.4 mm; Ø6.1 hole; body Ø11.5 ×32 +15 relief. Supplied nut Ø8 ×1.8; exposed thread3.','Finished panel STRICTLY <1.2. Use supplied nut; thread designation unpublished. Nominal1 panel +1.8 nut leaves0.2 tip. Body ends Y−149.5. Rear-output stereo only.']],10,59)
head(p,40,548,'PUBLIC PRIMARY / COMMERCIAL SOURCE LINKS')
# Linked labels avoid long supplier URLs colliding with page margins; full URLs remain in io-interfaces.json.
links=[('Newnex catalogue',0),('Newnex C drawing / rev A',1),('Newnex USR2-A family drawing',2),('Selected USR2-AA-1M listing',3),('Delock 67234 manufacturer sheet',4),('Delock 82941 manufacturer sheet',5),('FRONTX 36 in product',6),('FRONTX audio dimensions',7),('M3×4 button screw / TR00004815-000',8)]
for i,(label,idx) in enumerate(links):
 col=i//5; row=i%5; x=40+col*565;y=568+row*25
 box(p,x,y,540,24,label,10,teal)
 p.insert_link({'kind':f.LINK_URI,'from':f.Rect(x,y,x+540,y+24),'uri':IO['sources'][idx]})
box(p,40,714,1100,60,'ACCEPTANCE: measure finished 0.35 / 0.85 head gaps, washer stack, screw engagement/bottoming, hood corners/recess and audio thickness. Test enumeration, speed, hot-plug, all 4 local C orientations (2 rear × 2 front) and host current budget. Component ratings do not establish chain performance. Mechanical, thermal, bonding and safety prototype checks remain mandatory.',11,orange)
# coupons two pages
couponnotes=[
('QC01-steel-R1','1 mm mild steel; qty 1','90° to 40 × 40 outside legs. Bend at DXF X39.115265392; R1 / K0.42 / BA2.230530784.'),
('QC02-side-R2p25','1.5 mm 5052-H32; qty 1','90° to 40 × 40 outside legs. Bend at DXF X38.488384766; R2.25 / K0.40 / BA4.476769531.'),
('QC03-support-R3','3 mm mild steel; qty 1','90° to 40 × 40 outside legs. Bend at DXF X37.298672286; R3 / K0.40 / BA6.597344573.'),
('QC04-rivnut-power','1 mm mild steel; qty 1','Ø5 insert / Ø3.4 side clearance / Ø12.1 power hole. Qualify setter, bulb, spin, torque, finished head stack and removal. Separately test the switch on 1 mm aluminium.'),
('QC05-side-joggle','1.5 mm 5052-H32; qty 1','Opposed 26.5651° turns, R2.25 / K0.40. DXF Y39.775442927 and 53.096838613. Virtual Z40…52, offset 6; BA1.321395686 per bend.'),
('QC06-wrap-joggle','1 mm mild steel; qty 1','Opposed 18.4349° turns, R1 / K0.42. DXF Y39.903887573 and 52.523051021. Virtual Z40…52, offset 4; BA0.456885787 per bend.')]
for ci in range(2):
 p=page(f'Process coupons & qualification: {ci+1} / 2','Coupon dimensions are nominal starting points. Record material, grain, tooling, inside radius, springback, finish and measured result.',tag='coupons' if ci==0 else 'joggle-coupons')
 for j,(id,mat,note) in enumerate(couponnotes[ci*3:(ci+1)*3]):
  x=40+j*380
  head(p,x,160,id)
  box(p,x,174,350,40,mat,11)
  q,s=vector(p,id,(x,220,350,310),dimensions=True)
  axes=[]
  if ci==0: axes=[('x',[39.115265392,38.488384766,37.298672286][j])]
  elif j>0: axes=[('y',z) for z in ([39.775442927,53.096838613] if j==1 else [39.903887573,52.523051021])]
  for ax,v in axes:
   a,b=((v,0),(v,D[id]['height'])) if ax=='x' else ((0,v),(D[id]['width'],v))
   p.draw_line(q(a),q(b),color=teal,dashes='[4 3] 0',width=.8)
  box(p,x,554,350,145,note+' All coupon DXF origins are (0,0); do not scale from this PDF.',11)
 box(p,40,718,1100,55,'Pass gate: establish the actual R/K and springback before main cutting; verify the low-angle joggle offsets, not only the 90° bend tests. Qualify the bolted carrier stack with actual spacers/pads/gasket. If outcomes require geometry changes, update CAD, flats and schedules together.',11,teal)
# validation page 33
p=page('Qualification record & digital export status','Digital checks are reported from the current kit JSON. These are not physical tests or independent certification.',tag='validation')
table(p,40,145,[345,230],['Digital result','Current value'],[
['Native shaped leaves / solids',f'{EV["fcstd"]["objects"]} / {EV["fcstd"]["solids"]}'],['Native / STEP summed volume',f'{EV["fcstd"]["volume_mm3"]:,.3f} mm³'],['Native / STEP export validator','PASS' if EV['passed'] else 'FAIL'],['Serialized DXFs / closed loops',f'{len(DV)} / {sum(x["serialized_closed_loops"] for x in DV)}'],['Open nodes / duplicate entities',f'{sum(x["open_nodes"] for x in DV)} / {sum(x["duplicate_entities"] for x in DV)}'],['Largest DXF readback area error',f'{max(x["serialized_area_error_mm2"] for x in DV):.6g} mm²'],['Mapped circles / maximum mismatch',f'{sum(x["matched_circular_cuts"] for x in FH)} / {max(x["maximum_error_mm"] for x in FH):.6g} mm'],['Neutral development residual max',f'{max(abs(x["error_mm3"]) for x in DEV):.6g} mm³'],['I/O clearance / portable rebuild',('PASS' if IC['passed'] else 'FAIL')+' / '+('PASS' if IS['passed'] else 'FAIL')]],10,34)
para(p,40,555,575,'Interpretation and explicit intersections','19 main sheet instances are valid single solids; 18 unique developments include the K-neutral volume correction. No structural-sheet collisions. Nine intentional M03 tap-drill/thread-major overlaps and eight SSD/PSU screw-envelope intrusions remain explicit. The opposite sled adds 551 mirrored circular cuts. No STL claim. I/O: zero unexpected solid clashes; 10 continuous swept routes / 41 different-route checks. USB loop minimum 3 mm; audio ~2.994 mm. Source rebuild and standalone finish are idempotent.',145)
box(p,40,715,575,55,'Current reports: io-export-validation.json; io-clearance-check.json; io-source-validation.json. Panel STEP: model-export-check.json. DXF and development checks use serialized cut geometry.',10,teal)
head(p,660,160,'MANDATORY PHYSICAL SIGN-OFF')
items=['Material / bend / joggle / forming-tool coupons','Insert setting, finished shim stack, repeated removal','Bolted carrier stack and exact switch fit / insulation','Real PCI cover / GPU bracket and rear shield gauge','PSU support seating and permitted screw penetration','Motherboard / cooler / RAM and standoff subset','SSD boss seating, screw limit and SATA cables','Fan thickness / heads / full nut engagement','GPU support contact and stiffness, if installed','I/O hood fit, finished head gaps, screw bottoming, headers','Cable protection, grommet, strain relief and reach','Grounding continuity with actual finish','Loaded thermal tests; handling proof/load programme']
for i,t in enumerate(items):
 p.draw_rect(f.Rect(662,183+i*37,672,193+i*37),color=muted,width=.8)
 box(p,685,178+i*37,460,32,t,10.5)
box(p,660,690,485,73,'No physical prototype, load rating, fatigue, vibration, acoustics, thermal, EMI/ESD or electrical-safety certification is represented. Record actual results before declaring any build ready.',11,orange)
# references page 34
p=page('References, source files & document control','Supplier drawings are cited, not redistributed. The full CERN-OHL-P v2 licence is included separately as LICENSE.txt.')
for i,r in enumerate([r for r in REFS if r['topic'] not in ['USB-C','USB-A','Audio']]):
 col=i//7; row=i%7; x=40+col*570; y=147+row*76
 txt(p,x,y,r['topic']+': '+r['source'],10,teal)
 box(p,x,y+9,530,53,r['url'],8.5)
box(p,40,692,535,80,'Source authority: IO-ASSEMBLY.md / io-interfaces.json for completed I/O; current JSON/CSV schedules and ASSEMBLY-NOTES.md for legacy case details. Vector cut art uses drawing-geometry.json; bend lines use explicit flat_bend_lines_DXF_mm. Full coordinates remain in DXF / CSV. This script does not modify geometry.',10)
box(p,620,692,530,80,'Carrier fasteners are two ordinary M3×10 through-bolts, already included in the hardware BOM. The purchasing list is not an additional quantity. No welding is required.',10,orange)
# Retail citations, compact but legible, attached as PDF metadata links via existing compatibility page
cp=doc[2]
# intentionally cite manufacturer product pages without redistributing their drawings
box(cp,40,751,1100,28,'Retail dimensional references: nvidia.com (RTX 4080 FE); noctua.at (NH-D15, NF-A14 PWM); corsair.com (RM750e 2023); semiconductor.samsung.com (870 EVO). Verify exact revision.',8.5,muted)
# finish and proof
for n,p in enumerate(doc):
 # Collect all actual extracted text boxes to catch page-boundary clipping.
 for b in p.get_text('dict')['blocks']:
  if b['type']!=0: continue
  for line in b['lines']:
   for span in line['spans']:
    r=f.Rect(span['bbox'])
    if r.x0<0 or r.y0<0 or r.x1>W+.1 or r.y1>H+.1: raise RuntimeError(f'Out of page text {n+1}: {span["text"]}')
overlaps=[]
for n,p in enumerate(doc):
 spans=[s for b in p.get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] for s in l['spans']]
 for i,a in enumerate(spans):
  for b in spans[i+1:]:
   rr=f.Rect(a['bbox']) & f.Rect(b['bbox'])
   if rr.width>1 and rr.height>2:
    overlaps.append({'page':n+1,'a':a['text'],'b':b['text']})
PROOF.mkdir(parents=True,exist_ok=True)
(PROOF/'text-overlap-check.json').write_text(json.dumps({'overlaps':overlaps,'pass':not overlaps},indent=2))
if overlaps: raise RuntimeError('Overlapping text: '+str(overlaps))
doc.set_metadata({'title':'Sheet Metal PC Case: Drawings and Build Guide','author':'Sheet Metal PC Case engineering kit','subject':'Unprototyped; integrated 2C/2A/stereo/power; qualify before full cut','keywords':'CERN-OHL-P-2.0, A3, engineering prototype'})
doc.set_toc([[1,p.get_text().splitlines()[1],i+1] for i,p in enumerate(doc)])
doc.save(OUT,garbage=4,deflate=True)
PROOF.mkdir(parents=True,exist_ok=True)
for tag in ['cover','assembly','W01','wrap-form','S01-S02','M01','M02','M03','IO','IO-stack','IO-topology','IO-routing','IO-evidence','I01','I02','I03','validation','coupons','joggle-coupons']:
 p=doc[marks[tag]]; p.get_pixmap(matrix=f.Matrix(1.3,1.3),alpha=False).save(PROOF/(tag+'.png'))
(PROOF/'text-bbox-checks.json').write_text(json.dumps({'pages':len(doc),'textboxes':len(checks),'all_fit':all(x['remaining']>=-.01 for x in checks),'page_bounds_pass':True,'checks':checks},indent=2))
for i,p in enumerate(doc):
 p.get_pixmap(matrix=f.Matrix(.8,.8),alpha=False).save(PROOF/(f'page-{i+1:02d}.png'))
(PROOF/'page-index.json').write_text(json.dumps([{'page':i+1,'title':p.get_text().splitlines()[1]} for i,p in enumerate(doc)],indent=2))
(PROOF/'page-map.json').write_text(json.dumps({k:v+1 for k,v in marks.items()},indent=2))
print(OUT); print('Pages:',len(doc)); print('Proofs:',PROOF)
