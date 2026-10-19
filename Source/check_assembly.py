# SPDX-License-Identifier: CERN-OHL-P-2.0
import sys,os,shutil,json,math
exe=shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
if exe:sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))),'lib'))
import FreeCAD as A,Part
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));d=A.openDocument(root+'/CAD/Sheet Metal PC Case.FCStd')
leaves=[o for o in d.Objects if not hasattr(o,'Group') and hasattr(o,'Shape') and len(o.Shape.Solids)>0];manufactured=[o for o in leaves if 'PartID' in o.PropertiesList];refs=[o for o in leaves if o not in manufactured]
collisions=[]
for i,a in enumerate(manufactured):
 for b in manufactured[i+1:]+refs:
  if not a.Shape.BoundBox.intersect(b.Shape.BoundBox):continue
  vol=a.Shape.common(b.Shape).Volume
  if vol>0.001:collisions.append(dict(a=a.Label,b=b.Label,volume_mm3=vol,structural_pair=b in manufactured))
print(json.dumps(collisions,indent=2),flush=True)
bb=A.BoundBox()
for o in leaves:bb.add(o.Shape.BoundBox)
out=dict(objects=len(leaves),solids=sum(len(o.Shape.Solids) for o in leaves),manufactured_instances=len(manufactured),manufactured_valid_single_solids=all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in manufactured),invalid=[o.Label for o in leaves if not o.Shape.isValid()],bounds=[bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax],size=[bb.XLength,bb.YLength,bb.ZLength],manufactured_intersections=collisions)
intentional=[c for c in collisions if c['a'].startswith('M03 ') and c['b'].startswith(('PCI nutstrip end M3','PCI retention M3')) and not c['structural_pair']]
unexpected=[c for c in collisions if c not in intentional]
out['intentional_thread_intersections']=intentional
out['unexpected_intersections']=unexpected
out['passed']=not unexpected and not out['invalid'] and out['manufactured_valid_single_solids']
json.dump(out,open(root+'/assembly-check.json','w'),indent=2)
print('SUMMARY',len(leaves),'objects',out['solids'],'solids',out['size'],flush=True)

assert out['passed'],out
