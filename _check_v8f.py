"""Final check of hyb_v8 - constant 1e10, all steps completed"""
from odbAccess import openOdb
odb = openOdb('hyb_v8.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

all_steps = list(odb.steps.keys())
print(f"Total steps: {len(all_steps)}")
print(f"Steps: {all_steps[:15]}...{all_steps[-5:]}")

# Check heating steps only
heating_steps = [s for s in all_steps if s.startswith('Step-') and int(s.split('-')[1]) <= 41]
for sname in heating_steps[::5] + [heating_steps[-1]]:
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    nf = len(step.frames)
    
    tmax = 0
    pow_max = 0
    pow_1400 = 0
    for v in nt.values:
        if v.data > tmax: tmax = v.data
        info = node_info.get(v.nodeLabel)
        if info:
            nm, c = info
            if nm == 'POWDER-1':
                if v.data > pow_max: pow_max = v.data
                if v.data >= 1400: pow_1400 += 1
    
    print(f"  {sname}: Tmax={tmax:.0f}C  PowderTmax={pow_max:.0f}C  P>1400={pow_1400}  Nf={nf}")

# Step-8 detail
step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
hots = []
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if info:
        nm, c = info
        hots.append((v.data, nm, c[0]*1000, c[1]*1000, c[2]*1000))
hots.sort(key=lambda x: -x[0])
print(f"\nStep-8 hottest ALL:")
for t, nm, x, y, z in hots[:10]:
    print(f"  ({nm}) T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

# Last heating step (Step-41)
last_heat = [s for s in all_steps if s.startswith('Step-') and int(s.split('-')[1]) <= 41][-1]
step = odb.steps[last_heat]
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
hots = []
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if info:
        nm, c = info
        hots.append((v.data, nm, c[0]*1000, c[1]*1000, c[2]*1000))
hots.sort(key=lambda x: -x[0])
print(f"\n{last_heat} hottest ALL:")
for t, nm, x, y, z in hots[:10]:
    print(f"  ({nm}) T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

odb.close()
