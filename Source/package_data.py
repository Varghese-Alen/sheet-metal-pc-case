# SPDX-License-Identifier: CERN-OHL-P-2.0
import sys,os,shutil,json,csv,collections,math
exe=shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
if exe:sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))),'lib'))
import FreeCAD as A,Part
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));d=A.openDocument(root+'/CAD/Sheet Metal PC Case.FCStd');V=A.Vector
panels=json.load(open(root+'/panels.json'));fd=A.openDocument(root+'/CAD/Sheet Metal PC Case Flat Patterns.FCStd')
# Explicit bend-axis endpoint geometry, in rawflat AND serialized-DXF origin coordinates.
for panel in panels:
 ox,oy=panel['DXF_origin_mm']
 for bend in panel['bends']:
  if 'flat_axis_u' in bend:
   u=bend['flat_axis_u'];a,b=bend['flat_axis_v_range'];lines=[[[u,a],[u,b]]]
  elif panel['id']=='M02':
   v=bend['bend_axis_flat_v'];lines=[[[a,v],[b,v]] for a,b in bend['axis_ranges']]
  else:
   v=bend['bend_axis_flat_s'];a,b=panel['flat_bounds'][0],panel['flat_bounds'][2]
   if panel['id']=='W01':a,b=(-149,149) if bend['sequence'] in [1,2] else (-143,143)
   lines=[[[a,v],[b,v]]]
  bend['flat_bend_lines_raw_mm']=lines
  bend['flat_bend_lines_DXF_mm']=[[[x-ox,y-oy] for x,y in line] for line in lines]
json.dump(panels,open(root+'/panels.json','w'),indent=2)
with open(root+'/bend-schedule.csv','w') as bf:
 bw=csv.writer(bf);bw.writerow(['part','quantity','form_step','signed_angle_deg','inside_radius_mm','K','BA_mm','DXF_x1','DXF_y1','DXF_x2','DXF_y2','note'])
 for panel in panels:
  for bend in panel['bends']:
   for a,b in bend['flat_bend_lines_DXF_mm']:bw.writerow([panel['id'],panel['quantity'],bend['suggested_forming_step'],bend['angle_deg'],bend['inside_radius_mm'],bend['K'],bend['BA_mm'],*a,*b,'Neutral-BA midline; opposite sled fold hands; shop calibration mandatory'])
with open(root+'/sheet-parts-bom.csv','w') as f:
 w=csv.writer(f);w.writerow(['ID','quantity','material','thickness_mm','flat_width_mm','flat_height_mm','net_flat_area_mm2','estimated_unfinished_mass_kg_each','file'])
 for p in panels:
  sh=next(o.Shape for o in fd.Objects if o.Label==p['id']);rho=2.68e-6 if 'aluminium' in p['material'] else 7.85e-6
  w.writerow([p['id'],p['quantity'],p['material'],p['thickness_mm'],*p['flat_size_mm'],sh.Volume/p['thickness_mm'],sh.Volume*rho,'DXF/'+p['id']+'.dxf'])
agg=collections.Counter();spec={}
for row in json.load(open(root+'/hardware-bom-detail.json')):agg[row['name']]+=row['quantity'];spec[row['name']]=row['spec']
agg['9.525mm female-M3 / male-M3x5 standoff']=9;spec['9.525mm female-M3 / male-M3x5 standoff']='ATX installed9. Supply12positions total; install only actual motherboard subset. 9.525 above tray; locknuts supplied separately in BOM. Supplier/dryfit gate.'
with open(root+'/hardware-bom.csv','w') as f:
 w=csv.writer(f);w.writerow(['description','quantity_shown_or_required','qualification'])
 for name in sorted(agg):w.writerow([name,agg[name],spec[name]])
# Structural-part attachment graph includes every main fabricated part.
joints=[
 ('S01/S02','W01','10 M3x8 +10 RRE03-1 +10 nominal0.2shims','outsideX','1.5side +.7head/shim gap +1flange; nominal4.8useful engaged thread; coupon-set insert'),
 ('W01','R01 via C01..C04','8 M3x8,8washers,8nuts','roof/floor/rear plus open sides','two1mm sheets each joint; washer.5,nut2.4;8length leaves3.1nominal beyond nut'),
 ('M01','W01','4 M3x8,4washers,4nuts','roof/floor exterior, left-side spanner','two1mm sheets; washer.5,nut2.4; not captive; remove leftsled for service'),
 ('M01','R01 via T01/T02','4 M3x8,4washers,4nuts','rear exterior and component side; nut cable side','two1mm sheets each; washer.5,nut2.4'),
 ('M02','R01','2 M3x10,2 two-mm spacers,2washers,2nuts','rear','1back+2spacer+1rail+.5washer+2.4nut=6.9;3.1nominal excess'),
 ('M03','M02','2 M3x5 through rail into3mm tapped strip','+X outside rear rail','1rail+3nutstrip=4; full3engagement,1tip; M3 taps afterlaser'),
 ('purchased PCI cover/GPU bracket','M02/M03','7 M3x6 +7M3washers;7purchased covers','+X rear rail','1nominal cover+.5washer+1rail+3nutstrip=5.5;0.5tip. Notch fit and0.4572datum gauge gate.'),
 ('I01','W01/I02','captured0.5gasket +4one-mm pads','removeI02fromrightinterior','fasciaY-197.5..-196.5; backpads tocarrierY-195.5; cage captures flange, no floatingface'),
 ('I02','W01','2 M3x10 pan screws,2x2.5spacers,2washers,2nuts','front screwdriver/right-side nut access','1wrap+2.5spacer+1carrier+.5washer+2.4nut=7.4;2.6nominaltip; no welding'),
 ('F01','W01','2 M3x8 +washers/nuts','roof outside, side spanner','1roof+1bracket+.5washer+2.4nut; wholefan/bracket removable'),
 ('optional120fan','F01','4 M4x35 +.8washers +3.2nuts','bench after bracket removal','25fan+1bracket+.8washer+3.2nut=30;5nominaltip; head3gives0.5to side'),
 ('G01','W01','2 M4x10 +.8washers +3.2nuts','floor outside; open right side','1floor+3foot+.8washer+3.2nut=8;2tip;2bolts share54longY-adjustment slot'),
 ('G02','G01','2 M4x12 +.8washers +3.2nuts','open right side','3ledge+3post+.8washer+3.2nut=10;2tip; verticalslots;2padtoGPU'),
 ('PSU support bosses','W01','4 M3x6 into blind-M3 Ø8x8 bosses','underside','1floor+5thread engaged;6deep bore leaves2topwall;supporttopZ34'),
 ('PSU','R01','4 #6-32UNC x1/4in','rear','1back;5.35nominalpenetration MUST be checked against chosenPSU; no PSU drilling/opening'),
 ('SSD','M01','4 M3x4','component side before motherboard install','1tray gives3nominaldrivepenetration; chosenSSD limit gate; no addednuts'),
 ('motherboard standoffs','M01','9 male-M3x5 studs +9M3nuts','cable side before board','1tray+2.4nut;1.6tip;9.525standoff height fixed'),
 ('motherboard','standoffs','9 M3x6','component side','1.6PCB +4.4female engagement; install only board-supported standoffs'),
 ('bottom140fan','W01','4 M4x35 +.8washers +3.2nuts','underside and open case','1floor+25fan+.8washer+3.2nut=30;5tip clear components'),
 ('rear140fan','R01','4 M4x30 +.8washers +3.2plainnuts','rear and open side','1back+25fan+.8washer+3.2nut=30 exactly; flush fullnut engagement, check actual stack. Plain nut plus removable lowstrengththreadlock, NOT nyloc.35hits optionalbracket.'),
 ('bond lug','R01','M4x10, toothed/appropriate conductive lug washer and nut','rear/open side','Ø4.5dedicated holeX130Z250. Actual ringlug thickness/screw length must be stack-checked. PSU safety earth remains untouched.')]
# Selected I/O structural and electrical interfaces, not obsolete sample crossbars.
joints.extend([
 ('I03','I02','4 M3x6 ISO7380-1 +4 .5washers +4 plainM3nuts','bench fronthex / openright nuts','1+1+.5+2.4=4.9mm;1.1tip;headmax1.65;0.85to wrapinner'),
 ('4 Newnex USB modules','I03','8 M3x4 ISO7380-1 +8 .5washers -> embeddedM3nuts','bench fronthex with cage removed','1plate+.5washer;2.5nominal engagement; supplier alloweddepth UNKNOWN, bottoming/engagement receiving check;flangeY-193'),
 ('PV0F24011 unchanged','I01','supplier mounting nut/washer, no substitute thread callout','bench with cage removed','unchangedØ12.1cut and bezel/barrel datum; verify suppliednut/tool access and insulated terminals'),
 ('FRONTX P0902_036','I01','supplied ringnut only; thread unspecified','front before capturedfascia install','1mm fascia finished<1.2;nut1.8;3mm exposedthread;0.2nominaltip'),
 ('USB/audio cable restraint','I02 existingreturn tieholes','8 releasable2.5mm ties +6cushioned straps +sleeving','open case, before closing sides','loop and mating-pair supports; Type-E cable supported near actualheader, no headerlevering; inspect fan exclusion'),
 ('stereo rear cable','R01 existingØ12 exit','split grommet nominalID9','removegrommet,pass plug,fit split aroundcable','maximumplughood<=11mm throughbareØ12; protect externalcable toselectedrearstereooutput')])
json.dump([dict(part=a,mates_to=b,hardware=c,access=e,stack_and_engagement=f) for a,b,c,e,f in joints],open(root+'/joint-schedule.json','w'),indent=2)
with open(root+'/joint-schedule.csv','w') as f:
 w=csv.writer(f);w.writerow(['part','mate','hardware','access','stack_engagement']);w.writerows(joints)
def obj(prefix):return next(o for o in d.Objects if o.Label.startswith(prefix))
# exact sourced datums, clearance reservations and allPSUdepth contact checks
checks={};holes={'A':(0,0),'B':(78.74,0),'C':(124.46,0),'F':(281.94,22.86),'G':(0,154.94),'H':(124.46,154.94),'J':(281.94,154.94),'K':(0,227.33),'L':(124.46,227.33),'M':(281.94,227.33),'R':(58.42,154.94),'S':(78.74,154.94)}
checks['board_datums']={'A_Y':189.7318,'A_Z':141.51,'PCB_Z':[125,429.8],'PCB_rear_Y':199.8918,'rear_inner_Y':202,'PCB_under_X':-106.975,'PCB_top_X':-105.375,'standoff_height':9.525,'rear_IO_X':[-109.2102,-64.7602],'rear_IO_Z':[273.4884,432.2384]}
tray=obj('M01').Shape
for k,(u,v) in holes.items():
 y=189.7318-v;z=141.51+u
 assert tray.common(Part.makeCylinder(1.69,1,V(-117.5,y,z),V(1,0,0))).Volume<1e-6,(k,'trayholemissing')
checks['mounting_holes']=[dict(name=k,Y=189.7318-v,Z=141.51+u) for k,(u,v) in holes.items()]
checks['clearances_mm']={'rearPCB_to_innerrear':2.1082,'PCBtop_to_innerroof':27.2,'GPUfront_to_upperfrontinner':57.8918,'GPU35reserve_to_sideinner':63.875,'CPU170tip_to_sideinner':70.875,'CPU170tip_to_optional_fan':42.375,'CPU170tip_to_optional_bracket':41.375,'optional_fan_frame_to_rear_fan_frame':7,'optional_fan_panhead_to_side':.5,'bottomfan_to_innerfront':8,'bottomfan_to_PSU60reserve':16,'SSD_body_to_leftsideinner':19,'GPU_support_foot_to_bottomfan_X':6}
for depth in [140,160,180]:
 psu=Part.makeBox(150,depth,86,V(-55,202-depth,34));bosses=[o for o in d.Objects if o.Label.startswith('PSU 8mm blind')]
 checks['PSU_%d_depth_all_support_contact'%depth]=all(o.Shape.distToShape(psu)[0]<1e-6 and o.Shape.BoundBox.YMin>202-depth and o.Shape.BoundBox.YMax<202 for o in bosses)
 assert checks['PSU_%d_depth_all_support_contact'%depth]
reserves={'GPU35':Part.makeBox(35,100,65,V(44.625,-130,195)),'PSU60':Part.makeBox(150,60,86,V(-55,-38,34))};inter=[]
for name,shape in reserves.items():
 for o in d.Objects:
  if hasattr(o,'Group') or not hasattr(o,'Shape') or not o.Shape.Solids:continue
  if not shape.BoundBox.intersect(o.Shape.BoundBox):continue
  vol=shape.common(o.Shape).Volume
  if vol>1e-3:inter.append([name,o.Label,vol])
checks['reserve_collisions']=inter;assert not inter,inter
checks['qualifications']=['Simple component envelopes are notOEMreplicas.','Socket/RAM/VRM/GPUcontact/cable bend limits are selected-hardware gates.','Selected I/O envelopes and routing allocations integrated; see io-clearance-check.json and io-interfaces.json. Unknown corners/threaddepth/cableOD/bend and actualheader positions remain physical qualification, not verified OEM fit.','12trayholes verified; selected actualboard subset only.','ATX rearshield band2.54mm clear bothfaces; mask finish.']
json.dump(checks,open(root+'/component-clearances.json','w'),indent=2)
print('COMPONENT/DATUM/RESERVE CHECKS PASS; structured BOM and joint schedule saved')

# Current selected purchased components (overlap with hardware BOM is not additional quantity).
purchased_rows=[{'item': 'E-Switch PV0F24011', 'quantity': '1', 'status': 'production', 'notes': 'Includes supplied nut/O-ring; Ø14bezel; PWR_SW only. Confirm stock and exact part.'}, {'item': 'Two-wire insulated PWR_SW lead', 'quantity': '1', 'status': 'production', 'notes': 'Selected motherboard pinout; protect switch terminals; no LED supply/mains wiring.'}, {'item': '140x140x25 fan,124.5pitch', 'quantity': '2', 'status': 'reference target', 'notes': 'Select actual retail fans with compatible through holes; bottom/rear stacks in joint schedule. Not included OEM models.'}, {'item': '120x120x25 fan,105pitch', 'quantity': '1', 'status': 'optional', 'notes': 'RemovableF01 bracket; X115..140; actual screwhead finish gate.'}, {'item': 'Split grommet forØ12hole,1mmpanel,nominal9clear bore', 'quantity': '1', 'status': 'actual supplier fit gate', 'notes': 'Pass hood<=11mm through bare deburredØ12 BEFORE fitting split grommet around cable; not plug throughID9. Check actual cable fit.'}, {'item': '2mm nonconductive GPU support pad', 'quantity': '1', 'status': 'optional', 'notes': '12x20nominal; actual nonfan loadbearing card contact gate; no loadrating.'}, {'item': '1mm fascia back compression pad2x12', 'quantity': '4', 'status': 'production', 'notes': 'Captive by carrier; no structural adhesive.'}, {'item': 'M3 x 10 pan-head carrier through-bolts', 'quantity': '2', 'status': 'included in hardware BOM', 'notes': 'Ordinary bolts through front at X68/132, Z336; existing 2.5mm spacers, washers and nuts. No welding; do not double-count these bolts.'}, {'item': 'Full-height standard PCI blank cover', 'quantity': '7', 'status': 'production less occupied slots', 'notes': 'Also includedhardwareBOM. Buy real formed locatingtip/notch covers; not fake flat rectangles. Physicalgauge mandatory.'}, {'item': 'Compatible bonding lug/contact hardware and optional service braids', 'quantity': '1', 'status': 'electrical qualification', 'notes': 'M4rearpoint; stack/continuity/corrosion test; no PSU modification.'}, {'item': 'Newnex U4S5C01C08-010', 'quantity': '2', 'status': 'included in hardware BOM; do not double-count', 'notes': '1m panel-C to C male; one independent Delock67234/Type-E host per port. No USB-IF/PD/AltMode/USB4/Thunderbolt claim; actual chain speed and both orientations need qualification.'}, {'item': 'Delock 67234', 'quantity': '2', 'status': 'included in hardware BOM; do not double-count', 'notes': 'Type-E KeyA20p male to C female, approx18x15x7. One per installed C; C1 variant quantity1. Support cable near header.'}, {'item': 'Newnex USR2-AA-1M', 'quantity': '2', 'status': 'included in hardware BOM; do not double-count', 'notes': 'Individual panel-A to A male. Retail end must match linked USR2-A family38.5x13.7/30M3pitch. Connect to82941 female sockets; no A-male/A-male cable.'}, {'item': 'Delock 82941', 'quantity': '1', 'status': 'included in hardware BOM; do not double-count', 'notes': '19pin motherboard header to twoA female,45cm including connectors. Restrain added mating pairs; both ports use independent channels of one two-port host header.'}, {'item': 'FRONTX P0902_036 / P0902-036', 'quantity': '1', 'status': 'included in hardware BOM; do not double-count', 'notes': '36in/914.4mm stereo panel female to male; includes supplied nut. Rear-output pass-through, notHD_AUDIO/headset/amp. Ø6.1hole, finishedpanel strictly<1.2; mask bearing seats.'}, {'item': 'Releasable nylon ties width2.5mm', 'quantity': '8', 'status': 'included in hardware BOM; do not double-count', 'notes': 'Existing carrier return holes; cushion all metal edges and support actual header tails without levering sockets.'}, {'item': 'Broad cushioned hook-loop straps', 'quantity': '6', 'status': 'included in hardware BOM; do not double-count', 'notes': 'Four separate service-loop restraints plus two A mating-pair restraints; do not crush data cable jackets.'}, {'item': 'Protective sleeves / abrasion wrap', 'quantity': '1', 'status': 'included in hardware BOM; do not double-count', 'notes': 'Cut-to-fit set for lacing spine, restrained mating pairs and protected stereo rear run.'}]
with open(root+"/purchased-components.csv","w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=['item', 'quantity', 'status', 'notes']);w.writeheader();w.writerows(purchased_rows)
