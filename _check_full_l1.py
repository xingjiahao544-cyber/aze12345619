"""Check full_inp at Layer 1 completion"""
from odbAccess import openOdb
odb = openOdb('full_inp.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

# Check Step-41 (last heating of Layer 1)
for sn in ['Step-36', 'Step-38', 'Step-40', 'Step-41', 'Step-42']:
    if sn not in odb.steps:
        continue
    step = odb.steps[sn]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    
    tmax = 0
    pow_max = 0
    pow_500 = 0
    pow_1400 = 0
    for v in nt.values:
        if v.data > tmax: tmax = v.data
        info = node_info.get(v.nodeLabel)
        if info:
            nm, c = info
            if nm == 'POWDER-1':
                if v.data > pow_max: pow_max = v.data
                if v.data >= 500: pow_500 += 1
                if v.data >= 1400: pow_1400 += 1
    
    print(f"{sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  P>500={pow_500}  P>1400={pow_1400}")

# Detail Step-41 powder
step = odb.steps['Step-41']
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
print(f"\nStep-41 hottest powder:")
for t, nl, x, y, z in hots[:5]:
    print(f"  N{nl}: T={t:.0f}C @ X={x:.1f} Y={y:.1f} Z={z:.1f}")

# Check Step-42 (cool)
step = odb.steps['Step-42']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
pow_max = 0
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if info and info[0] == 'POWDER-1' and v.data > pow_max:
        pow_max = v.data
tmax = max(v.data for v in nt.values)
print(f"\nStep-42 (cool): Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C")

odb.close()
