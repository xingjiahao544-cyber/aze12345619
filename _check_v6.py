"""Check hyb_v6 results"""
from odbAccess import openOdb
odb = openOdb('hyb_v6.odb', readOnly=True)

node_inst = {}
for inst_name, inst in odb.rootAssembly.instances.items():
    for n in inst.nodes:
        node_inst[n.label] = inst_name

print(f"Steps: {list(odb.steps.keys())}")

for sname in ['Step-2', 'Step-4', 'Step-6', 'Step-8', 'Step-42']:
    if sname not in odb.steps:
        continue
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    nframes = len(step.frames)
    vals = list(nt.values)
    tmax = max(v.data for v in vals)
    tmin = min(v.data for v in vals)
    
    n_hot = sum(1 for v in vals if v.data >= 1400)
    n_powder_hot = 0
    for v in vals:
        iname = node_inst.get(v.nodeLabel, '')
        if 'POWDER' in iname.upper() and v.data >= 1400:
            n_powder_hot += 1
    
    print(f"  {sname}: Tmax={tmax:>7.1f}C  Tmin={tmin:.1f}C  Nframes={nframes}  Hot>1400={n_hot}  PowderHot={n_powder_hot}")

# Check Step-8 final frame powder hotspot
step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

print("\n=== Step-8 top 10 nodes ===")
coords = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        coords[n.label] = n.coordinates

hots = []
for v in nt.values:
    iname = node_inst.get(v.nodeLabel, '')
    if v.nodeLabel in coords:
        c = coords[v.nodeLabel]
        hots.append((v.data, v.nodeLabel, iname, c[0]*1000, c[1]*1000, c[2]*1000))

hots.sort(key=lambda x: -x[0])
for t, nl, nm, x, y, z in hots[:10]:
    print(f"  Node {nl:>5d} ({nm}): T={t:.0f}C @ X={x:.2f}mm Y={y:.2f}mm Z={z:.2f}mm")

odb.close()
