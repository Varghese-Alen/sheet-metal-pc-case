# SPDX-License-Identifier: CERN-OHL-P-2.0
import sys,os,shutil,json
exe=shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
if exe:sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))),'lib'))
import FreeCAD as A,Part
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));d=A.openDocument(root+'/CAD/Sheet Metal PC Case.FCStd')
refs=[o for o in d.Objects if not hasattr(o,'Group') and hasattr(o,'Shape') and len(o.Shape.Solids)>0 and 'PartID' not in o.PropertiesList]
cs=[]
for i,a in enumerate(refs):
 for b in refs[i+1:]:
  if not a.Shape.BoundBox.intersect(b.Shape.BoundBox):continue
  v=a.Shape.common(b.Shape).Volume
  if v>.001:cs.append([a.Label,b.Label,v])
json.dump(cs,open(root+'/reference-intersections.json','w'),indent=2);print(json.dumps(cs,indent=2))
