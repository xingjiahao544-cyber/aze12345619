"""Full 123-step results analysis"""
from odbAccess import openOdb
odb = openOdb('full_inp.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

# Check each layer's last heating step
for sn in ['Step-41', 'Step-82', 'Step-122']:
    if sn not in odb.steps:
        continue
    step = odb.steps[sn]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    nf = len(step.frames)
    
    tmax = 0
    pow_max = 0
    pow_500 = 0
    pow_1400 = 0
    sub_max = 0
    for v in nt.values:
        if v.data > tmax: tmax = v.data
        info = node_info.get(v.nodeLabel)
        if info:
            nm, c = info
            if nm == 'POWDER-1':
                if v.data > pow_max: pow_max = v.data
                if v.data >= 500: pow_500 += 1
                if v.data >= 1400: pow_1400 += 1
            if nm == 'SUBSTRATE-1' and v.data > sub_max:
                sub_max = v.data
    
    print(f"{sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  SubMax={sub_max:.0f}C  P>500={pow_500}  P>1400={pow_1400}  Nf={nf}")

# Step-122 hottest powder detail
step = odb.steps['Step-122']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

hots = []
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if info:
        nm, c = info
        if nm == 'POWDER-1':
            hots.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
hots.sort(key=lambda x: -x[0])
print(f"\nStep-122 hottest powder:")
for t, x, y, z in hots[:10]:
    print(f"  T={t:.0f}C @ X={x:.1f} Y={y:.1f} Z={z:.1f}")

# Also check Layer 2 and Layer 1
for sn in ['Step-41', 'Step-82']:
    step = odb.steps[sn]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    hots = []
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info:
            nm, c = info
            if nm == 'POWDER-1':
                hots.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
    hots.sort(key=lambda x: -x[0])
    print(f"\n{sn} hottest powder:")
    for t, x, y, z in hots[:5]:
        print(f"  T={t:.0f}C @ X={x:.1f} Y={y:.1f} Z={z:.1f}")

odb.close()
