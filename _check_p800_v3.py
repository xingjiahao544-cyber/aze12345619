"""Fresh check P800_V3 after new FOR fix"""
from odbAccess import openOdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

odb = openOdb('ortho_P800_V3.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

all_steps = list(odb.steps.keys())
print(f"Total steps: {len(all_steps)}")

for sn in ['Step-2', 'Step-10', 'Step-20', 'Step-30', 'Step-41']:
    if sn not in odb.steps: continue
    step = odb.steps[sn]
    if not step.frames: continue
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    pow_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0].upper() == 'POWDER-1' and v.data > pow_max:
            pow_max = v.data
    print(f"{sn}: PowderMax={pow_max:.0f}C")

# Check Layer 2 and 3
for sn in ['Step-43', 'Step-50', 'Step-82', 'Step-84', 'Step-100', 'Step-122']:
    if sn not in odb.steps: continue
    step = odb.steps[sn]
    if not step.frames: continue
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    pow_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0].upper() == 'POWDER-1' and v.data > pow_max:
            pow_max = v.data
    print(f"{sn}: PowderMax={pow_max:.0f}C")

# Check Step-122 (Layer 3 last step) top 5
if 'Step-122' in odb.steps:
    step = odb.steps['Step-122']
    if step.frames:
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        hots = []
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0].upper() == 'POWDER-1':
                c = info[1]
                hots.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
        hots.sort(key=lambda x: -x[0])
        print("\nStep-122 powder top 5:")
        for t, x, y, z in hots[:5]:
            print(f"  T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

odb.close()
