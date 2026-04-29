"""Check full_inp progress - just Step-30"""
from odbAccess import openOdb
odb = openOdb('full_inp.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

# Check Step-30
step = odb.steps['Step-30']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
nf = len(step.frames)

tmax = 0
pow_max = 0
pow_1400 = 0
pow_500 = 0
for v in nt.values:
    if v.data > tmax: tmax = v.data
    info = node_info.get(v.nodeLabel)
    if info:
        nm, c = info
        if nm == 'POWDER-1':
            if v.data > pow_max: pow_max = v.data
            if v.data >= 1400: pow_1400 += 1
            if v.data >= 500: pow_500 += 1

print(f"Step-30: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  P>500={pow_500}  P>1400={pow_1400}  Nf={nf}")

# Check a few earlier steps too
for sn in ['Step-5', 'Step-10', 'Step-15', 'Step-20', 'Step-25']:
    if sn not in odb.steps:
        continue
    step = odb.steps[sn]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    tmax = max(v.data for v in nt.values)
    pow_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0] == 'POWDER-1' and v.data > pow_max:
            pow_max = v.data
    print(f"  {sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C")

odb.close()
