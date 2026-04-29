"""full_v11 trend"""
from odbAccess import openOdb
odb = openOdb('full_v11.odb', readOnly=True)
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)
for sn in ['Step-20', 'Step-25', 'Step-30', 'Step-35', 'Step-38', 'Step-39', 'Step-40']:
    if sn in odb.steps:
        step = odb.steps[sn]
        if step.frames:
            f = step.frames[-1]
            nt = f.fieldOutputs['NT11']
            tmax = max(v.data for v in nt.values)
            pow_max = 0; pow_1400 = 0
            for v in nt.values:
                info = node_info.get(v.nodeLabel)
                if info and info[0] == 'POWDER-1':
                    if v.data > pow_max: pow_max = v.data
                    if v.data >= 1400: pow_1400 += 1
            print(f"{sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  P>1400={pow_1400}")

# Step-40 hottest powder
step = odb.steps['Step-40']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
hots = []
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if info and info[0] == 'POWDER-1':
        c = info[1]
        hots.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
hots.sort(key=lambda x: -x[0])
print(f"\nStep-40 hottest powder:")
for t, x, y, z in hots[:10]:
    print(f"  T={t:.0f}C @ X={x:.1f} Y={y:.1f} Z={z:.1f}")

odb.close()
