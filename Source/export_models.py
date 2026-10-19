# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Run in a FreeCAD Python environment. Regenerated STEP files are uncoloured.
The distributed assembly STEP is coloured; geometry is identical.
--panels-only leaves the existing assembly STEP untouched.
"""
import sys,os,shutil,json
exe=shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
if exe:sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))),'lib'))
import FreeCAD as A,Part
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=A.openDocument(ROOT+'/CAD/Sheet Metal PC Case.FCStd')
leaves=[o for o in d.Objects if not hasattr(o,'Group') and hasattr(o,'Shape') and len(o.Shape.Solids)]
panels=[o for o in leaves if 'PartID' in o.PropertiesList]
sets=[('Sheet Metal PC Case Sheet Parts',panels)]
if '--panels-only' not in sys.argv:sets.insert(0,('Sheet Metal PC Case Assembly',leaves))
results=[]
for name,objects in sets:
 path=ROOT+'/CAD/'+name+'.step';Part.export(objects,path);rt=Part.read(path)
 bb=A.BoundBox();volume=0;solids=0
 for o in objects:bb.add(o.Shape.BoundBox);volume+=o.Shape.Volume;solids+=len(o.Shape.Solids)
 a=[bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax];b=rt.BoundBox;c=[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
 errors=[abs(x-y) for x,y in zip(a,c)];dv=abs(volume-rt.Volume)
 assert all(o.Shape.isValid() for o in objects) and rt.isValid()
 assert len(rt.Solids)==solids and max(errors)<.001 and dv<.001,(name,solids,len(rt.Solids),errors,dv)
 results.append(dict(file=os.path.relpath(path,ROOT),objects=len(objects),solids=solids,volume_mm3=volume,roundtrip_volume_error_mm3=dv,bounds_mm=a,maximum_bound_error_mm=max(errors),passed=True,colour='uncoloured'))
json.dump(results,open(ROOT+'/model-export-check.json','w'),indent=2)
print(json.dumps(results,indent=2))
