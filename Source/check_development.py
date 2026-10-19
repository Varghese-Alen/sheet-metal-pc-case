# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Check analytical neutral-axis area versus formed constant-gauge volume,
then match every circular cut to a source-cylinder axis in the assembly."""
import sys,os,shutil,json,math
exe=shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
if exe:sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))),'lib'))
import FreeCAD as A,Part
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));d=A.openDocument(root+'/CAD/Sheet Metal PC Case.FCStd');fd=A.openDocument(root+'/CAD/Sheet Metal PC Case Flat Patterns.FCStd');panels=json.load(open(root+'/panels.json'));geometry=json.load(open(root+'/drawing-geometry.json'))
out=[]
for p in panels:
 pid=p['id'];s=d.getObject(p['object']).Shape;f=next(o.Shape for o in fd.Objects if o.Label==pid);t=p['thickness_mm'];correction=0
 for b in p['bends']:
  if pid=='W01':width=16 if 'flat_axis_u' in b else (298 if b['sequence'] in [1,2] else 286)
  elif pid=='M02':width=17
  else:width=f.BoundBox.XLength
  correction+=t*t*(.5-b['K'])*abs(math.radians(b['angle_deg']))*width
 err=abs((s.Volume-f.Volume)-correction)
 assert err<.001,(pid,'constant-gauge/development volume mismatch',s.Volume-f.Volume,correction,err)
 # Native full cylindrical cut axes. Duplicate seam surfaces are collapsed by spatial datum.
 bores={}
 for face in s.Faces:
  c=face.Surface
  if not isinstance(c,Part.Cylinder):continue
  u0,u1,v0,v1=face.ParameterRange
  if abs(abs(u1-u0)-2*math.pi)>1e-5:continue
  axis=c.Axis;cc=c.Center;bb=face.BoundBox;ctr=[(bb.XMin+bb.XMax)/2,(bb.YMin+bb.YMax)/2,(bb.ZMin+bb.ZMax)/2]
  key=tuple(round(v,6) for v in ctr+[c.Radius]);bores[key]=dict(center=ctr,axis=[axis.x,axis.y,axis.z],diameter=2*c.Radius)
 circles=[e for e in geometry[pid]['entities'] if e['type']=='CIRCLE']
 # radius-count invariant is independent of coordinate transforms. Slot/handle arcs are not bores.
 def radii(items):
  r={}
  for dia in items:r[round(dia,6)]=r.get(round(dia,6),0)+1
  return r
 assert radii([b['diameter'] for b in bores.values()])==radii([2*c['r'] for c in circles]),(pid,'source/flat circular cut mismatch',radii([b['diameter'] for b in bores.values()]),radii([2*c['r'] for c in circles]))
 out.append(dict(part=pid,formed_volume_mm3=s.Volume,flat_volume_mm3=f.Volume,neutral_axis_volume_correction_mm3=correction,error_mm3=err,valid_constant_gauge_analytical_development=True,circular_bore_count=len(bores),assembled_bores=list(bores.values()),flat_circles=circles))
json.dump(out,open(root+'/development-check.json','w'),indent=2)
print('DEVELOPMENT PASS',len(out),'designs; max volume correction residual',max(x['error_mm3'] for x in out))
# Explicit assembled-to-neutral-strip coordinate mapping for EVERY circular cut.
def serialized_circles(pid):
 lines=open(root+'/DXF/'+pid+'.dxf').read().splitlines();pairs=[(int(lines[i]),lines[i+1]) for i in range(0,len(lines),2)];items=[];g=None
 for code,value in pairs:
  if code==0:
   if g is not None:items.append(dict(type='CIRCLE',c=[float(g[10]),float(g[20])],r=float(g[40])))
   g={} if value=='CIRCLE' else None
  elif g is not None:g[code]=value
 return items
match_report=[]
for p,rec in zip(panels,out):
 pid=p['id'];s=d.getObject(p['object']).Shape;ox,oy=geometry[pid]['origin_shift'];targets=serialized_circles(pid);matches=[]
 segs=next((b['straight_segments'] for b in p['bends'] if 'straight_segments' in b),[])
 def station(a,b):
  for seg in segs:
   x,y=seg['a'];dx,dy=seg['tangent'];along=(a-x)*dx+(b-y)*dy;perp=abs((a-x)*dy-(b-y)*dx)
   if perp<1e-5 and -1e-5<=along<=seg['length']+1e-5:return seg['start']+along
  raise ValueError((pid,'bore not on straight section',a,b))
 for bore in rec['assembled_bores']:
  x,y,z=bore['center'];axis=bore['axis']
  if pid in ['R01','I01','I03']:uv=[x,z]
  elif pid=='M03':uv=[y,z]
  elif pid=='M02':uv=[z,y-201] if abs(axis[0])>.99 else [z,-math.pi/2*1.42-(x-3.2323)]
  elif pid=='W01':
   if abs(axis[0])>.99:
    tab=next(b for b in p['bends'] if 'pilot_assembled' in b and sum((a-bb)**2 for a,bb in zip(b['pilot_assembled'],[x,y,z]))<1e-8);uv=tab['pilot_flat']
   else:uv=[x,station(y,z)]
  elif pid in ['S01-S02','M01','F01','G01','G02']:uv=[y,station(x,z)]
  elif pid.startswith('C'):uv=[x-(s.BoundBox.XMin+s.BoundBox.XMax)/2,station(y,z)]
  elif pid.startswith('T'):uv=[z-(s.BoundBox.ZMin+s.BoundBox.ZMax)/2,station(x,y)]
  elif pid=='I02':uv=[z,station(x,y)]
  else:raise ValueError(pid)
  uv=[uv[0]-ox,uv[1]-oy];best=min(targets,key=lambda c:(c['c'][0]-uv[0])**2+(c['c'][1]-uv[1])**2+((2*c['r'])-bore['diameter'])**2)
  err=math.sqrt(sum((a-b)**2 for a,b in zip(uv,best['c']))+((2*best['r'])-bore['diameter'])**2);assert err<1e-5,(pid,bore,uv,best,err)
  matches.append(dict(assembled_center=bore['center'],axis=axis,diameter=bore['diameter'],source_developed_center=uv,flat_DXF_center=best['c'],mapping_error_mm=err))
 match_report.append(dict(part=pid,matched_circular_cuts=len(matches),maximum_error_mm=max((m['mapping_error_mm'] for m in matches),default=0),holes=matches))
json.dump(match_report,open(root+'/folded-hole-alignment.json','w'),indent=2)
print('FOLDED HOLE MAPPING PASS',sum(r['matched_circular_cuts'] for r in match_report),'bores',max(r['maximum_error_mm'] for r in match_report),'mm maxerror')
