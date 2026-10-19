# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Check local new solids vs entire assembly; swept route distances, not empty boxes.
Physical cable properties/header placement remain explicit receiving/prototype checks.
"""
import os,sys,shutil,json,math
exe=shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
if exe:sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))),'lib'))
import FreeCAD as A,Part
V=A.Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=A.openDocument(root+'/CAD/Sheet Metal PC Case.FCStd')
leaves=[o for o in d.Objects if not hasattr(o,'Group') and hasattr(o,'Shape') and o.Shape.Solids]
new=[o for o in leaves if getattr(o,'IOCompletion','')=='owned']
collisions=[];pairs=set()
for a in new:
 for b in leaves:
  key=tuple(sorted([a.Name,b.Name]))
  if a==b or key in pairs:continue
  pairs.add(key)
  if not a.Shape.BoundBox.intersect(b.Shape.BoundBox):continue
  v=a.Shape.common(b.Shape).Volume
  if v>.001:collisions.append(dict(a=a.Label,b=b.Label,volume_mm3=v))
# Explicit intended threaded engagements are modelled as bore/major diameter contact,
# not true thread solids. No blanket exclusion of new module or fastener collisions.
print('Solid comparisons done',collisions,flush=True)
assert not collisions,collisions
fascia=next(o for o in leaves if getattr(o,'PartID','')=='I01');plate=next(o for o in leaves if getattr(o,'PartID','')=='I03');wrap=next(o for o in leaves if getattr(o,'PartID','')=='W01')
heads=[o for o in new if 'M3x4 button head' in o.Label];attachments=[o for o in new if 'attachment M3x6 button head' in o.Label]
clearances={'module_head_to_fascia_back_mm':min(o.Shape.distToShape(fascia.Shape)[0] for o in heads),'attachment_head_to_wrap_mm':min(o.Shape.distToShape(wrap.Shape)[0] for o in attachments)}
assert abs(clearances['module_head_to_fascia_back_mm']-.35)<1e-6
assert abs(clearances['attachment_head_to_wrap_mm']-.85)<1e-6
oldfix=[o for o in leaves if o.Label.startswith(('I/O shell M3','I/O carrier washer','I/O carrier removable M3'))]
clearances['I03_scallop_to_retained_cage_joint_mm']=min(plate.Shape.distToShape(o.Shape)[0] for o in oldfix)
powerreserve=Part.makeCylinder(10,12,V(100,-197,400),V(0,1,0))
clearances['I03_to_power_R10_tool_allocation_mm']=plate.Shape.distToShape(powerreserve)[0]
assert plate.Shape.common(powerreserve).Volume<.001
# Test diameter10 swept entry/loop clearance using distance to actual continuous centerlines.
# This is equivalent to checking a round tube, not zero-overlap boxes. Root entry into
# its own relief is intentionally excluded and reported individually.
routes=[]
for o in d.Objects:
 if not (o.Label.startswith('IO route USB-') or o.Label.startswith('IO service loop USB-') or o.Label.startswith('IO stereo cable protected') or o.Label.startswith('IO power switch pair')):continue
 radius=2 if 'power switch pair' in o.Label else (3 if 'stereo' in o.Label else 5)
 root_module=None
 if o.Label.startswith('IO route USB-'):
  z=int(o.Label.split(' Z')[1].split()[0]);root_module=next(q.Name for q in new if 'conservative body allocation' in q.Label and 'Z'+str(z)+' ' in q.Label)
 if 'stereo' in o.Label:root_module=next(q.Name for q in new if q.Label.startswith('IO FRONTX P0902_036'))
 if 'power switch pair' in o.Label:root_module=next(q.Name for q in leaves if q.Label.startswith('E-Switch PV0F24011'))
 nearest=[]
 for q in leaves:
  aa=o.Shape.BoundBox;bb=q.Shape.BoundBox
  lower=math.sqrt(sum(max(0,getattr(aa,k+'Min')-getattr(bb,k+'Max'),getattr(bb,k+'Min')-getattr(aa,k+'Max'))**2 for k in ['X','Y','Z']))
  if lower>radius+20:continue
  if q.Name==root_module:continue
  if 'stereo' in o.Label and q.Label.startswith('Rear audio grommet'):continue # intended cable-through-grommet contact, actual OD fit gate
  distance=o.Shape.distToShape(q.Shape)[0]-radius
  nearest.append((distance,q.Label))
 nearest.sort();routes.append(dict(route=o.Label,clearance_radius_mm=radius,minimum_swept_clearance_mm=nearest[0][0],nearest=nearest[:3],intentional_root_contact_object=root_module,method='Actual continuous centerline-to-solid distance minus allocated cable radius; nonmaterial construction geometry'))
 assert nearest[0][0]>=-1e-6,(o.Label,nearest[:3])
# Check cable routes against each other (same cable's entry/loop is connected intentionally).
route_objects=[o for o in d.Objects if o.Label.startswith(('IO route USB-','IO service loop USB-','IO stereo cable protected','IO power switch pair'))]
route_pairs=[]
for i,a in enumerate(route_objects):
 for b in route_objects[i+1:]:
  if 'USB-' in a.Label and 'USB-' in b.Label and a.Label.split(' Z')[1].split()[0]==b.Label.split(' Z')[1].split()[0]:continue
  r1=2 if 'power switch pair' in a.Label else (3 if 'stereo' in a.Label else 5);r2=2 if 'power switch pair' in b.Label else (3 if 'stereo' in b.Label else 5)
  distance=a.Shape.distToShape(b.Shape)[0]-r1-r2;assert distance>=-1e-6,(a.Label,b.Label,distance)
  route_pairs.append(dict(a=a.Label,b=b.Label,swept_clearance_mm=distance))
# Every USB entry and OPEN270 loop is one open, tangent-continuous path.
self_checks=[]
for z in [380,360,337,316]:
 entry=next(o for o in route_objects if o.Label.startswith('IO route USB-') and (' Z'+str(z)+' ') in o.Label)
 loop=next(o for o in route_objects if o.Label.startswith('IO service loop USB-') and (' Z'+str(z)+' ') in o.Label)
 edges=entry.Shape.Edges+loop.Shape.Edges;w=Part.Wire(edges)
 assert w.isValid() and not w.isClosed() and len(w.Wires)==1
 assert abs(loop.Shape.Length-75*math.pi)<1e-6
 assert (edges[0].Vertexes[0].Point-edges[-1].Vertexes[-1].Point).Length>10
 gaps=[edges[i].distToShape(edges[j])[0]-10 for i in range(len(edges)) for j in range(i+2,len(edges))]
 assert min(gaps)>0,(z,gaps)
 self_checks.append(dict(z=z,continuous_open_wire=True,service_arc_degrees=270,service_length_mm=loop.Shape.Length,minimum_nonadjacent_swept_gap_mm=min(gaps)))

# Mating block allocations tested as occupied volumes; actual board endpoints not asserted.
reserves=[]
for label,origin,size in [('Type-E upper',(-85,-135,423),(55,20,15)),('Type-E lower',(-85,-135,400),(55,20,15)),('A restrained pair',(-48,-120,286),(96,25,18))]:
 s=Part.makeBox(*size,V(*origin));hits=[]
 for q in leaves:
  if not s.BoundBox.intersect(q.Shape.BoundBox):continue
  v=s.common(q.Shape).Volume
  if v>.001:hits.append(dict(part=q.Label,volume_mm3=v))
 assert not hits,(label,hits)
 reserves.append(dict(name=label,origin=origin,size=size,solid_collisions=hits,status='Service/mating allocation only, NOT board-specific installed connector coordinates'))
# Main sheet validation has 9 preexisting M3 tap-drill/major-thread representations;
# keep those distinct from unexpected local interference (zero tolerated here).
out=dict(passed=True,new_shaped_solid_leaves=len(new),unexpected_new_solid_intersections=collisions,nominal_clearances=clearances,routing=routes,inter_route_clearances=route_pairs,mating_allocations=reserves,service_path_self_checks=self_checks,intentional_thread_representation='New nominal M3 screws touch nominalØ3 embeddednut/nut bores; true helices not modelled. Existing9 PCI screw/tap-drill intersections remain separately in assembly-check.json.',qualification='Swept allocations validate ONLY shown paths and diameter assumptions. Actual cable OD/minbend, local tie force, header-tail endpoints/slack and external audio end depend on selected hardware; no complete installed-harness or OEM module-fit certification.')
json.dump(out,open(root+'/io-clearance-check.json','w'),indent=2)
print('IO CHECK PASS',len(new),'new solid leaves;',len(routes),'swept route allocations; zero unexpected new solid clashes')
print(json.dumps(clearances,indent=2))
