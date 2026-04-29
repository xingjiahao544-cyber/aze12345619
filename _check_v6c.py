"""Check hyb_v6c results - Dflux on Powder-1.Set-Kill"""
from odbAccess import openOdb
odb = openOdb('hyb_v6c.odb', readOnly=True)

node_inst = {}
for inst_name, inst in odb.rootAssembly.instances.items():
    for n in inst.nodes:
        node_inst[n.label] = inst_name

print(f"Steps in ODB: {list(odb.steps.keys())[:12]}...")

for sname in ['Step-2', 'Step-4', 'Step-6', 'Step-8', 'Step-9']:
    if sname not in odb.steps:
        continue
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    nframes = len(step.frames)
    vals = list(nt.values)
    tmax = max(v.data for v in vals)
    
    n_powder_hot = 0
    n_powder_warm = 0
    for v in vals:
        iname = node_inst.get(v.nodeLabel, '')
        if 'POWDER' in iname:
            if v.data >= 1400: n_powder_hot += 1
            if v.data >= 500: n_powder_warm += 1
    
    print(f"  {sname}: Tmax={tmax:>7.1f}C  Nframes={nframes}  Powder>500C={n_powder_warm}  Powder>1400C={n_powder_hot}")

# Check powder coords
print("\n=== Powder temperature distribution (Step-8) ===")
step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

coords = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        coords[n.label] = n.coordinates

hots = []
for v in nt.values:
    iname = node_inst.get(v.nodeLabel, '')
    if 'POWDER' in iname and v.nodeLabel in coords:
        c = coords[v.nodeLabel]
        hots.append((v.data, v.nodeLabel, c[0]*1000, c[1]*1000, c[2]*1000))

hots.sort(key=lambda x: -x[0])
print(f"Total powder nodes with NT11: {len(hots)}")
for t, nl, x, y, z in hots[:15]:
    print(f"  Node {nl:>5d}: T={t:.0f}C @ X={x:.2f}mm Y={y:.2f}mm Z={z:.2f}mm")

print(f"\nHottest 3 nodes overall:")
all_hots = []
for v in nt.values:
    if v.nodeLabel in coords:
        c = coords[v.nodeLabel]
        all_hots.append((v.data, v.nodeLabel, node_inst.get(v.nodeLabel,''), c[0]*1000, c[1]*1000, c[2]*1000))
all_hots.sort(key=lambda x: -x[0])
for t, nl, nm, x, y, z in all_hots[:3]:
    print(f"  Node {nl:>5d} ({nm}): T={t:.0f}C @ X={x:.2f}mm Y={y:.2f}mm Z={z:.2f}mm")

# Print Z position check  
print("\n=== Z pos calc ===")
SCAN_SPEED=0.005; STEP1_TIME=10.0
for step_n in [2, 8, 9]:
    heat_time = (step_n-2)*0.12 + 0.12  # end of step
    z = SCAN_SPEED * heat_time
    print(f"  Step-{step_n} end: HEAT_TIME={heat_time}s, Z={z*1000:.2f}mm")

odb.close()
