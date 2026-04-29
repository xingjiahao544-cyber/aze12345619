"""Check hyb_v10 - Gap Conductance 1e5"""
from odbAccess import openOdb
import sys

odb = openOdb('hyb_v10.odb', readOnly=True)

# Node -> instance map
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

for sname in ['Step-2', 'Step-4', 'Step-6', 'Step-8']:
    if sname not in odb.steps:
        continue
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    nframes = len(step.frames)
    
    tmax = 0
    powder_max_t = 0
    powder_gt_1400 = 0
    powder_gt_5 = 0
    
    for v in nt.values:
        if v.data > tmax: tmax = v.data
        info = node_info.get(v.nodeLabel)
        if info:
            nm, c = info
            if nm == 'POWDER-1':
                if v.data > powder_max_t: powder_max_t = v.data
                if v.data >= 1400: powder_gt_1400 += 1
                if v.data >= 500: powder_gt_5 += 1
    
    print(f"{sname}: Tmax={tmax:.0f}C  PowderTmax={powder_max_t:.0f}C  P>500={powder_gt_5}  P>1400={powder_gt_1400}  Nf={nframes}")

# Hottest powder detail
step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

hots = []
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if info:
        nm, c = info
        if nm == 'POWDER-1':
            hots.append((v.data, v.nodeLabel, c[0]*1000, c[1]*1000, c[2]*1000))
hots.sort(key=lambda x: -x[0])
print(f"\nStep-8 powder hottest:")
for t, nl, x, y, z in hots[:10]:
    print(f"  N{nl}: T={t:.0f}C @ ({x:.1f},{y:.1f},{z:.1f})")

# Also check global hottest 5
all_hots = []
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if info:
        nm, c = info
        all_hots.append((v.data, v.nodeLabel, nm, c[0]*1000, c[1]*1000, c[2]*1000))
all_hots.sort(key=lambda x: -x[0])
print(f"\nGlobal hottest:")
for t, nl, nm, x, y, z in all_hots[:5]:
    print(f"  N{nl} ({nm}): T={t:.0f}C @ ({x:.1f},{y:.1f},{z:.1f})")

odb.close()
