# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Consolidated fabrication-detail operations on the approved native baseline.
Run with python3 detail.py. Does NOT invoke any historical patch script.
Bend model: exact circular constant-gauge mid-surface, analytical neutral development.
"""
import sys,os,shutil,math,json,gc,csv
exe=shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
if exe:sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))),'lib'))
import FreeCAD as A, Part
V=A.Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));WORK=ROOT+'/CAD';os.makedirs(WORK,exist_ok=True)
A.ParamGet('User parameter:BaseApp/Preferences/Document').SetBool('CreateBackupFiles',False)
d=A.openDocument(os.path.join(ROOT,'Source','Approved-design.FCStd'))
flatdoc=A.newDocument('DevelopedBlanks'); panels=[]; flats={}; groups={}; fastening=[]
colors={'sand':(.77,.71,.60),'charcoal':(.12,.13,.14),'steel':(.52,.55,.58),'board':(.05,.20,.16),'hardware':(.12,.14,.16),'blue':(.2,.48,.65)}
def box(x,y,z,dx,dy,dz): return Part.makeBox(dx,dy,dz,V(x,y,z))
def cyl(r,h,p,axis=(0,0,1)):return Part.makeCylinder(r,h,V(*p),V(*axis))
def fuse(ss):
 s=ss[0]
 for q in ss[1:]:s=s.fuse(q)
 return s.removeSplitter()
def cut(s,cs):return s.cut(Part.makeCompound(cs)).removeSplitter() if cs else s

def orient(s,origin,u,v):
 n=V(*u).cross(V(*v));m=A.Matrix();m.A11,m.A21,m.A31=u;m.A12,m.A22,m.A32=v;m.A13,m.A23,m.A33=n;m.A14,m.A24,m.A34=origin
 q=s.copy();q.transformShape(m,True);return q

def affine(s,rows,offset):
 m=A.Matrix()
 for i in range(3):
  for j in range(3):setattr(m,'A%d%d'%(i+1,j+1),rows[i][j])
  setattr(m,'A%d4'%(i+1),offset[i])
 q=s.copy();q.transformShape(m,True);return q

def poly(points,t=1):return Part.Face(Part.makePolygon([V(x,y,0) for x,y in points]+[V(*points[0],0)])).extrude(V(0,0,t))
def cap(x,y,w,h,t=1):
 r=min(w,h)/2
 if h>=w:return fuse([box(x,y+r,0,w,h-2*r,t),cyl(r,t,(x+r,y+r,0)),cyl(r,t,(x+r,y+h-r,0))])
 return fuse([box(x+r,y,0,w-2*r,h,t),cyl(r,t,(x+r,y+r,0)),cyl(r,t,(x+w-r,y+r,0))])
def flatcut(s,x,y,r):return s.cut(cyl(r,20,(x,y,-10))).removeSplitter()
def obj(prefix):return next(o for o in d.Objects if o.Label.startswith(prefix))
def group(name):
 if name not in groups:
  g=d.addObject('App::Part',name);g.Label=name;groups[name]=g
 return groups[name]
def add(name,s,mat='charcoal',grp='Fabricated',existing=None):
 assert s.isValid() and len(s.Solids)>0,(name,'INVALID',len(s.Solids))
 o=existing or d.addObject('PartDesign::Feature','Detail')
 # old shapes can carry their own placement. Assignment in world coordinates resets it.
 o.Placement=A.Placement();o.Shape=s;o.Label=name
 if 'DisplayColor' not in o.PropertiesList:o.addProperty('App::PropertyColor','DisplayColor','Appearance')
 o.DisplayColor=colors[mat];group(grp).addObject(o)
 return o

def prop(o,key,value):
 if key not in o.PropertiesList:o.addProperty('App::PropertyString',key,'Fabrication')
 setattr(o,key,str(value))

def record(pid,o,f,t,material,bends=[],qty=1,axes='',notes=''):
 assert f.isValid() and len(f.Solids)==1,(pid,'bad flat',len(f.Solids))
 assert o.Shape.isValid() and len(o.Shape.Solids)==1,(pid,'bad formed')
 flats[pid]=f
 fo=flatdoc.addObject('PartDesign::Feature',pid);fo.Label=pid;fo.Shape=f
 bb=f.BoundBox
 panels.append(dict(id=pid,label=o.Label,object=o.Name,quantity=qty,material=material,thickness_mm=t,flat_bounds=[bb.XMin,bb.YMin,bb.XMax,bb.YMax],flat_size_mm=[bb.XLength,bb.YLength],bends=bends,local_axes=axes,notes=notes,flat_source='CAD/Sheet Metal PC Case Flat Patterns.FCStd:'+pid,formed_source='CAD/Sheet Metal PC Case.FCStd:'+o.Name))
 for k,v in [('PartID',pid),('Material',material),('Gauge',t),('Development',notes),('BendSchedule',json.dumps(bends))]:prop(o,k,v)
 print('PART',pid,'formed',o.Shape.Volume,'flat',f.Volume,flush=True)

class Strip:
 """2D mid-surface polyline with circular tangent bends. u is bend axis;
 a,b cross-section coordinates. K factor acts from the INSIDE of each bend.
 Origin/axes provided to solid() map local cross-section XY to assembly.
 """
 def __init__(self,pts,t=1,R=1,K=.42):
  self.pts=pts;self.t=t;self.R=R;self.K=K;self.prims=[];self.bends=[]
  r=R+t/2; p=[V(x,y,0) for x,y in pts]; nodes={}
  for i in range(1,len(p)-1):
   v=(p[i]-p[i-1]);v.normalize();w=p[i+1]-p[i];w.normalize();ang=math.atan2(v.cross(w).z,v.dot(w));sign=1 if ang>0 else -1;setback=r*math.tan(abs(ang)/2)
   a=p[i]-v*setback;b=p[i]+w*setback;c=a+V(-v.y,v.x,0)*r*sign
   nodes[i]=(a,b,c,ang)
  s=0;self.segments=[]
  for i in range(len(p)-1):
   a=nodes[i][1] if i in nodes else p[i];b=nodes[i+1][0] if i+1 in nodes else p[i+1];L=(b-a).Length;v=b-a;v.normalize()
   self.prims.append(('line',a,b,v,s,L));self.segments.append(dict(a=[a.x,a.y],b=[b.x,b.y],start=s,length=L,tangent=[v.x,v.y]))
   s+=L
   if i+1 in nodes:
    a,b,c,ang=nodes[i+1];BA=abs(ang)*(R+K*t)
    self.prims.append(('arc',a,b,c,s,BA,ang));self.bends.append(dict(sequence=len(self.bends)+1,angle_deg=math.degrees(ang),inside_radius_mm=R,K=K,BA_mm=BA,tangent_flat_s=s,bend_axis_flat_s=s+BA/2,flat_end_s=s+BA,tangent_setback_mid_mm=r*math.tan(abs(ang)/2)))
    s+=BA
  self.L=s
 def sec(self):
  pieces=[];t=self.t
  for q in self.prims:
   typ,a,b,c=q[:4]
   if typ=='line':
    n=V(-c.y,c.x,0)*t/2;points=[a+n,b+n,b-n,a-n];pieces.append(Part.Face(Part.makePolygon(points+[points[0]])))
   else:
    ang=q[6];r=self.R+t/2;va=a-c;vb=b-c
    def arc(rad,reverse=False):
     p=c+va*(rad/r);e=c+vb*(rad/r);mv=V(va);mv=A.Rotation(V(0,0,1),math.degrees(ang)/2).multVec(mv);m=c+mv*(rad/r)
     return Part.Arc(e,m,p).toShape() if reverse else Part.Arc(p,m,e).toShape()
    r1=r-t/2;r2=r+t/2
    pieces.append(Part.Face(Part.Wire([arc(r1),Part.makeLine(c+vb*r1/r,c+vb*r2/r),arc(r2,True),Part.makeLine(c+va*r2/r,c+va*r1/r)])))
  return pieces
 def solid(self,width,origin,u,v):
  return fuse([orient(f.extrude(V(0,0,width)),origin,u,v) for f in self.sec()])
 def s_at(self,a,b):
  p=V(a,b,0);best=None
  for q in self.prims:
   if q[0]!='line':continue
   _,start,end,v,s,L=q;f=(p-start).dot(v);distance=(p-(start+v*f)).Length
   if f>=-1e-5 and f<=L+1e-5 and (best is None or distance<best[0]):best=(distance,s+f)
  assert best,(a,b,'point not on straight')
  return best[1]
 def schedule(self,axis):return [dict(b,axis=axis,cross_section_midline_virtual_points=self.pts,straight_segments=self.segments,neutral_total_length_mm=self.L,outside_setback_mm=(self.R+self.t)*math.tan(abs(math.radians(b['angle_deg']))/2)) for b in self.bends]

# Preserve native objects as source of cuts and unchanged purchased reference envelopes.
oldside=obj('S01').Shape.copy();oldwrap=obj('W01').Shape.copy();oldrear=obj('R01').Shape.copy();oldtray=obj('M01').Shape.copy();oldrail=obj('M02').Shape.copy()
# Side midline intersection of exact offset of original virtual outer planes.
t=1.5;z1=(223-.75*math.sqrt(1.25)-150.25)/.5;z2=(223-.75*math.sqrt(1.25)-144.25)/.5
side=Strip([(150.25,0),(150.25,z1),(144.25,z2),(144.25,520)],1.5,2.25,.40)
s=side.solid(410,(0,-205,0),(1,0,0),(0,0,1)) # normal of X,Z = -Y: fix extrusion direction below
# Cross-section X,Z extrudes -Y. start Y205 to end -205.
s=side.solid(410,(0,205,0),(1,0,0),(0,0,1))
lo=side.segments[0]['b'][1];hi=side.segments[-1]['a'][1];shi=side.segments[-1]['start']
low=oldside.common(box(140,-210,-1,20,420,lo+1));high=oldside.common(box(140,-210,hi,20,420,521-hi))
mid=s.common(box(140,-210,lo,20,420,hi-lo));s=fuse([low,mid,high])
flo=affine(low,[(0,1,0),(0,0,1),(1,0,0)],[0,0,-149.5]);fhi=affine(high,[(0,1,0),(0,0,1),(1,0,0)],[0,shi-hi,-143.5]);sf=fuse([flo,box(-205,lo,0,410,shi-lo,1.5),fhi])
right=add('S01 Sand sled right / radiused joggle',s,'sand','Right',obj('S01'));left=add('S02 Sand sled left / mirrored fold hand',s.mirror(V(0,0,0),V(1,0,0)),'sand','Left',obj('S02'))
record('S01-S02',right,sf,1.5,'5052-H32 aluminium',side.schedule('global Y / flat u'),2,'u=global Y; v=developed upward from Z0','Same cut blank, opposite fold hands. Native outer outlines, handle and 546 bores retained; upper flat coordinates offset by %.9f mm. Ri2.25 K.40 provisional.'%(shi-hi))
prop(left,'PartID','S01-S02');prop(left,'Gauge',1.5)
# Wrap: exact rounded floor/front/roof with original external planes.
z1w=3*(-202.5-(-251+.5*math.sqrt(1+1/9)));z2w=3*(-198.5-(-251+.5*math.sqrt(1+1/9)))
wrap=Strip([(203,25.5),(-202.5,25.5),(-202.5,z1w),(-198.5,z2w),(-198.5,457.5),(203,457.5)],1,1,.42)
# Width transitions are developed on the straight inclined web only, not projected across a curved bend.
# First joggle bend retains298width; second286. The diagonal is an exact trapezoid
# in its own tangent/normal coordinates, with the same cut edge in the flat.
sections=wrap.sec();pieces=[];diag=wrap.prims[4];_,da,db,dv,ds,dl=diag
for index,face in enumerate(sections):
 if index==4:
  sh=poly([(-149,0),(149,0),(143,dl),(-143,dl)],1)
  sh=orient(sh,(0,da.x+.5*dv.y,da.y-.5*dv.x),(1,0,0),(0,dv.x,dv.y))
 else:
  width=298 if index<4 else 286
  sh=orient(face.extrude(V(0,0,width)),(-width/2,0,0),(0,1,0),(0,0,1))
 pieces.append(sh)
ws=fuse(pieces)
wf=poly([(-149,0),(149,0),(149,ds),(143,ds+dl),(143,wrap.L),(-143,wrap.L),(-143,ds+dl),(-149,ds)],1)
# Source all existing floor bores and front capsule directly from approved model plane faces.
def planar_face(s,axis,value):
 fs=[f for f in s.Faces if getattr(f.BoundBox,axis+'Length')<1e-6 and abs(getattr(f.BoundBox,axis+'Min')-value)<1e-5]
 return max(fs,key=lambda f:f.Area)
def inner_cut_faces(face):return [Part.Face(w) for w in face.Wires if not w.isSame(face.OuterWire)]
def project_cut_faces(faces,rows,offs,t=1):
 out=[]
 for f in faces:
  q=affine(f,rows,offs);q.translate(V(0,0,-q.BoundBox.ZMin-1));out.append(q.extrude(V(0,0,t+2)))
 return out
floorface=planar_face(oldwrap,'Z',25);floorholes=inner_cut_faces(floorface)
ws=cut(ws,[f.extrude(V(0,0,3)) for f in floorholes])
# first strip runs Y203 toward front: s=203-Y
wf=cut(wf,project_cut_faces(floorholes,[(1,0,0),(0,-1,0),(0,0,-1)],[0,203,25]))
frontface=planar_face(oldwrap,'Y',-199);frontcuts=inner_cut_faces(frontface)
ws=cut(ws,[f.extrude(V(0,3,0)) for f in frontcuts])
frontoff=wrap.s_at(-198.5,300)-300
wf=cut(wf,project_cut_faces(frontcuts,[(1,0,0),(0,0,1),(0,-1,0)],[0,frontoff,-199]))
# Integral side ears, DOWN under roof and DOWN below floor. .7 mm gap = .5 insert head + .2 finish allowance.
tab_schedule=[]
for sign in [-1,1]:
 for yy in [-165,0,165]:
  for upper in [True,False]:
   if not upper and yy==0:continue
   outer=142.8 if upper else 148.8;z=457.5 if upper else 25.5;end=438 if upper else 4;mid=outer-.5
   st=Strip([(mid-4,z),(mid,z),(mid,end)],1,1,.42)
   ts=st.solid(16,(0,yy+8,0),(1,0,0),(0,0,1))
   # Base panel trimmed to horizontal tangent (mid-1.5); keep full straight below circular bend.
   tang=mid-1.5
   if upper:
    region=box(tang,yy-8,456.9,20,16,2)
   else:region=box(tang,yy-8,24.9,20,16,2)
   if sign<0:region=region.mirror(V(0,0,0),V(1,0,0));ts=ts.mirror(V(0,0,0),V(1,0,0))
   ws=ws.cut(region).fuse(ts).removeSplitter()
   zz=448 if upper else 11
   ws=ws.cut(cyl(2.5,12,(sign*(outer-6) if sign>0 else -outer-6,yy,zz),(1,0,0))).removeSplitter()
   # Develop ear outward from roof/floor straight tangent; neutral length after tangent.
   sa=wrap.s_at(yy,z);startx=tang;length=st.L-st.segments[0]['length'];flatx=startx+length
   region=box(startx,sa-8,-1,30,16,3);ear=box(startx,sa-8,0,length,16,1)
   if sign<0:region=region.mirror(V(0,0,0),V(1,0,0));ear=ear.mirror(V(0,0,0),V(1,0,0))
   wf=wf.cut(region).fuse(ear).removeSplitter()
   holex=sign*(startx+st.s_at(mid,zz)-st.segments[0]['length']);wf=flatcut(wf,holex,sa,2.5)
   tab_schedule.append(dict(sequence=1,axis='flat v; ear at Y%s %s'%(yy,'roof' if upper else 'floor'),flat_axis_u=sign*(startx+st.bends[0]['BA_mm']/2),flat_axis_v_range=[sa-8,sa+8],angle_deg=-90*sign,inside_radius_mm=1,K=.42,BA_mm=st.bends[0]['BA_mm'],fold='DOWN',pilot_flat=[holex,sa],pilot_assembled=[sign*(outer-.5),yy,zz]))
body=add('W01 Single charcoal wrap / four main bends and ten downward ears',ws,'charcoal','Wrap',obj('W01'))
record('W01',body,wf,1,'mild steel',tab_schedule+wrap.schedule('global X / flat u'),axes='u=global X; v follows floor rear to front, then upward, then roof toward rear',notes='Ri1 K.42 provisional. Main shell external front planes -203/-199, floor25, roof458 unchanged. Width298 to286 tapers6mm each side only along the straight joggle web; exact tangent-coordinate trapezoid, not a projection. First joggle bend298wide, second286; no open corner-relief gap. Ears preform before main bends; roof ears DOWN. 0.7 mm side gap.')
# Tray bent channel, preserve corrected cut geometry by subtracting native missing volumes.
tr=Strip([(-142.5,26.5),(-117,26.5),(-117,456.5),(-142.5,456.5)],1,1,.42)
trs=tr.solid(276,(0,201,0),(1,0,0),(0,0,1))
# native web extends to Y202; use 277 width, flanges originally 276: unified web/flange ends Y202 with back clearance trimmed later.
trs=tr.solid(277,(0,202,0),(1,0,0),(0,0,1))
fullold=fuse([box(-117.5,-75,27,1,277,429),box(-142.5,-75,26,26,276,1),box(-142.5,-75,456,26,276,1)])
trs=trs.cut(fullold.cut(oldtray)).removeSplitter()
trf=box(-75,0,0,277,tr.L,1)
trayface=planar_face(oldtray,'X',-116.5);traycuts=inner_cut_faces(trayface)
troff=tr.s_at(-117,200)-200
trf=cut(trf,project_cut_faces(traycuts,[(0,1,0),(0,0,1),(1,0,0)],[0,troff,116.5]))
# Lower PCI tip pockets break rear edge; retain by explicit source-derived dimensions.
centers=[139.1656+i*20.32 for i in range(7)]
# Tip pockets are enclosed inner wires already mapped above; never widen them to the edge.
tray=add('M01 Removable motherboard tray / radiused channel',trs,'charcoal','Tray',obj('M01'))
# do not record until attachment and SSD holes added
# Retain back skin, correct handed PSU hole pattern (external rear view reverses global X).
rear=obj('R01');rear.Shape=oldrear
# Original upper/lower-right coordinates reflect rear-view handedness correctly: x=95-localX.
# Preserve cutout and existing four holes: (-49,114),(89,114),(89,50),(-25,40).
rf=affine(oldrear,[(1,0,0),(0,0,1),(0,1,0)],[0,0,-202])
# Remove obsolete I/O artwork/reference sockets. Production face is known-power-only.
for o in list(d.Objects):
 if any(o.Label.startswith(p) for p in ['USB C fascia','USB A fascia','Audio jack illustration','Powerbutton reference','Powerbutton dark','Sledplate sand screw']):d.removeObject(o.Name)
fas=cap(77,252,46,168,1);fas=flatcut(fas,100,400,6.05)
# Concealed extensions of fascia, two mounting ears outside visible opening, no external screw heads.
# No visible or hidden extra mounting holes: gasket and cage capture the full capsule perimeter.
io=add('I01 Replaceable known-power-only fascia; USB/audio BLANK',orient(fas,(0,-196.5,0),(1,0,0),(0,0,1)),'sand','Front',obj('I01'))
record('I01',io,fas,1,'aluminium',axes='u=global X; v=global Z; visible plane Y-197.5',notes='46x168 hidden flange behind unchanged 42x164 visible capsule. Ø12.1 nominal falls in 12.0 +0.2 cutout. All USB/audio positions intentionally blank pending samples.')
prop(io,'IOQualification','PV0F24011 only; USB/audio no functional ports in production blank. Two C need two independent Type-E headers; rear stereo pass-through is NOT HD_AUDIO. Full envelope and setback sample gated.')
# Power exact bezel/actuator, simplified barrel/terminal envelope clearly reference only.
button=fuse([cyl(7,1.5,(100,-199,400),(0,1,0)),cyl(6,18,(100,-197.5,400),(0,1,0))])
add('E-Switch PV0F24011 envelope / Ø14 bezel,18±1mm under-bezel terminal depth',button,'hardware','ReferenceHardware')
# Save intermediate before extensive accessories.
d.recompute();d.saveAs(ROOT+'/CAD/Sheet Metal PC Case.FCStd')
# Hardware are simplified nominal envelopes, not manufacturer CAD or thread helices.
hardware_bom=[]
def hw(name,s,qty=1,spec=''):
 o=add(name,s,'steel','ReferenceHardware');prop(o,'Qualification',spec or 'Nominal reference envelope; obtain supplier drawing. Threads represented by cylindrical mating clearance, not helices.');hardware_bom.append(dict(name=name,quantity=qty,spec=spec));return o

def axis_shape(s,p,n):
 q=s.copy();q.Placement=A.Placement(V(*p),A.Rotation(V(0,0,1),V(*n)));return q

def screw(name,p,n,L=8,dia=3,washer=False):
 # p is under-head plane, n points into the joint. Head is outside, -n.
 hr=2.8 if dia==3 else 3.5;hh=2.4 if dia==3 else 3.0
 sh=fuse([cyl(hr,hh,(0,0,-hh)),cyl(dia/2,L,(0,0,0))]);sh=sh.cut(box(-.5,-hr,-hh,1,2*hr,.7)).removeSplitter()
 return hw(name,axis_shape(sh,p,n),spec='ISO7045 nominal pan envelope M%d x%g; head Ø%g x%g. Verify purchased head and usable thread.'%(dia,L,2*hr,hh))
def washer(name,p,n,dia=3):
 od=7 if dia==3 else 9;t=.5 if dia==3 else .8
 return hw(name,axis_shape(cyl(od/2,t,(0,0,0)).cut(cyl((dia+.4)/2,t,(0,0,0))),p,n),spec='Plain washer M%d OD%g thickness%g'%(dia,od,t))
def nut(name,p,n,dia=3):
 af=5.5 if dia==3 else 7;h=2.4 if dia==3 else 3.2;r=af/math.sqrt(3)
 s=poly([(r*math.cos(i*math.pi/3),r*math.sin(i*math.pi/3)) for i in range(6)],h);s=s.cut(cyl(dia/2,h,(0,0,0)))
 return hw(name,axis_shape(s,p,n),spec='ISO4032 nominal M%d nut; AF%g H%g. Use prevailing-torque equivalent where accessible.'%(dia,af,h))
def rivnut(name,p,n):
 # p on receiving outer flange, n toward insert backside.
 s=fuse([cyl(3,.5,(0,0,-.5)),cyl(2.45,8.5,(0,0,0))]);s=s.cut(cyl(1.5,10,(0,0,-1)))
 return hw(name,axis_shape(s,p,n),spec='Harrison Silverdale RRE03-1; Ø5 pilot, Ø6x.5 reduced head,1mm grip. Shape is UNSET envelope, installed bulb/mandrel/setting access MUST be coupon-qualified.')
# Side ten standard pan-head fasteners, inserts on wrap, no side-plane change.
for sign in [-1,1]:
 for y in [-165,0,165]:
  for upper in [True,False]:
   if not upper and y==0:continue
   x=145 if upper else 151;z=448 if upper else 11;out=142.8 if upper else 148.8
   sidebolt=screw('Side removable M3x8', (sign*x,y,z),(-sign,0,0));sidebolt.DisplayColor=colors['sand']
   rivnut('Side captive RRE03-1',(sign*out,y,z),(-sign,0,0))
   fastening.append(dict(pair='sled/wrap ear',xyz=[sign*x,y,z],hardware='M3x8 pan + RRE03-1',stack_mm=[1.5,.7,1],engagement_nominal_mm=4.8,access='external screwdriver; set insert before assembly. .5 head within .7 gap; retain thin spacer strips as required after finish.'))
# Actual .2mm conductive shim closes the gap over each .5mm insert head without moving side planes.
for sign in [-1,1]:
 for y in [-165,0,165]:
  for upper in [True,False]:
   if not upper and y==0:continue
   outer=142.8 if upper else 148.8;z=448 if upper else 11
   hw('Side captive conductive shim0.2',axis_shape(cyl(4,.2,(0,0,0)).cut(cyl(1.7,.2,(0,0,0))),(sign*(outer+.5),y,z),(sign,0,0)),spec='Ø8xØ3.4x0.2 conductive shim over reduced-head insert. Mask contact annuli; final thickness after finish must close0.2gap without dimpling. Verify shop stack; do not alter approved side outer planes.')
# Actual compression ring seats fascia against front inner skin.
gasket=cap(77,252,46,168,.5).cut(cap(79,254,42,164,1)).removeSplitter()
hw('Fascia captive perimeter gasket0.5',orient(gasket,(0,-197.5,0),(1,0,0),(0,0,1)),spec='0.5mm closed-cell gasket ring46x168 outer/42x164 inner capsule, no structural adhesive. Cage/pads capture fascia against shell. Compression/finish gate.')
# Proper removable standoffs secured with male stud and nut behind tray; only ATX nine installed.
holes={'A':(0,0),'B':(78.74,0),'C':(124.46,0),'F':(281.94,22.86),'G':(0,154.94),'H':(124.46,154.94),'J':(281.94,154.94),'K':(0,227.33),'L':(124.46,227.33),'M':(281.94,227.33),'R':(58.42,154.94),'S':(78.74,154.94)}
board=obj('ATX PCB');bc=[]
for k,(a,b) in holes.items():
 y=189.7318-b;z=141.51+a;bc.append(cyl(1.9812,3,(-107.5,y,z),(1,0,0)))
 if k in ['B','R','S']:continue
 old=obj('ATX standoff '+k)
 # Blind6mm female bore leaves a connected solid base above the male stud; supplier-qualified usable thread required.
 sh=fuse([cyl(2.75,9.525,(-116.5,y,z),(1,0,0)).cut(cyl(1.5,6,(-112.975,y,z),(1,0,0))),cyl(1.5,5,(-121.5,y,z),(1,0,0))])
 add('ATX 9.525 female / M3x5 male standoff '+k,sh,'steel','ReferenceHardware',old)
 nut('Standoff locknut '+k,(-117.5,y,z),(-1,0,0));screw('PCB M3x6 '+k,(-105.375,y,z),(-1,0,0),6)
board.Shape=board.Shape.cut(Part.makeCompound(bc)).removeSplitter()
# SSD bottom screws from component side, connector body datum at Z300.
obj('2.5 inch SSD').Shape=obj('2.5 inch SSD').Shape.translated(V(0,104.065,0))
for y in [64.065,125.785]:
 for z in [286,209.4]:
  trs=trs.cut(cyl(1.75,4,(-119,y,z),(1,0,0))).removeSplitter();trf=flatcut(trf,y,z+troff,1.75)
  screw('SSD bottom M3x4',(-116.5,y,z),(-1,0,0),4)
prop(obj('2.5 inch SSD'),'ConnectorDatum','Connector-end body plane Z300. Hole rows Z286/209.4 =14/90.6 from connector end; transverse Y64.065/125.785. BodyY60..129.85 relocated104.065mm rearward to clear standoffL and its securing nut. Reserve Z300..335 on cable side for SATA plugs. Selected-drive penetration gate: nominal3mm, NOT universally approved.')
# PSU 8mm supports: Ø8 blind-M3 bosses, fixed from below, support all 140/160/180 cases.
for o in list(d.Objects):
 if o.Label.startswith('PSU support'):d.removeObject(o.Name)
for x in [-45,85]:
 for y in [95,190]:
  sh=cyl(4,8,(x,y,26)).cut(cyl(1.5,6,(x,y,26)))
  hw('PSU 8mm blind-M3 support',sh,spec='Bought or machined Ø8x8 boss, blind M3 underside depth6, flat insulating top film ≤0.2 accounted by selected support height. Never drill PSU.')
  screw('PSU support M3x6',(x,y,25),(0,0,1),6)
for x,z in [(-49,114),(89,114),(89,50),(-25,40)]:
 pso=screw('PSU rear #6-32 x1/4 nominal envelope',(x,203,z),(0,-1,0),6.35,3.5052)
 prop(pso,'Qualification','#6-32 UNC-2A nominal majorØ3.5052,L6.35; conservative head envelopeØ7x3. Actual supplier head/PSU penetration gate. NOT metric.')
 hardware_bom[-1]['spec']='#6-32 UNC-2A x1/4 inch, conservativeØ7x3 pan head envelope; verify PSU permitted5.35 penetration.'
fastening.append(dict(pair='PSU to rear',pattern_global_XZ=[[-49,114],[89,114],[89,50],[-25,40]],source='Intel336521-002 Fig12-1 external AC rear view; global X=95-drawingX, global Z=34+drawingY',hardware='4 #6-32 UNC x1/4 inch nominal; verify PSU permitted penetration: 5.35mm through1mm back. Use shorter if required. No PSU opening/modification.'))
# Back-to-wrap four radiused L clips, through M3 joints accessible from open sides.
for idx,(x,upper) in enumerate([(-100,False),(115,False),(-100,True),(100,True)],1):
 zfloor=456.5 if upper else 26.5;zend=437 if upper else 46
 st=Strip([(182,zfloor),(201.5,zfloor),(201.5,zend)],1,1,.42)
 sh=st.solid(20,(x-10,0,0),(0,1,0),(0,0,1));f=box(-10,0,0,20,st.L,1)
 zhole=445 if upper else 38
 for y,z,axis in [(190,zfloor,(0,0,1)),(201.5,zhole,(0,1,0))]:
  p=(x,y,z-2) if axis[2] else (x,y-2,z)
  sh=sh.cut(cyl(1.7,4,p,axis)).removeSplitter();f=flatcut(f,0,st.s_at(y,z),1.7)
 o=add('C%02d: Rear to %s angle'%(idx,'roof' if upper else 'floor'),sh)
 record('C%02d'%idx,o,f,1,'mild steel',st.schedule('global X / flat u'),axes='u=X-center; v=from Y182 toward rear then along Z',notes='One M3 on each leg, through bolts and accessible nuts. Ri1 K.42.')
 # back hole / through joint
 rear.Shape=rear.Shape.cut(cyl(1.7,4,(x,200,zhole),(0,1,0))).removeSplitter();rf=flatcut(rf,x,zhole,1.7)
 screw('Rear clip M3x8',(x,203,zhole),(0,-1,0));washer('Rear clip washer',(x,201,zhole),(0,-1,0));nut('Rear clip nut',(x,200.5,zhole),(0,-1,0))
 z=458 if upper else 25;n=(0,0,-1) if upper else (0,0,1)
 ws=ws.cut(cyl(1.7,5,(x,190,z-3),(0,0,1))).removeSplitter();wf=flatcut(wf,x,wrap.s_at(190,zfloor),1.7)
 screw('Wrap clip M3x8',(x,190,z),n);washer('Wrap clip washer',(x,190,456 if upper else 27),n);nut('Wrap clip nut',(x,190,455.5 if upper else 27.5),n)
# Tray four direct flange bolts, nuts serviced with left side removed. No tapped 1mm sheet.
for upper in [False,True]:
 for y in [-50,100]:
  x=-132;z=456.5 if upper else 26.5
  trs=trs.cut(cyl(1.7,4,(x,y,z-2))).removeSplitter();trf=flatcut(trf,y,tr.s_at(x,z),1.7)
  ws=ws.cut(cyl(1.7,5,(x,y,z-2.5))).removeSplitter();wf=flatcut(wf,x,wrap.s_at(y,457.5 if upper else 25.5),1.7)
  n=(0,0,-1) if upper else (0,0,1)
  screw('Tray service M3x8',(x,y,458 if upper else 25),n);washer('Tray service washer',(x,y,456 if upper else 27),n);nut('Tray service nut',(x,y,455.5 if upper else 27.5),n)
# Two back/tray service clips away from I/O band, at X-132 Z90/440. Short angle legs.
for idx,z in enumerate([90,440],1):
 st=Strip([(-132,201.5),(-118,201.5),(-118,185)],1,1,.42)
 sh=st.solid(16,(0,0,z-8),(1,0,0),(0,1,0));f=box(-8,0,0,16,st.L,1)
 # vertical leg at X-118 (outer toward tray -117.5), web contact. Rear leg at Y201..202.
 for x,y in [(-126,201.5),(-118,192)]:
  axis=(0,1,0) if y==201.5 else (1,0,0);p=(x,200,z) if y==201.5 else (-120,y,z)
  sh=sh.cut(cyl(1.7,5,p,axis)).removeSplitter();f=flatcut(f,0,st.s_at(x,y),1.7)
 o=add('T%02d: Tray rear service angle'%idx,sh);record('T%02d'%idx,o,f,1,'mild steel',st.schedule('global Z / flat u'),axes='u=Z-center; v cross-section path',notes='M3 through fasteners; remove after unplugging rear I/O before tray extraction.')
 rear.Shape=rear.Shape.cut(cyl(1.7,4,(-126,200,z),(0,1,0))).removeSplitter();rf=flatcut(rf,-126,z,1.7)
 screw('Tray back M3x8',(-126,203,z),(0,-1,0));washer('Tray back washer',(-126,201,z),(0,-1,0));nut('Tray back nut',(-126,200.5,z),(0,-1,0))
 trs=trs.cut(cyl(1.7,5,(-120,192,z),(1,0,0))).removeSplitter();trf=flatcut(trf,192,tr.s_at(-117,z),1.7)
 screw('Tray angle M3x8',(-116.5,192,z),(-1,0,0));washer('Tray angle washer',(-118.5,192,z),(-1,0,0));nut('Tray angle nut',(-119,192,z),(-1,0,0))
# PCI bent 1mm interface: reproduce exact Ri1 outerX2.2323, remove weak tapped holes.
# Existing rail is already genuinely radiused; preserve its radii and cutouts, plug obsolete taps then drill corrected seven.
rs=oldrail
for i in range(7):rs=rs.fuse(cyl(1.25,1,(1.2323,206.1148,147.4841+i*20.32),(1,0,0)))
rs=rs.removeSplitter()
retcenters=[147.4841+i*20.32 for i in range(7)]
rail_holes=[(206.1148,z) for z in retcenters]+[(214,z) for z in [130,272]]
for y,z in rail_holes:rs=rs.cut(cyl(1.7,4,(0,y,z),(1,0,0))).removeSplitter()
# Flatten web and two terminal return ears analytically, using existing actual tangent atY201 / X3.2323.
BA=math.pi/2*1.42
webface=planar_face(rs,'X',2.2323)
railflat=affine(webface,[(0,0,1),(0,1,0),(1,0,0)],[0,-201,-2.2323]).extrude(V(0,0,1))
for face in rs.Faces:
 if face.BoundBox.YLength<1e-6 and abs(face.BoundBox.YMin-199)<1e-5 and face.Area>100:
  ear=affine(face,[(0,0,1),(-1,0,0),(0,1,0)],[0,3.2323-BA,-199]).extrude(V(0,0,1));railflat=railflat.fuse(ear)
for za,zb in [(125,134),(268,276)]:railflat=railflat.fuse(box(za,-BA,0,zb-za,BA,1))
railflat=railflat.removeSplitter()
rail=add('M02 1mm PCI formed interface with clearance holes',rs,'charcoal','Rear',obj('M02'))
record('M02',rail,railflat,1,'mild steel',[dict(sequence=1,angle_deg=90,inside_radius_mm=1,K=.42,BA_mm=BA,axis='global Z; flat u',bend_axis_flat_v=-BA/2,axis_ranges=[[125,134],[268,276]])],axes='u=global Z; v=Y-201 on rail web; negative v develops terminal ears',notes='Outer retentionX2.2323 unchanged. Seven source retention centers Z147.4841+n20.32,Y206.1148; aperture centres remain139.1656+n20.32. EndfixingsY214,Z130/272; backed by separate3mm tapped nutstrip. Legacy interface gauge REQUIRED: Protocase vs ATX setback differs0.4572mm.')
ns=box(-1.7677,203,125,3,14,151);nf=box(203,125,0,14,151,3)
for y,z in rail_holes:ns=ns.cut(cyl(1.25,5,(-2.7677,y,z),(1,0,0))).removeSplitter();nf=flatcut(nf,y,z,1.25)
nutstrip=add('M03 3mm steel M3 tapped PCI nutstrip',ns,'steel','Rear');record('M03',nutstrip,nf,3,'mild steel',axes='u=global Y; v=global Z',notes='9 Ø2.5 tap drills; tap M3x0.5 through3mm AFTER cut, deburr. X-1.7677..1.2323,Y203..217; does NOT cross rear wall. Seven retention plus2 end attachments.')
for z in [130,272]:screw('PCI nutstrip end M3x5',(2.2323,214,z),(-1,0,0),5)
for z in retcenters:
 washer('PCI bracket-notch M3 washer',(3.2323,206.1148,z),(1,0,0));screw('PCI retention M3x6',(3.7323,206.1148,z),(-1,0,0),6)
for z in [130,272]:
 # rail ear Y199..200; 2mm spacer to rearinner202
 hw('PCI rear 2mm spacer',cyl(3.5,2,(16.5,200,z),(0,1,0)).cut(cyl(1.7,2,(16.5,200,z),(0,1,0))))
 screw('PCI rail to rear M3x10',(16.5,203,z),(0,-1,0),10);washer('PCI rear washer',(16.5,199,z),(0,-1,0));nut('PCI rear nut',(16.5,198.5,z),(0,-1,0))
hardware_bom.append(dict(name='Purchased standard full-height PCI slot blank covers',quantity=7,spec='Standard0.8..1.0mm formed cover with locating tip and ordinary screw notch. NOT a120x18 rectangle. Fit actual cover/GPU bracket to legacy interface gauge before committing rear; remove covers occupied by GPU/controller. Not OEM geometry in model.'))
# Adjacent rear clearance slit for ordinaryOD7 washers; source aperture axes unchanged.
rear.Shape=rear.Shape.cut(box(1,201,124,3.2,3,153)).removeSplitter();rf=rf.cut(box(1,124,-1,3.2,153,3)).removeSplitter()
# Optional120 fan bracket: inboard mounting side,2mm+3mm shift for outer screwheads.
fan=obj('Optional side120');fan.Shape=fan.Shape.translated(V(-3.5,0,0));fan.Label='Optional120 fan reference / X115..140'
st=Strip([(99,456.5),(114.5,456.5),(114.5,295)],1,1,.42)
fs=st.solid(120,(0,170,0),(1,0,0),(0,0,1));ff=box(50,0,0,120,st.L,1)
fs=fs.cut(box(112,64,294,5,92,137)).removeSplitter();start=st.s_at(114.5,431);ff=ff.cut(box(64,start,-1,92,st.L-start+1,3)).removeSplitter()
for y in [57.5,162.5]:
 for z in [302.5,407.5]:
  fs=fs.cut(cyl(2.25,5,(112,y,z),(1,0,0))).removeSplitter();ff=flatcut(ff,y,st.s_at(114.5,z),2.25)
  screw('Optional fan M4x35',(140,y,z),(-1,0,0),35,4);washer('Optional fan M4 washer',(114,y,z),(-1,0,0),4);nut('Optional fan M4 nut',(113.2,y,z),(-1,0,0),4)
 for x,z in [(105,456.5)]:
  fs=fs.cut(cyl(1.7,4,(x,y,z-2))).removeSplitter();ff=flatcut(ff,y,st.s_at(x,z),1.7)
  ws=ws.cut(cyl(1.7,4,(x,y,456))).removeSplitter();wf=flatcut(wf,x,wrap.s_at(y,457.5),1.7)
  screw('Optional bracket roof M3x8',(x,y,458),(0,0,-1));washer('Optional bracket washer',(x,y,456),(0,0,-1));nut('Optional bracket nut',(x,y,455.5),(0,0,-1))
fo=add('F01 Removable120 side fan bridge',fs,'charcoal','Optional');record('F01',fo,ff,1,'mild steel',st.schedule('global Y / flat u'),axes='u=Y; v roof inward edge to downward legs',notes='Two roof bolts; four105x105 M4 fan fixings. Fan X115..140,3.5mm inboard shift. Cooler tip to frame42.375mm, to bracket41.375mm. Fan frame to rear fan7mm. M4 head projects to143 nominal:0.5mm to sideinside143.5 before finish; verify head and coating.')
# Carrier cage: one folded frame, two ordinary through-bolts. Fascia clamped with compression pads/gasket.
st=Strip([(62,-174.5),(62,-195),(138,-195),(138,-174.5)],1,1,.42)
cs=st.solid(180,(0,0,246),(1,0,0),(0,1,0));cf=box(246,0,0,180,st.L,1)
cs=cs.cut(box(81,-198,260,38,6,152)).removeSplitter();sleft=st.s_at(81,-195);sright=st.s_at(119,-195);cf=cf.cut(box(260,sleft,-1,152,sright-sleft,3)).removeSplitter()
for x in [68,132]:
 cs=cs.cut(cyl(1.7,5,(x,-198,336),(0,1,0))).removeSplitter();cf=flatcut(cf,336,st.s_at(x,-195),1.7)
 ws=ws.cut(cyl(1.7,5,(x,-201,336),(0,1,0))).removeSplitter();wf=flatcut(wf,x,wrap.s_at(-198.5,336),1.7)
 screw('I/O shell M3x10 pan screw',(x,-199,336),(0,1,0),10).DisplayColor=(.12,.13,.14)
 hw('I/O carrier 2.5mm spacer',cyl(3.5,2.5,(x,-198,336),(0,1,0)).cut(cyl(1.7,2.5,(x,-198,336),(0,1,0))))
 washer('I/O carrier washer',(x,-194.5,336),(0,1,0));nut('I/O carrier removable M3 nut',(x,-194,336),(0,1,0))
for x in [62,138]:
 for z in [300,380]:
  for y in [-181,-177]:
   cs=cs.cut(cyl(1.5,4,(x-2,y,z),(1,0,0))).removeSplitter();cf=flatcut(cf,z,st.s_at(x,y),1.5)
co=add('I02 Concealed folded carrier / sample-gated module rails',cs,'charcoal','Front');record('I02',co,cf,1,'mild steel',st.schedule('global Z / flat u'),axes='u=global Z; v from left rear return around front to right rear return',notes='Front carrier planeY-195.5..-194.5. Two ordinary M3x10 pan screws atX68/132 Z336; NO WELDING;2.5 spacers. Clamp fascia using0.5 front gasket and1mm back pads (not adhesive structural retention). Remove2nuts from right open side, pull cage then face inward; power supplied nut accessible. Future USB modules mount to sample-drilled removable crossbars, not guessed footprints. Returns carry tie holes. Nominal module zone endsY-158; measured sample/plug-setback gate.')
# Shared cage clamps fascia perimeter.
# Back pads are retained mechanically by cage compression.
for x in [78,120]:
 for z in [300,372]:
  hw('Fascia captive compression pad1mm',box(x,-196.5,z,2,1,12),spec='1mm elastomer compression pad captive between fascia and carrier. Contact gate; not a glued structural joint.')
# protected rear audio patch exit and a separate bonding point clear of fans.
rear.Shape=rear.Shape.cut(cyl(6,4,(130,201,280),(0,1,0))).removeSplitter();rf=flatcut(rf,130,280,6)
hw('Rear audio grommet nominal12mm panel hole',fuse([cyl(7,.5,(130,201.5,280),(0,1,0)),cyl(6,1,(130,202,280),(0,1,0)),cyl(7,.5,(130,203,280),(0,1,0))]).cut(cyl(4.5,2,(130,201.5,280),(0,1,0))),spec='Select split grommet fitting Ø12 hole in1mm panel, nominal clear aperture9mm. Check actual audio plug and shielded extension. Protect cable, tie strain relief inside; no seam pinching.')
for x,z in [(130,250)]:
 rear.Shape=rear.Shape.cut(cyl(2.25,4,(x,201,z),(0,1,0))).removeSplitter();rf=flatcut(rf,x,z,2.25)
 screw('Dedicated chassis bonding M4x10',(x,203,z),(0,-1,0),10,4);washer('Bond lug washer',(x,202,z),(0,-1,0),4);nut('Bond stud M4nut',(x,201.2,z),(0,-1,0),4)
# GPU support, optional but recommended for heavy cards; no fan obstruction/cable-reserve incursion.
st=Strip([(96,27.5),(118,27.5),(118,190)],3,3,.40)
gs=st.solid(24,(0,-88,0),(1,0,0),(0,0,1));gf=box(-112,0,0,24,st.L,3)
for y in [-107,-93]:
 gs=gs.cut(cyl(2.25,6,(101.5,y,25))).removeSplitter();gf=flatcut(gf,y,st.s_at(101.5,27.5),2.25)
 # floorYadjustmentslots, connected round ends: y-20..y+20
 sl=cap(99.25,y-20,4.5,40,3);sl.translate(V(0,0,24));ws=ws.cut(sl).removeSplitter()
 # flat floor mapping reverses Y. Capsule symmetric.
 fsl=cap(99.25,203-(y+20),4.5,40,3);fsl.translate(V(0,0,-1));wf=wf.cut(fsl).removeSplitter()
 screw('GPU post floor M4x10',(101.5,y,25),(0,0,1),10,4);washer('GPU post washer',(101.5,y,29),(0,0,1),4);nut('GPU post floor nut',(101.5,y,29.8),(0,0,1),4)
for y in [-105,-95]:
 slot=cap(y-2.25,125,4.5,56,5);gs=gs.cut(orient(slot,(115.5,0,0),(0,1,0),(0,0,1))).removeSplitter()
 start=st.s_at(118,125);end=st.s_at(118,181);gf=gf.cut(cap(y-2.25,start,4.5,end-start,5).translated(V(0,0,-1))).removeSplitter()
go=add('G01 Optional GPU support post',gs,'charcoal','Optional');record('G01',go,gf,3,'mild steel',st.schedule('global Y / flat u'),axes='u=Y; v from X96 base toward post then upward',notes='3mmsteel Ri3 K.40. Post X116.5..119.5, floorfootX96..119.5 clears bottomfan maxX90 by6mm, PSUmaxX95 by1mm at foot; post21.5mm right of PSU envelope. One continuous54mm floor slot with2bolts for Yadjustment; two vertical slots for ledge. Prototype stiffness/actual GPU contact gate; never load fan shroud blindly.')
st=Strip([(40,191.5),(115,191.5),(115,155)],3,3,.40)
ls=st.solid(20,(0,-90,0),(1,0,0),(0,0,1));lf=box(-110,0,0,20,st.L,3)
for y in [-105,-95]:
 ls=ls.cut(cyl(2.25,6,(111.5,y,170),(1,0,0))).removeSplitter();lf=flatcut(lf,y,st.s_at(115,170),2.25)
 screw('GPU ledge clamp M4x12',(119.5,y,170),(-1,0,0),12,4);washer('GPU ledge washer',(113.5,y,170),(-1,0,0),4);nut('GPU ledge M4nut',(112.7,y,170),(-1,0,0),4)
lo=add('G02 Adjustable GPU ledge',ls,'charcoal','Optional');record('G02',lo,lf,3,'mild steel',st.schedule('global Y / flat u'),axes='u=Y; v fromX40 ledge tip towardpost then down',notes='TopZ193 plus2mm nonconductive pad to GPU undersideZ195; adjust to actual nonfan load-bearing card surface. X40..116.5 below GPU, no entry into35mm cable zone aboveZ195. Remove if unsuitable and fit GPU-maker support.')
hw('GPU contact pad2mm',box(40,-110,193,12,20,2),spec='Nonconductive2mm firm pad, actual card support surface must be identified. No handling/shipping load rating.')
# Bottom/rear140 fans: four long screws each. Reference envelopes have real clearance holes.
for x in [20-62.25,20+62.25]:
 for y in [-124-62.25,-124+62.25]:
  screw('Bottom140 M4x35',(x,y,25),(0,0,1),35,4);washer('Bottom fan M4washer',(x,y,51),(0,0,1),4);nut('Bottom fan M4nut',(x,y,51.8),(0,0,1),4)
for x in [50-62.25,50+62.25]:
 for z in [365-62.25,365+62.25]:
  screw('Rear140 M4x30',(x,203,z),(0,-1,0),30,4);washer('Rear fan M4washer',(x,177,z),(0,-1,0),4);rear_nut=nut('Rear fan M4nut',(x,176.2,z),(0,-1,0),4)
  rear_nut.Qualification='ISO4032 plain M4 nut, AF7, height3.2mm ONLY for rear M4x30 stack. No thick nyloc/prevailing-torque substitution. Use suitable removable low-strength thread locking and verify the actual finished stack; nominal protrusion is zero.';hardware_bom[-1]['spec']='ISO4032 plain M4 nut, AF7, height3.2mm ONLY for rear M4x30 stack. No thick nyloc/prevailing-torque substitution. Use suitable removable low-strength thread locking and verify the actual finished stack; nominal protrusion is zero.'
# Local top-flange edge reliefs avoid the down-folded left wrap ears, keeping side outer planes.
for y in [0,165]:
 trs=trs.cut(box(-143,y-10,455.5,3.2,20,2)).removeSplitter()
 v0=tr.s_at(-139.8,456.5)
 trf=trf.cut(box(y-10,v0,-1,20,tr.L-v0+1,3)).removeSplitter()
# Write final changed sheet shapes and update existing records after late interface cuts.
body.Shape=ws;flats['W01']=wf;flatdoc.getObject('W01').Shape=wf
tray.Shape=trs;record('M01',tray,trf,1,'mild steel',tr.schedule('global Y / flat u'),axes='u=global Y; v follows bottom flange to tray up and across top flange',notes='Corrected12 motherboard positions retained. Plain clearance holes: male standoffs secured by nuts; no1mm tapped structure. Fourflange servicebolts plus2rear clips. SSD61.72x76.6 bottomholes, connectorbodyZ300. Ri1 K.42. Disassemble GPU, rear cables and side before tray extraction; see assembly notes.')
add('R01 Rear hardware interface / fastened to wrap and tray',rear.Shape,'charcoal','Rear',rear);record('R01',rear,rf,1,'mild steel',axes='u=global X; v=global Z',notes='RearinnerY202 preserved;1mmsteel ATXI/O interface. Correct handedPSU holes. Added protectedØ12audio patch exit andM4bondpoint; no PSU modification.')
# Mark untouched envelopes and move into clear group; keep all shaped leaves eligible for STEP validation.
for o in list(d.Objects):
 if not hasattr(o,'Group') and hasattr(o,'Shape') and not o.Shape.isNull() and len(o.Shape.Solids)>0 and o not in sum([g.Group for g in groups.values()],[]):
  print('GROUP',o.Label,o.TypeId,flush=True)
  for parent in list(o.InList):
   if hasattr(parent,'Group'):parent.removeObject(o)
  group('ReferenceHardware').addObject(o)
  prop(o,'Qualification','Approved component envelope, not OEM model. Retail fans are frame/hub compound solids. Actual board/card/cooler/cable fit sample-gated.')
# Remove old empty assembly groups, retain dimension spreadsheet updated status.
for n in ['SheetPanels','Components','ClearanceReserves']:
 if d.getObject(n):d.removeObject(n)
ss=d.getObject('Dimensions');ss.set('B1','UNPROTOTYPED ENGINEERING KIT: COUPON/FIT QUALIFICATION REQUIRED');ss.set('B11','Power-only blank; USB/audio sample-gated');ss.set('B12','Handles UNRATED; empty case only until tested')
for p in panels:
 if p['id']=='W01':
  bb=wf.BoundBox;p['flat_bounds']=[bb.XMin,bb.YMin,bb.XMax,bb.YMax];p['flat_size_mm']=[bb.XLength,bb.YLength]
for panel in panels:
 panel['DXF_origin_mm']=panel['flat_bounds'][:2]
 panel['status']='UNPROTOTYPED; mandatory shop coupon and component fit qualification'
 for bend in panel['bends']:
  bend['suggested_forming_step']=bend['sequence']
  if panel['id']=='W01':bend['suggested_forming_step']=1 if 'flat_axis_u' in bend else {1:4,2:2,3:3,4:5}[bend['sequence']]
  if 'bend_axis_flat_s' in bend:bend['flat_axis_v_mm']=bend['bend_axis_flat_s']
for o in d.Objects:
 if not hasattr(o,'Group') and hasattr(o,'Shape') and len(o.Shape.Solids)>0:prop(o,'License','CERN-OHL-P-2.0; third-party names/data remain their owners; no certification or trademark license')
json.dump(panels,open(ROOT+'/panels.json','w'),indent=2);json.dump(fastening,open(ROOT+'/fastening-pairs.json','w'),indent=2);json.dump(hardware_bom,open(ROOT+'/hardware-bom-detail.json','w'),indent=2)
d.recompute();flatdoc.recompute();d.saveAs(ROOT+'/CAD/Sheet Metal PC Case.FCStd');flatdoc.saveAs(WORK+'/Sheet Metal PC Case Flat Patterns.FCStd')
print('SAVED',len(panels),'panel designs',len([o for o in d.Objects if not hasattr(o,'Group') and hasattr(o,'Shape') and len(o.Shape.Solids)>0]),'shaped objects',flush=True)

# Finish the selected I/O subsystem only after base generation.
from finish_io import finish
finish(ROOT, d, flatdoc)
