"""Check hyb_v8 - constant 1e10 test"""
from odbAccess import openOdb
odb = openOdb('hyb_v8.odb', readOnly=True)

for sname in ['Step-8', 'Step-20', 'Step-26']:
    if sname not in odb.steps:
        continue
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    vals = list(nt.values)
    tmax = max(v.data for v in vals)
    
    # Find powder nodes through coordinates
    coords = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            coords[n.label] = (inst.name, n.coordinates)
    
    pow_temps = [v.data for v in vals if coords.get(v.nodeLabel,('',))[0]=='POWDER-1']
    pow_tmax = max(pow_temps) if pow_temps else 0
    pow_n_gt_500 = sum(1 for t in pow_temps if t>=500)
    
    print(f"{sname}: Tmax={tmax:.0f}C  PowderTmax={pow_tmax:.0f}C  Powder>500C={pow_n_gt_500}")

# Detailed powder check
step = odb.steps['Step-26']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
coords = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        coords[n.label] = (inst.name, n.coordinates)

powder_hot = []
for v in nt.values:
    if v.nodeLabel in coords:
        nm, c = coords[v.nodeLabel]
        if nm == 'POWDER-1':
            powder_hot.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000, v.nodeLabel))

powder_hot.sort(key=lambda x: -x[0])
print(f"\nPowder nodes in Step-26: {len(powder_hot)} total")
print("Top 10:")
for t, x, y, z, nl in powder_hot[:10]:
    print(f"  N{nl:>5d}: T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

odb.close()
