"""FINAL check - cooling time fix version"""
from odbAccess import openOdb
odb = openOdb('ortho_P1200_V5.odb', readOnly=True)
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

all_steps = list(odb.steps.keys())
print(f"Steps: {len(all_steps)}")

for sn in ['Step-41', 'Step-42', 'Step-82', 'Step-83', 'Step-122']:
    if sn in odb.steps:
        step = odb.steps[sn]
        if step.frames:
            f = step.frames[-1]
        else:
            print(f"{sn}: no frames"); continue
        nt = f.fieldOutputs['NT11']
        tmax = max(v.data for v in nt.values)
        pow_max = 0; pow_1400 = 0; pow_500 = 0
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0] == 'POWDER-1':
                if v.data > pow_max: pow_max = v.data
                if v.data >= 1400: pow_1400 += 1
                if v.data >= 500: pow_500 += 1
        print(f"{sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  P>500={pow_500}  P>1400={pow_1400}")

# Check Layer 2 and 3 in detail
for sn in ['Step-82', 'Step-122']:
    step = odb.steps[sn]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    hots = []
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0] == 'POWDER-1':
            c = info[1]
            hots.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
    hots.sort(key=lambda x: -x[0])
    print(f"\n{sn} powder top 5:")
    for t, x, y, z in hots[:5]:
        marker = " ***MELT" if t >= 1400 else ""
        print(f"  T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}{marker}")

odb.close()
