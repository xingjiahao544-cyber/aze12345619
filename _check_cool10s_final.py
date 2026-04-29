"""full_cool10s 3-layer results!"""
from odbAccess import openOdb
odb = openOdb('full_cool10s.odb', readOnly=True)
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

all_steps = list(odb.steps.keys())
print(f"Steps: {len(all_steps)}")
print(f"Last 10: {all_steps[-10:]}")

for sn in ['Step-41', 'Step-42', 'Step-82', 'Step-83', 'Step-122']:
    if sn in odb.steps:
        step = odb.steps[sn]
        if step.frames:
            f = step.frames[-1]
        else:
            print(f"{sn}: no frames"); continue
        nt = f.frameValue if hasattr(f, 'frameValue') else '?'
        nt11 = f.fieldOutputs['NT11']
        tmax = max(v.data for v in nt11.values)
        pow_max = 0; pow_1400 = 0; pow_500 = 0
        for v in nt11.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0] == 'POWDER-1':
                if v.data > pow_max: pow_max = v.data
                if v.data >= 1400: pow_1400 += 1
                if v.data >= 500: pow_500 += 1
        print(f"{sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  P>500={pow_500}  P>1400={pow_1400}")

# Also check if there's any node > 1400 ANYWHERE
print("\n=== Global check - any node > 1400C? ===")
for sn in all_steps:
    step = odb.steps[sn]
    if not step.frames: continue
    nt = step.frames[-1].fieldOutputs['NT11']
    for v in nt.values:
        if v.data >= 1400:
            info = node_info.get(v.nodeLabel)
            nm = info[0] if info else '?'
            c = info[1] if info else (0,0,0)
            print(f"  {sn}: Node {v.nodeLabel} ({nm}): T={v.data:.0f}C @ ({c[0]*1000:.1f},{c[1]*1000:.1f},{c[2]*1000:.1f})")
            break

odb.close()
