# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Idempotent I/O completion. Edits the authoritative native assembly, never rebuilds shell.
Called after detail.py's base generation; also runnable standalone. Vendor drawings are
research evidence only, NOT bundled. Reference envelopes are not OEM CAD.
"""
import os,sys,shutil,json,math
exe=shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
if exe:sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))),'lib'))
import FreeCAD as A,Part
V=A.Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A.ParamGet('User parameter:BaseApp/Preferences/Document').SetBool('CreateBackupFiles',False)
def box(x,y,z,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x,y,z))
def cyl(r,h,x,y,z,axis=(0,1,0)):return Part.makeCylinder(r,h,V(x,y,z),V(*axis))
def union(ss):
 s=ss[0]
 for t in ss[1:]:s=s.fuse(t)
 return s.removeSplitter()
def rounded(x,z,w,h,r,t=1):
 return union([box(x+r,z,0,w-2*r,h,t),box(x,z+r,0,w,h-2*r,t)]+[cyl(r,t,a,b,0,(0,0,1)) for a in [x+r,x+w-r] for b in [z+r,z+h-r]])
def capsule():
 return union([box(77,275,0,46,122,1),cyl(23,1,100,275,0,(0,0,1)),cyl(23,1,100,397,0,(0,0,1))])
def boreflat(s,x,z,r=1.7):return s.cut(cyl(r,3,x,z,-1,(0,0,1))).removeSplitter()
def formed(s,back):
 m=A.Matrix();m.A11=1;m.A22=0;m.A23=-1;m.A32=1;m.A33=0;m.A24=back
 q=s.copy();q.transformShape(m,True);return q

def finish(root=ROOT,doc=None,flatdoc=None):
 global ROOT
 ROOT=root
 d=doc or A.openDocument(ROOT+'/CAD/Sheet Metal PC Case.FCStd');fd=flatdoc or A.openDocument(ROOT+'/CAD/Sheet Metal PC Case Flat Patterns.FCStd')
 panels=json.load(open(ROOT+'/panels.json'));byid={p['id']:p for p in panels}
 # Delete only objects owned by this subsystem. I01/I02 identities and placements survive.
 owned=[o.Name for o in d.Objects if getattr(o,'IOCompletion','')=='owned']
 for name in reversed(owned):
  if d.getObject(name):d.removeObject(name)
 for o in list(fd.Objects):
  if o.Label=='I03':fd.removeObject(o.Name)
 panels=[p for p in panels if p['id']!='I03']
 byid.pop('I03',None)
 groups={}
 def prop(o,k,v):
  if k not in o.PropertiesList:o.addProperty('App::PropertyString',k,'IO engineering')
  setattr(o,k,str(v))
 def add(label,s,color=(.12,.14,.16),group='IO_SelectedHardware',role='Reference allocation; not OEM CAD'):
  assert s.isValid(),label
  if group not in groups:
   g=d.addObject('App::Part',group);g.Label=group;prop(g,'IOCompletion','owned');groups[group]=g
  o=d.addObject('PartDesign::Feature','IO');o.Label=label;o.Shape=s
  o.addProperty('App::PropertyColor','DisplayColor','Appearance');o.DisplayColor=color
  prop(o,'IOCompletion','owned');prop(o,'Qualification',role);groups[group].addObject(o)
  return o
 def setpanel(pid,o,f,notes):
  if pid in byid:p=byid[pid];fo=next(ob for ob in fd.Objects if ob.Label==pid)
  else:
   p=dict(id=pid,quantity=1,material='mild steel',thickness_mm=1,bends=[],local_axes='u=global X; v=global Z',status='UNPROTOTYPED; mandatory shop coupon and component fit qualification');panels.append(p)
   fo=fd.addObject('PartDesign::Feature',pid);fo.Label=pid
  fo.Shape=f;bb=f.BoundBox
  p.update(label=o.Label,object=o.Name,notes=notes,flat_bounds=[bb.XMin,bb.YMin,bb.XMax,bb.YMax],flat_size_mm=[bb.XLength,bb.YLength],DXF_origin_mm=[bb.XMin,bb.YMin],flat_source='CAD/Sheet Metal PC Case Flat Patterns.FCStd:'+pid,formed_source='CAD/Sheet Metal PC Case.FCStd:'+o.Name)
  p['axes']=p['local_axes']
  for k,v in [('PartID',pid),('Material',p['material']),('Gauge',1),('Development',notes),('BendSchedule',json.dumps(p['bends']))]:prop(o,k,v)
  assert f.isValid() and len(f.Solids)==1 and o.Shape.isValid() and len(o.Shape.Solids)==1,pid
  return p
 # Fascia remains the same capsule; access apertures are designer geometry, not OEM cuts.
 f=capsule();f=boreflat(f,100,400,6.05)
 for z in [380,360]:f=f.cut(rounded(93,z-4,14,8,2,3).translated(V(0,0,-1)))
 for z in [337,316]:f=f.cut(rounded(90,z-6,20,12,1,3).translated(V(0,0,-1)))
 f=boreflat(f,100,281,3.05).removeSplitter()
 fascia=d.getObject(byid['I01']['object']);fascia.Shape=formed(f,-196.5);fascia.Label='I01 Full 2C / 2A / stereo audio / power fascia'
 setpanel('I01',fascia,f,'1mm aluminium, FINISHED thickness strictly <1.2mm at audio. Designer access C14x8R2,A20x12R1; not manufacturer cut recommendations. C hood <=12.2x6.4/A <=18x10 prototype access test. Audio supplier Ø6.1, power unchanged Ø12.1. Port centresX100,Z400/380/360/337/316/281. Alternative C1 blanks lowerC; power-only and fullyblank are mutually exclusive alternatives.')
 prop(fascia,'IOQualification','Selected commercial passive extensions + header adapters, NOT certified cable chain; both C orientations/speed and mechanical access require prototype qualification. See IO-ASSEMBLY.md.')
 # Add four holes to existing I02 formed sheet and map onto its exact neutral strip.
 cage=d.getObject(byid['I02']['object']);cf=next(ob.Shape.copy() for ob in fd.Objects if ob.Label=='I02')
 for x in [72,128]:
  for z in [308,386]:
   cage.Shape=cage.Shape.cut(cyl(1.7,4,x,-197,z)).removeSplitter()
   station=byid['I02']['bends'][0]['straight_segments'][1]['start']+x-63.5
   cf=boreflat(cf,z,station)
 cage.Label='I02 Concealed folded carrier / common I03 ladder attachment'
 setpanel('I02',cage,cf,'Existing windowX81..119 Z260..412, returns and shell fixings unchanged. Added4 Ø3.4 holesX72/128,Z308/386 through front sheet for I03. No welding; existing2 M3x10 shell boltsX68/132 Z336. Existingreturn Ø3 tieholesX62/138,Y-181/-177,Z300/380 retained for cushioned lacing. Finish/strain-relief qualification required.')
 plate=box(66,303,0,68,88,1).cut(box(90,389,-1,20,3,3))
 for x in [72,128]:
  for z in [308,386]:plate=boreflat(plate,x,z)
 for z,kind in [(380,'C'),(360,'C'),(337,'A'),(316,'A')]:
  w,h,r,pitch=(14,8,2,20) if kind=='C' else (20,12,1,30)
  plate=plate.cut(rounded(100-w/2,z-h/2,w,h,r,3).translated(V(0,0,-1)))
  for x in [100-pitch/2,100+pitch/2]:plate=boreflat(plate,x,z)
 # Retained I02 shell bolts/washers atX68/132 Z336 need open edge service scallops.
 for x in [68,132]:plate=boreflat(plate,x,336,4.5)
 plate=plate.removeSplitter()
 po=add('I03 Common concealed USB ladder / 1mm steel',formed(plate,-193.5),(.52,.55,.58),'IO_CommonPlate','Manufactured common flat steel plate; four attachment bolts; eight module screws; no visible fascia fasteners')
 setpanel('I03',po,plate,'68x88x1 steel, X66..134 Z303..391 Y-194.5..-193.5. Central20x2 top notch keeps power tool envelope clear.4attachmentØ3.4 atX72/128 Z308/386; C mountingØ3.4 atX90/110 Z380/360; A atX85/115 Z337/316. Two openedgeR4.5 scallops centredX68/132 Z336 clear retained shellbolt/OD7washer/nut; no new shellholes. All holes cut, deburr; no bends. Flange frontsY-193 using0.5mm washers; no tapped1mm sheet.')
 hb=json.load(open(ROOT+'/hardware-bom-detail.json'));hb=[r for r in hb if r.get('scope')!='IOCompletion']
 def bom(name,qty,spec):hb.append(dict(name=name,quantity=qty,spec=spec,scope='IOCompletion'))
 def screw(x,y,z,L,label):
  s=union([cyl(2.85,1.65,x,y-1.65,z),cyl(1.5,L,x,y,z)])
  # Shallow socket indication; head envelope deliberately conservative cylindrical maximum.
  s=s.cut(box(x-.8,y-1.66,z-.8,1.6,.7,1.6)).removeSplitter()
  return add(label,s,(.55,.57,.60),role='ISO7380-1 M3 nominal max headØ5.7 H1.65, cylindrical conservative head envelope, not thread geometry')
 def washer(x,y,z,label):return add(label,cyl(3.5,.5,x,y,z).cut(cyl(1.7,.5,x,y,z)),(.6,.62,.64),role='M3 flat washer OD7 ID3.4 thickness0.5')
 def nut(x,y,z):
  r=5.5/math.sqrt(3);pts=[V(x+r*math.cos(i*math.pi/3),y,z+r*math.sin(i*math.pi/3)) for i in range(6)]
  s=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,2.4,0)).cut(cyl(1.5,2.4,x,y,z))
  return add('IO I03 attachment M3 plain nut',s,(.6,.62,.64),role='M3 plain nut AF5.5 H2.4; nominal bore represents threaded engagement without helices')
 for x in [72,128]:
  for z in [308,386]:screw(x,-195.5,z,6,'IO I03 attachment M3x6 button head');washer(x,-193.5,z,'IO I03 attachment washer');nut(x,-193,z)
 bom('IO I03 attachment M3x6 ISO7380-1',4,'Head maxØ5.7x1.65; two1mm sheets+.5washer+2.4plainnut=4.9;1.1nominal tip. Heads behind wrap innerY-198 by0.85.')
 bom('IO M3 flat washer OD7 ID3.4 x0.5',12,'4 I03 attachments +8 module spacers; thickness controls flangeY-193; verify actual finish stack')
 bom('IO M3 plain nut AF5.5 H2.4',4,'I03 four attachments only; no thick nyloc substitution without stack review')
 bom('IO module M3x4 ISO7380-1',8,'1plate+.5washer ->2.5nominal embedded-nut engagement. Allowed supplier thread depth NOT published: bottoming/engagement receiving check mandatory. Use factory screws/spacers if needed while maintaining flangeY-193. TR00004815-000 commercially listed.')
 module_objects=[]
 for z,kind in [(380,'C'),(360,'C'),(337,'A'),(316,'A')]:
  w,h,pitch,rear=(30,8,20,37.5) if kind=='C' else (38.5,13.7,30,36.5)
  # Outer simplified allocations within published bounds; flange thickness and corner profiles unknown.
  # Whole rectangular body reservation is conservative, NOT a reproduction of unpublished outline.
  depth=27.5 if kind=='C' else 26.5
  s=box(100-w/2,-193,z-h/2,w,depth,h)
  for x in [100-pitch/2,100+pitch/2]:
   s=s.cut(cyl(1.5,depth,x,-193,z));screw(x,-194.5,z,4,'IO USB-'+kind+' Z'+str(z)+' M3x4 button head');washer(x,-193.5,z,'IO USB-'+kind+' flange 0.5mm washer')
  relief_r=4.65 if kind=='C' else 4.65 # A relief diameter unreported: Ø9.3 allocation, not supplier dimension
  s=s.fuse(cyl(relief_r,rear-depth,100,-193+depth,z)).removeSplitter()
  # Reference mouth, deliberately labelled allocation. A receives blue tongue and metal shell.
  nw,nh=(12,6) if kind=='C' else (17.8,9)
  front=-196.2 if kind=='C' else -193
  s=s.cut(box(100-nw/2, -193-.01,z-nh/2,nw,5.01,nh)).removeSplitter()
  body=add('IO Newnex '+('U4S5C01C08-010' if kind=='C' else 'USR2-AA-1M')+' Z'+str(z)+' conservative body allocation',s,role='Published outer limits only. Rectangular body/full width reservation, corners/flange thickness not OEM geometry. '+('C flange30x8,20pitch,37.5rear includingØ9.3relief.' if kind=='C' else 'A family38.5x13.7,30pitch,26.5body/36.5rear; reliefØ9.3 allocation ONLY; retail must match family drawing.'))
  module_objects.append(body.Name)
  metal=box(100-nw/2,front,z-nh/2,nw,5+( -193-front),nh).cut(box(100-nw/2+.4,front-.01,z-nh/2+.4,nw-.8,4.5+(-193-front),nh-.8)).removeSplitter()
  if kind=='C':
   # Racetrack mouth is a VISUAL allocation within12x6, not a claimed OEM profile.
   def race(width,height,depth):
    rr=height/2
    return union([box(100-width/2+rr,z-rr,0,width-height,height,depth),cyl(rr,depth,100-width/2+rr,z,0,(0,0,1)),cyl(rr,depth,100+width/2-rr,z,0,(0,0,1))])
   metal=formed(race(12,6,8.2),-188).cut(formed(race(10.8,4.8,7.72),-188.5)).removeSplitter()
  add('IO USB-'+kind+' Z'+str(z)+' metal mouth / visual allocation',metal,(.72,.74,.76),role='Mouth shape/height/wall thickness visual allocation, not exact supplier profile. '+('Published front projection3.2.' if kind=='C' else 'Published width17.8 only; forward projection not stated, allocated0; do not infer OEM exact setback.'))
  add('IO USB-'+kind+' Z'+str(z)+' insulator / visual allocation',box(100-nw/2+1,front+1,z-.6,nw-2,3,1.2),(.08,.32,.72) if kind=='A' else (.09,.10,.11),role='Visual reference, not contact or OEM insulator geometry')
 bom('Newnex U4S5C01C08-010 panel-C female to C male 1m',2,'Commercial passive extension, full CC/VCONN and4SSpairs per drawing. Each C male into independent Delock67234/Type-E host. No Y/legacyA-to-Csocket. No USB-IF chain certification or PD/AltMode/USB4/Thunderbolt claim. C1 variant qty1.')
 bom('Newnex USR2-AA-1M panel-A female to A male 1m',2,'Catalogue links USR2-A family drawing; receiving variant must match38.5x13.7/30M3pitch. A male connects82941 female; NEVER A-male/A-male cable.')
 bom('Delock 67234 Type-E Key A male20p to USB-C female',2,'Approx18x15x7 manufacturer listing. One independent supported Type-E header per C; direct host adapter, NOT Y. C1 qty1. Secure cable near header, do not lever PCB header.')
 bom('Delock 82941 19p female to two USB-A female 45cm',1,'Manufacturer45cm including connectors, supports two host A ports. Secure both extra mated pairs on cushioned cradle; no dangling couplers. Allocations not exact OEM CAD.')
 # Audio: body seats fascia rear; thread protrudes3mm from body shoulder.
 audio=union([cyl(5.75,32,100,-196.5,281),cyl(3,15,100,-164.5,281),cyl(3,3,100,-199.5,281)]).cut(cyl(1.75,6,100,-199.51,281))
 add('IO FRONTX P0902_036 stereo pass-through body',audio,role='SupplierØ11.5 body32 +15 relief; exposed thread3; lead36in confirmed. Stereo rear-output pass-through, NOT HD_AUDIO/headset microphone/amplifier.')
 add('IO FRONTX supplied ring nut Ø8 x1.8',cyl(4,1.8,100,-199.3,281).cut(cyl(3,1.8,100,-199.3,281)),(.62,.64,.66),role='USE SUPPLIED NUT; thread specification not given. Seats fasciafrontY-197.5;3mmthread permits1mm panel+1.8nut+0.2tip nominal.')
 bom('FRONTX P0902_036 (P0902-036) 36in stereo panel female to male',1,'36in=914.4mm confirmed supplier page; includes suppliedØ8x1.8ringnut. Ø6.1cut, finishedpanel STRICTLY<1.2. 32+15rearbody. No HD_AUDIO or microphone function.')
 # Keep existing rear hole and grommet. Split grommet installed after passing bare plug through panel.
 grommet=next(o for o in d.Objects if o.Label.startswith('Rear audio grommet'))
 prop(grommet,'Qualification','Split grommet Ø12 panel / nominalID9. Remove grommet, pass plug hood <=11mm through bare deburredØ12 hole, then fit split grommet around cable. Cable OD must suit final grommet; do not force plug throughID9. Reject larger hood unless a controlled matched rear-only redesign is made.')
 for r in hb:
  if r['name'].startswith('Rear audio grommet'):r['spec']=grommet.Qualification
 # Construction wires: actual centerline entries and loop allocations, excluded from material/STEP solids.
 routes=[]
 def wire(label,edges,role):return add(label,Part.makeCompound(edges),(.20,.65,.80),'IO_Routing_Construction',role)
 def arc(p,m,q):return Part.Arc(V(*p),V(*m),V(*q)).toShape()
 for z,kind,rear in [(380,'C',-155.5),(360,'C',-155.5),(337,'A',-156.5),(316,'A',-156.5)]:
  start=(100,rear,z);p=(100,-140,z);q=(50,-90,z);e=(0,-90,z)
  edges=[Part.makeLine(V(*start),V(*p)),arc(p,(50+50/math.sqrt(2),-140+50/math.sqrt(2),z),q),Part.makeLine(V(*q),V(*e))]
  wire('IO route USB-'+kind+' Z'+str(z)+' entry R50',edges,'Nonmaterial centerline; reserve sweptØ10. R50 designer allocation, not claimed OEM minimum radius. Actual cableOD/minbend required on receiving.')
  loop=[arc((0,-90,z),(-50,-140,z),(0,-190,z)),arc((0,-190,z),(50/math.sqrt(2),-140-50/math.sqrt(2),z),(50,-140,z))]
  wire('IO service loop USB-'+kind+' Z'+str(z)+' R50',loop,'Nonmaterial OPEN270deg R50 service loop, center(0,-140,Z); sweptØ10 reserve X±55 Y-195..-85. Arc235.62mm ends(50,-140,Z), does not close across its own entry. Tail route to actual header remains board dependent.')
  routes.append(dict(kind=kind,z=z,start=[100,rear,z],bend_center=[50,-140,z],bend_radius_mm=50,loop_center=[0,-140,z],loop_radius_mm=50,clearance_diameter_mm=10,entry_length_mm=(-140-rear)+math.pi*25+50,one_loop_length_mm=75*math.pi,loop_angle_degrees=270,tail_start=[50,-140,z],lead_length_mm=1000,remaining_after_entry_and_one_loop_mm=1000-((-140-rear)+math.pi*25+50)-75*math.pi,connector_length_deduction_allowance_mm=85 if kind=='C' else 90,remaining_flexible_length_allocation_mm=1000-((-140-rear)+math.pi*25+50)-75*math.pi-(85 if kind=='C' else 90),status='Raw1000mm lead budget includes connector ends; deduct85mm C/90mm A designer allowance before planning flexible header tail. Actual end-to-end datum/hood dimensions and board endpoints must be checked; not a measured cable cut length.'))
 # Lace loop bundle to existing left carrier return holes; flexible supports, not load-bearing connector mounts.
 for z in [300,380]:
  points=[(62,-181,z),(56,-181,z),(54,-145,z),(54,-135,z),(58,-135,z),(60,-177,z),(62,-177,z)]
  wire('IO cushioned lacing anchor on existing I02 return Z'+str(z),[Part.makePolygon([V(*p) for p in points])],'Nonmaterial strap path; 2.5mm releasable tie through existingØ3holes. Protective sleeving at all metal edges. Use adjustable broad cushioned straps to support service-loop bundle, not tighten data cable jacket.')
 # Board-dependent mating pair allocations. Wireframes have no manufactured mass.
 for z in [400,423]:
  reserve=box(-85,-135,z,55,20,15)
  wire('IO Type-E + C male mating/support allocation Z'+str(z),reserve.Edges,'55x20x15 combined service allocation. NOT installed board header position or full OEM CAD. Delock18x15x7 +35longmalehood12.2x6.4; support cable close to actual independent header with removable sleeved ties, no header levering.')
 # A mated-pair cradle tied to left return, front void aboveGPU, independent of actual19p header.
 reserve=box(-48,-120,286,96,25,18)
 wire('IO dual A mated-pair cushioned cradle allocation',reserve.Edges,'96x25x18 designer allocation only for82941 female pair + twoNewnexmale plugs. Secure to laced loop support, not floating; verify actual adapter dimensions on receiving. Header lead45cm routed to selected board with no fan incursion.')
 for x in [-30,30]:
  wire('IO dual A mating restraint strap X'+str(x),[Part.makePolygon([V(x,-121,285),V(x,-94,285),V(x,-94,305),V(x,-121,305),V(x,-121,285)])],'Nonmaterial releasable cushioned strap around paired connectors; prevents dangling and strain. Supply two straps and insulating sleeve.')
 # Protected audio path in the right perimeter lane, below optionalfan; no new rear cut.
 ap=[(100,-149.5,281),(100,-140,281)]
 audioedges=[Part.makeLine(V(*ap[0]),V(*ap[1])),arc(ap[1],(130-30*math.cos(math.pi/6),-125,281),(115,-140+15*math.sqrt(3),281)),arc((115,-140+15*math.sqrt(3),281),(100+30*math.cos(math.pi/6),-140+30*math.sqrt(3)-15,281),(130,-140+30*math.sqrt(3),281)),Part.makeLine(V(130,-140+30*math.sqrt(3),281),V(130,180,281)),Part.makeLine(V(130,180,281),V(130,202,280))]
 wire('IO stereo cable protected right-side route to split rear grommet',audioedges,'Nonmaterial route, reserveØ6; rear holeX130Z280 unchanged. Pass hood<=11mm before split grommet installation. Tie at rightreturn and existing rearbond-area independent insulated restraint; no safety-earth disconnection. External protected cable to selected rear stereo-output socket; socket coordinates board dependent.')
 wire('IO audio power strain relief on existing right I02 return',[Part.makePolygon([V(138,-181,300),V(132,-181,300),V(130,-150,281),V(126,-150,281),V(132,-177,300),V(138,-177,300)])],'Nonmaterial sleeved tie path on existingreturnholes; support audio and power separately, no terminal strain. Rightlane audio below optionalfan; no addedhole.')
 # Power button geometry remains unchanged; show only the low-current switch-pair route allocation.
 wire('IO power switch pair entry and support allocation',[Part.makeLine(V(100,-179.5,400),V(100,-160,400)),arc((100,-160,400),(110-10/math.sqrt(2),-160+10/math.sqrt(2),400),(110,-150,400)),Part.makeLine(V(110,-150,400),V(130,-150,400))],'Nonmaterial Ø4pair allocation, R10designer turn; not OEM bendradius. Continue sleeved along rightcarrier anchor to actualmotherboardPWR_SW pins; momentary switch only, no mains/USB power connection. Preserve PV0F24011 terminal geometry and insulate terminals.')
 wire('IO service-loop lacing spine',[Part.makeLine(V(57,-140,300),V(57,-140,386))],'Nonmaterial flexible cushioned lacing spine secured to existingleftreturnanchorsZ300/380. Four loops restrained independently; do not suspend connector weight from sockets.')
 for z in [316,337,360,380]:
  wire('IO service-loop cushioned restraint Z'+str(z),[Part.makePolygon([V(44,-140,z-6),V(57,-140,z-6),V(57,-140,z+6),V(44,-140,z+6),V(44,-140,z-6)])],'Nonmaterial broadstrap path aroundØ10clearance service-loop tube, attachedtolacing spine. Loose enough for jacket protection; adjust to actualcable without kinks.')
 wire('IO A mating cradle tether to leftreturn',[Part.makePolygon([V(62,-177,300),V(57,-140,300),V(30,-120,300)]),Part.makeLine(V(57,-140,300),V(-30,-120,300))],'Nonmaterial laced cradle support and restraint: two secured A matedpairs aboveGPU, not dangling. Insulating/cushioned sleeves required; dimensions allocations only.')
 bom('E-Switch PV0F24011 existing power switch',1,'Unchanged selected power part/geometry/Ø12.1cutout atX100Z400. Use supplied mounting hardware; verify nut/tool and terminal insulation. Power-onlyvariant qty1; fullyblank qty0. Momentary motherboard PWR_SW, not mains.')
 bom('IO releasable nylon ties width2.5mm',8,'ExistingI02 Ø3 returnholes: cushioned lacing and strain relief, do not crush cable jacket; no addedpanel holes')
 bom('IO broad cushioned hook-loop service/connector straps',6,'4service-loop retention +2 A mating-pair restraints; lash to carrier return anchors. Secure Type-E cable near actual header using spare nylon ties; never load header with cable weight.')
 bom('IO protective cable sleeves / split abrasion wrap',1,'Cut-to-fit set for I02 lacing, paired couplers and protected external audio run. No sharp edges or fan access; tie locations adjusted to actual cable without changing sheet interfaces.')
 joints=[dict(pair='I03/I02',scope='IOCompletion',pattern_global_XZ=[[x,z] for x in [72,128] for z in [308,386]],hardware='4 M3x6 ISO7380-1 +4 .5washers +4 M3plainnuts',stack_mm=[1,1,.5,2.4],nominal_tip_mm=1.1,access='Bench assemble cage/ladder before installing fascia; front heads concealed; open-right-side nut access'),dict(pair='4 Newnex modules/I03',scope='IOCompletion',hardware='8 M3x4 ISO7380-1 +8 .5washers to embedded supplier M3nuts',stack_mm=[1,.5],engagement_nominal_mm=2.5,access='Bench front hex key; stripcage for service; actual screw-bottoming/engagement receiving check required'),dict(pair='FRONTX/I01',scope='IOCompletion',hardware='Supplied ringnut ONLY, thread unspecified',stack_mm=[1,1.8],nominal_thread_tip_mm=.2,access='Nut fromfront before captured fascia fitted; finishedpanel<1.2')]
 fastening=[r for r in json.load(open(ROOT+'/fastening-pairs.json')) if r.get('scope')!='IOCompletion']+joints
 interfaces=dict(schema=1,units='mm',status='UNPROTOTYPED subsystem integrated; supplier-envelope allocations are not verified OEM fit',port_centers_XZ={'power':[100,400],'C1':[100,380],'C2':[100,360],'A1':[100,337],'A2':[100,316],'audio':[100,281]},planes_Y={'fascia_front':-197.5,'fascia_back':-196.5,'I02_front':-195.5,'I02_back_I03_front':-194.5,'I03_back':-193.5,'USB_flange':-193,'C_nose':-196.2,'A_front_reserve':-193},apertures={'C':{'width':14,'height':8,'radius':2},'A':{'width':20,'height':12,'radius':1},'audio_diameter':6.1,'power_diameter':12.1},flange={'C':{'width':30,'height':8,'M3_pitch':20,'rear_depth_including_relief':37.5,'relief_diameter':9.3,'nose_forward':3.2},'A':{'width':38.5,'height':13.7,'M3_pitch':30,'body_rear':26.5,'rear_including_relief':36.5,'nose_width':17.8,'forward_projection_published':False}},module_objects=module_objects,nominal_clearances_mm={'USB_buttonhead_to_fascia_back':.35,'I03_attachment_head_to_wrap_inner':.85,'C_recess':1.3,'A_reserve_recess_not_OEM_exact':4.5},joints=joints,routes=routes,audio={'part':'FRONTX P0902_036','length_mm':914.4,'body_diameter':11.5,'body_rear':32,'relief_length':15,'finished_panel_limit_exclusive':1.2,'supplied_nut_diameter':8,'supplied_nut_thickness':1.8,'thread_exposed':3,'rear_hole_diameter':12,'grommet_nominal_ID':9,'assembly_maximum_plug_hood_diameter':11,'thread_specification':'unpublished: use supplied nut'},variants=[{'fascia':'I01','C':2,'A':2,'audio':1,'power':1,'I03':1,'I03_attachment_screws':4,'I03_attachment_washers':4,'I03_attachment_nuts':4,'module_washers':8,'Delock67234':2,'Delock82941':1,'module_screws':8},{'fascia':'I01-C1','C':1,'A':2,'audio':1,'power':1,'I03':1,'I03_attachment_screws':4,'I03_attachment_washers':4,'I03_attachment_nuts':4,'module_washers':6,'Delock67234':1,'Delock82941':1,'module_screws':6,'blank_C2':True},{'fascia':'I01-power-only','C':0,'A':0,'audio':0,'power':1,'I03':0,'I03_attachment_screws':0,'I03_attachment_washers':0,'I03_attachment_nuts':0,'module_washers':0,'Delock67234':0,'Delock82941':0,'module_screws':0},{'fascia':'I00-fully-blank-option','C':0,'A':0,'audio':0,'power':0,'I03':0,'I03_attachment_screws':0,'I03_attachment_washers':0,'I03_attachment_nuts':0,'module_washers':0,'Delock67234':0,'Delock82941':0,'module_screws':0}],topology={'C':'Each Newnex male -> Delock67234 Cfemale / Type-E20p male -> independent supported hostType-E. NeverY or legacyA-to-Csocket adapter.','A':'Each Newnex A male -> one82941 A female -> shared19p header carrying2independent A ports. Never A-male/A-male cable.','audio':'Stereo3.5male rear-output pass-through; NOT HD_AUDIO/headset mic/amp.','qualification':'Commercial passive extension/header-adapter architecture; NOT USB-IF certified cable chain or direct harness. Standard5V host only; noPD/AltMode/USB4/Thunderbolt claim. Actual chain speed and bothC orientations require prototype qualification.'},sources=['https://newnex.com/usb-3-panel-mount-cables.php','https://newnex.com/documents/drawings/U4S5C01C08-010.PDF','https://newnex.com/documents/USR2-A-Custom-Drawing.PDF','https://www.ntcdistributing.com/usb-3-0/panel-mount-cables/a-female/usb-3-0-a-female-panel-mount-to-a-male-cable/?sku=USR2-AA-1M','https://www.delock.com/produkt/67234/pdf.html?sprache=en','https://www.delock.com/produkt/82941/pdf.html?sprache=en','https://www.frontx.com/pro/p0902_036.html','https://www.frontx.com/pro/3.5audio_dimensions.gif','https://www.trfastenings.com/products/catalogue/screws-and-bolts/Hexagon-Socket-Screws/Button-Head/TR00004815-000'],physical_checks=['Unpublished flange thickness/corner profiles, embeddednut thread depth and selected retailA family match','Actual hood access/recess and screw finish clearance; verify C<=12.2x6.4,A<=18x10 with rounded aperture corners','Finishedaudio panel<1.2, suppliednut and actualhood<=11 through bare rearØ12 before split grommet','Actual cable OD/minbend, residual slack, secured adapter/male couplers and board-dependent headers; cableweight must not lever PCBheaders','USB data enumeration/speed bothC orientations, standard5V current and hotplug; no certification inferred','Power suppliednut/tool fit near topnotch, tactile access, captive fascia compression; existingPV0F24011 unchanged'])
 interfaces['common_plate']={'bounds_X_mm': [66, 134], 'bounds_Z_mm': [303, 391], 'planes_Y_mm': [-194.5, -193.5], 'thickness_mm': 1, 'attachment_hole_diameter_mm': 3.4, 'attachment_centers_XZ': [[72, 308], [72, 386], [128, 308], [128, 386]], 'top_notch_XZ_bounds': [90, 389, 110, 391], 'retained_cage_joint_scallops': [{'center_XZ': [68, 336], 'radius_mm': 4.5, 'open_to_outer_edge': True}, {'center_XZ': [132, 336], 'radius_mm': 4.5, 'open_to_outer_edge': True}], 'C_mount_centers_XZ': [[90, 380], [110, 380], [90, 360], [110, 360]], 'A_mount_centers_XZ': [[85, 337], [115, 337], [85, 316], [115, 316]], 'module_hole_diameter_mm': 3.4, 'bends': []}
 interfaces['topology']['power']='UnchangedPV0F24011 momentary switch -> actual motherboardPWR_SW pins; insulated low-current pair, not mains or USB power.'
 interfaces['C_orientation_test_matrix']={'per_chain_local_combinations': [[0, 0], [0, 180], [180, 0], [180, 180]], 'axes': ['rear male to Delock67234', 'front user plug'], 'reversible_device_end': 'Repeat all four with the device-end orientation reversed when applicable, eight total.', 'tests': ['enumeration', 'USB2 and SuperSpeed operation', 'throughput/error behaviour', 'hotplug', 'standard5V current within host/component budget']}
 for name,data in [('panels.json',panels),('hardware-bom-detail.json',hb),('fastening-pairs.json',fastening),('io-interfaces.json',interfaces)]:json.dump(data,open(ROOT+'/'+name,'w'),indent=2)
 if d.getObject('Dimensions'):d.getObject('Dimensions').set('B11','2C/2A/stereo selected subsystem; prototype qualification required')
 d.recompute();fd.recompute();d.saveAs(ROOT+'/CAD/Sheet Metal PC Case.FCStd');fd.saveAs(ROOT+'/CAD/Sheet Metal PC Case Flat Patterns.FCStd')
 print('IO COMPLETION SAVED',len(panels),'main designs',sum(p['quantity'] for p in panels),'main sheet instances',flush=True)
 return interfaces
if __name__=='__main__':finish()
