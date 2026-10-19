# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Generalized analytical DXF exporter. Explicit serialized read-back is mandatory below."""
import sys,os,shutil,json,math,collections,csv
exe=shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
if exe:sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))),'lib'))
import FreeCAD as A,Part
V=A.Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));work=root+'/CAD';out=root+'/DXF';results=[];allgeom={}
records=json.load(open(root+'/panels.json'));d=A.openDocument(work+'/Sheet Metal PC Case Flat Patterns.FCStd')
for ob in list(d.Objects):
 if ob.Label not in [r['id'] for r in records]:d.removeObject(ob.Name)
def entity(code,**kw):return dict(type=code,**kw)
def exportshape(pid,shape,folder):
 assert shape.isValid() and len(shape.Solids)==1,(pid,'flat invalid/disconnected')
 bb=shape.BoundBox;ox,oy=bb.XMin,bb.YMin
 faces=[f for f in shape.Faces if f.BoundBox.ZLength<1e-6 and abs(f.BoundBox.ZMin-bb.ZMax)<1e-6]
 face=max(faces,key=lambda f:f.Area);geom=[]
 for wire in face.Wires:
  for e in wire.Edges:
   c=e.Curve
   if isinstance(c,Part.Circle):
    cx,cy=c.Center.x-ox,c.Center.y-oy;r=c.Radius
    p=e.valueAt(e.FirstParameter);q=e.valueAt(e.LastParameter)
    if p.distanceToPoint(q)<1e-6:geom.append(entity('CIRCLE',c=[cx,cy],r=r));continue
    m=e.valueAt((e.FirstParameter+e.LastParameter)/2)
    ang=lambda v:math.degrees(math.atan2(v.y-c.Center.y,v.x-c.Center.x))%360
    a,b,mid=ang(p),ang(q),ang(m)
    if (mid-a)%360>(b-a)%360:a,b=b,a
    geom.append(entity('ARC',c=[cx,cy],r=r,a=a,b=b))
   elif isinstance(c,Part.Line):
    p=e.Vertexes[0].Point;q=e.Vertexes[-1].Point;geom.append(entity('LINE',p=[p.x-ox,p.y-oy],q=[q.x-ox,q.y-oy]))
   else:raise ValueError((pid,'nonanalyticcut',str(type(c))))
 # exactendpointgraphdegreechecks; fullcirclesareclosedthemselves
 endpoints=[];edges=[]
 def pt(c,r,a):a=math.radians(a);return [c[0]+r*math.cos(a),c[1]+r*math.sin(a)]
 for g in geom:
  if g['type']=='LINE':p,q=g['p'],g['q'];edges.append(Part.makeLine(V(*p,0),V(*q,0)))
  elif g['type']=='ARC':
   p,q=pt(g['c'],g['r'],g['a']),pt(g['c'],g['r'],g['b']);m=pt(g['c'],g['r'],g['a']+((g['b']-g['a'])%360)/2)
   edges.append(Part.Arc(V(*p,0),V(*m,0),V(*q,0)).toShape())
  else:
   edges.append(Part.makeCircle(g['r'],V(*g['c'],0)));continue
  endpoints +=[tuple(round(v,5) for v in p),tuple(round(v,5) for v in q)]
 degree=collections.Counter(endpoints);bad={str(k):v for k,v in degree.items() if v!=2};assert not bad,(pid,bad)
 wires=[Part.Wire(chain) for chain in Part.sortEdges(edges)]
 assert all(w.isClosed() for w in wires),(pid,[(len(w.Edges),len(w.Vertexes),[(v.Point.x,v.Point.y) for v in w.Vertexes][:4]) for w in wires if not w.isClosed()])
 areas=sorted([Part.Face(w).Area for w in wires],reverse=True);rtarea=areas[0]-sum(areas[1:]);assert abs(rtarea-face.Area)<1e-4,(pid,rtarea,face.Area)
 # R12ASCII,pureCUTlayer,noengraving,bendlinesorconstructionentities.
 lines=[]
 def pair(c,v):lines.extend([str(c),str(v)])
 pair(0,'SECTION');pair(2,'HEADER');pair(9,'$ACADVER');pair(1,'AC1009');pair(9,'$INSUNITS');pair(70,4);pair(9,'$MEASUREMENT');pair(70,1);pair(0,'ENDSEC');pair(0,'SECTION');pair(2,'TABLES');pair(0,'TABLE');pair(2,'LAYER');pair(70,1);pair(0,'LAYER');pair(2,'CUT');pair(70,0);pair(62,7);pair(6,'CONTINUOUS');pair(0,'ENDTAB');pair(0,'ENDSEC');pair(0,'SECTION');pair(2,'ENTITIES')
 for g in geom:
  pair(0,g['type']);pair(8,'CUT')
  if g['type']=='LINE':
   for c,v in [(10,g['p'][0]),(20,g['p'][1]),(30,0),(11,g['q'][0]),(21,g['q'][1]),(31,0)]:pair(c,round(v,8))
  else:
   for c,v in [(10,g['c'][0]),(20,g['c'][1]),(30,0),(40,g['r'])]:pair(c,round(v,8))
   if g['type']=='ARC':pair(50,round(g['a'],8));pair(51,round(g['b'],8))
 pair(0,'ENDSEC');pair(0,'EOF');open(folder+'/'+pid+'.dxf','w').write('\n'.join(lines)+'\n')
 results.append({'part':pid,'valid_flat':True,'solids':1,'closed_loops':len(wires),'entities':len(geom),'width':bb.XLength,'height':bb.YLength,'area_mm2':face.Area,'curve_roundtrip_area_mm2':rtarea,'area_error_mm2':abs(rtarea-face.Area),'open_nodes':len(bad)})
 allgeom[pid]={'entities':json.loads(json.dumps(geom),parse_float=lambda x:round(float(x),8)),'width':bb.XLength,'height':bb.YLength,'origin_shift':[ox,oy]}
for r in records:
 exportshape(r['id'],d.getObject(r['id'].replace('-','_')).Shape if d.getObject(r['id'].replace('-','_')) else next(o.Shape for o in d.Objects if o.Label==r['id']),out)
# Supplemental cut files are alternative/nonassembly sheets, never included in assembly STEP.
extras=[]
def supplemental(pid,s,folder,material,notes):
 os.makedirs(folder,exist_ok=True);exportshape(pid,s,folder);o=d.addObject('PartDesign::Feature','Extra');o.Label=pid;o.Shape=s
 extras.append(dict(id=pid,quantity=1,thickness_mm=s.BoundBox.ZLength,material=material,folder=os.path.relpath(folder,root),notes=notes))
# Selected full I01 is the default. Alternatives are mutually exclusive, NOT sample templates.
from finish_io import capsule, rounded, boreflat
A.ParamGet('User parameter:BaseApp/Preferences/Document').SetBool('CreateBackupFiles',False)
shutil.rmtree(out+'/Sample-gated-IO',ignore_errors=True)
fas=next(o.Shape for o in d.Objects if o.Label=='I01')
blank=capsule()
supplemental('I00-fully-blank-option',blank,out+'/Alternatives','aluminium','Alternative to I01; omit all ports/power/I03/module hardware. Same captured fascia. Never count as extra main sheet.')
power=boreflat(blank,100,400,6.05)
supplemental('I01-power-only',power,out+'/Alternatives','aluminium','Backward-use alternative: power only; omit USB/audio/I03 and their hardware, retain I02 carrier. No sample template.')
one=fas.fuse(rounded(93,356,14,8,2,1)).removeSplitter()
supplemental('I01-C1',one,out+'/Alternatives','aluminium','One C atZ380 only; lowerC Z360 BLANK. Retain2A/audio/power/commonI03. Omit lowerC module, one67234, twoM3x4 and two0.5washers. One independentType-E host required.')
for pid,t,R,K in [('QC01-steel-R1',1,1,.42),('QC02-side-R2p25',1.5,2.25,.40),('QC03-support-R3',3,3,.40)]:
 BA=math.pi/2*(R+K*t);L=80-2*(R+t)+BA
 supplemental(pid,Part.makeBox(L,40,t),out+'/Process-coupons','5052-H32 aluminium' if t==1.5 else 'mild steel','Bend90deg to40x40 outside legs; neutralBA %.9f; flat bendaxis u=%.9f; provisional Ri%g K%g. Measure springback/effectiveK at actual grain/tool/finish.'%(BA,L/2,R,K))
s=Part.makeBox(80,40,1)
for x,r in [(15,2.5),(35,1.7),(60,6.05)]:s=s.cut(Part.makeCylinder(r,3,V(x,20,-1)))
supplemental('QC04-rivnut-power',s,out+'/Process-coupons','mild steel','RRE03-1 Ø5 pilot, side clearanceØ3.4, PV0F24011Ø12.1. Validate setter nose/bulb, spin/torque, finish and head gap. Test power on1mmaluminium fascia separately.')
# Actual low-angle joggle coupons, not only90degree calibration.
for pid,t,R,K,offset,H in [('QC05-side-joggle',1.5,2.25,.40,6,120),('QC06-wrap-joggle',1,1,.42,4,100)]:
 angle=math.atan(offset/12);midR=R+t/2;setback=midR*math.tan(angle/2);BA=angle*(R+K*t)
 z1=40-t/2*(math.sqrt(1+(offset/12)**2)-1)/(offset/12)
 first=z1-setback;diagonal=math.hypot(offset,12)-2*setback;L=H-12+math.hypot(offset,12)-4*setback+2*BA
 supplemental(pid,Part.makeBox(40,L,t),out+'/Process-coupons','5052-H32 aluminium' if t==1.5 else 'mild steel','Joggle coupon virtualZ40..52,offset%g; opposed angles%gdeg; Ri%g K%g; flat bendaxes v=%.9f /%.9f frombottom, along40width. Measure offset, springback and developedheight after actual tooling/finish.'%(offset,math.degrees(angle),R,K,first+BA/2,first+BA+diagonal+BA/2))
d.recompute();d.saveAs(work+'/Sheet Metal PC Case Flat Patterns.FCStd')
# Ancillary cut-only items are represented in the native reference-hardware group.
inner=Part.makeBox(42,122,1,V(79,275,0)).fuse(Part.makeCylinder(21,1,V(100,275,0))).fuse(Part.makeCylinder(21,1,V(100,397,0))).removeSplitter()
gasket=blank.common(Part.makeBox(100,200,.5,V(50,240,0))).cut(inner).removeSplitter()
supplemental('GSK01-fascia-gasket',gasket,out+'/Ancillary-cuts','closed-cell elastomer','Quantity1;0.5mm nominal compression gasket, outer46x168/inner42x164 concentric capsule; captured, not structural adhesive. Match actual finish/compression.')
shim=Part.makeCylinder(4,.2).cut(Part.makeCylinder(1.7,.2))
supplemental('SH01-side-head-shim',shim,out+'/Ancillary-cuts','conductive compatible shim stock','Quantity10;Ø8xØ3.4x0.2 nominal; cut or buy equivalent. Stack closes0.2gap above RRE03-1 head. Fit finished stack without moving side outer planes; corrosion/contact treatment gate.')
extras[-1]['quantity']=10
d.recompute();d.saveAs(work+'/Sheet Metal PC Case Flat Patterns.FCStd')
# Read BACK actual serialized DXFs, reconstruct loops and areas; reject duplicates.
def readback(path,expected):
 raw=open(path).read().splitlines();pairs=[(int(raw[i]),raw[i+1]) for i in range(0,len(raw),2)];ents=[];active=False;g=None
 for code,val in pairs:
  if code==2 and val=='ENTITIES':active=True;continue
  if not active:continue
  if code==0:
   if g:ents.append(g)
   g=None
   if val=='ENDSEC':break
   assert val in ['LINE','ARC','CIRCLE'],(path,'unexpected',val);g={'type':val}
  elif g is not None:g[code]=val
 edges=[];keys=[];endpoints=[]
 def point(x,y):return V(float(x),float(y),0)
 def ap(c,r,a):a=math.radians(a);return c+V(r*math.cos(a),r*math.sin(a),0)
 for g in ents:
  typ=g['type'];assert g.get(8)=='CUT'
  if typ=='LINE':
   p=point(g[10],g[20]);q=point(g[11],g[21]);edges.append(Part.makeLine(p,q));keys.append(('L',tuple(sorted([(round(p.x,6),round(p.y,6)),(round(q.x,6),round(q.y,6))]))))
  else:
   c=point(g[10],g[20]);r=float(g[40]);assert r>0
   if typ=='CIRCLE':edges.append(Part.makeCircle(r,c));keys.append(('C',round(c.x,6),round(c.y,6),round(r,6)));continue
   a=float(g[50]);b=float(g[51]);p=ap(c,r,a);q=ap(c,r,b);m=ap(c,r,a+((b-a)%360)/2);edges.append(Part.Arc(p,m,q).toShape());keys.append(('A',round(c.x,6),round(c.y,6),round(r,6),round(a,6),round(b,6)))
  endpoints +=[(round(p.x,5),round(p.y,5)),(round(q.x,5),round(q.y,5))]
 assert len(keys)==len(set(keys)),(path,'duplicate cut')
 assert all(n==2 for n in collections.Counter(endpoints).values()),(path,'open/branch')
 wires=[Part.Wire(chain) for chain in Part.sortEdges(edges)];assert all(w.isClosed() for w in wires),(path,'open loops')
 areas=sorted([Part.Face(w).Area for w in wires],reverse=True);area=areas[0]-sum(areas[1:]);error=abs(area-expected)
 assert error<1e-4,(path,error)
 return dict(serialized_entities=len(ents),serialized_closed_loops=len(wires),serialized_area_mm2=area,serialized_area_error_mm2=error,duplicate_entities=0,open_nodes=0)
import glob
for r in results:
 path=next(p for p in glob.glob(out+'/**/*.dxf',recursive=True) if os.path.basename(p)==r['part']+'.dxf');r.update(readback(path,r['area_mm2']))
json.dump(results,open(root+'/dxf-validation.json','w'),indent=2);json.dump(allgeom,open(root+'/drawing-geometry.json','w'));json.dump(extras,open(root+'/supplemental-blanks.json','w'),indent=2)
with open(root+'/flat-hole-schedule.csv','w') as f:
 w=csv.writer(f);w.writerow(['part','circle','flat_X_from_bbox_mm','flat_Y_from_bbox_mm','diameter_mm','source'])
 for pid,geo in allgeom.items():
  n=0
  for e in geo['entities']:
   if e['type']=='CIRCLE':n+=1;w.writerow([pid,n,*e['c'],2*e['r'],'Exact analytic flat boundary; see panels.json mapping'])
print('DXF serialized readback PASS',len(results),'files',sum(r['serialized_closed_loops'] for r in results),'closedloops; maximumareaerror',max(r['serialized_area_error_mm2'] for r in results))
