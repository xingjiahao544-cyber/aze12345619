"""Check hyb_v9 - FORCED recompile, STEP1_TIME=0.1"""
from odbAccess import openOdb
odb = openOdb('hyb_v9.odb', readOnly=True)

coords = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        coords[n.label] = (inst.name, n.coordinates)

print(f"Steps: {list(odb.steps.keys())[:10]}")

for sname in ['Step-2', 'Step-4', 'Step-6', 'Step-8', 'Step-42']:
    if sname not in odb.steps:
        continue
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    nframes = len(step.frames)
    
    tmax = 0
    powder_max_t = 0
    powder_gt_1400 = 0
    powder_gt_500 = 0
    
    for v in nt.values:
        if v.data > tmax:
            tmax = v.data
        tup = coords.get(v.nodeLabel)
        if tup:
            nm, c = tup
            if nm == 'POWDER-1':
                if v.data > powder_max_t:
                    powder_max_t = v.data
                if v.data >= 1400: powder_gt_1400 += 1
                if v.data >= 500: powder_gt_500 += 1
    
    print(f"  {sname}: Tmax={tmax:.0f}C  PowderTmax={powder_max_t:.0f}C  "
          f">500={powder_gt_500}  >1400={powder_gt_1400}  Nf={nframes}")

# Detail Step-8 powder
step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
hots = []
for v in nt.values:
    tup = coords.get(v.nodeLabel)
    if tup:
        nm, c = tup
        if nm == 'POWDER-1':
            hots.append((v.data, v.nodeLabel, c[0]*1000, c[1]*1000, c[2]*1000))
hots.sort(key=lambda x: -x[0])
print(f"\n=== Step-8: Hottest powder nodes ===")
for t, nl, x, y, z in hots[:10]:
    print(f"  N{nl:>5d}: T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

# Also check non-powder top hots
hots_all = []
for v in nt.values:
    tup = coords.get(v.nodeLabel)
    if tup:
        nm, c = tup
        hots_all.append((v.data, v.nodeLabel, nm, c[0]*1000, c[1]*1000, c[2]*1000))
hots_all.sort(key=lambda x: -x[0])
print(f"\n=== Step-8: Hottest ALL nodes ===")
for t, nl, nm, x, y, z in hots_all[:5]:
    print(f"  N{nl:>5d} ({nm}): T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

odb.close()
