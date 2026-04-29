"""Compare: duoceng single-layer Step-2 temps"""
from odbAccess import openOdb
odb = openOdb('D:/temp/duoceng/compare_de_hyb_v2.odb', readOnly=True)

step = odb.steps['Step-2']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

print(f"Step-2, {len(step.frames)} frames")

# Check substrate/powder temps
# This is a single-part model (Part-1-1)
coords = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        coords[n.label] = n.coordinates

SUB_Y = 0.003  # duoceng substrate top
tmax = 0
pow_tmax = 0
for v in nt.values:
    if v.data > tmax: tmax = v.data
    if v.nodeLabel in coords:
        y = coords[v.nodeLabel][1]
        if y >= SUB_Y and v.data > pow_tmax:
            pow_tmax = v.data

print(f"Tmax={tmax:.0f}C, PowderTmax={pow_tmax:.0f}C")

# Check last step
last_step = list(odb.steps.keys())[-1]
step = odb.steps[last_step]
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
tmax = max(v.data for v in nt.values)
print(f"\n{last_step}: Tmax={tmax:.0f}C")

odb.close()
