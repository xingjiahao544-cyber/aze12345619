"""Diagnose P800_V3 DFLUX - does it heat powder?"""
from odbAccess import openOdb

odb = openOdb('ortho_P800_V3.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

# Step-2 frame by frame
step = odb.steps['Step-2']
print("=== Step-2 frame by frame ===")
for i, frame in enumerate(step.frames):
    nt = frame.fieldOutputs['NT11']
    pow_max = 0
    glb_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info is None: continue
        if info[0].upper() == 'POWDER-1' and v.data > pow_max:
            pow_max = v.data
        if v.data > glb_max:
            glb_max = v.data
    print(f"  Frame {i}: PowderMax={pow_max:.0f}C, GlobalMax={glb_max:.0f}C")

# Check several steps
for sn in ['Step-3', 'Step-5', 'Step-10', 'Step-20', 'Step-30', 'Step-40']:
    if sn not in odb.steps: continue
    step = odb.steps[sn]
    if not step.frames: continue
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    pow_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0].upper() == 'POWDER-1' and v.data > pow_max:
            pow_max = v.data
    print(f"{sn}: PowderMax={pow_max:.0f}C")

# Check Step-41 (Layer 1 last step)
for sn in ['Step-41', 'Step-82', 'Step-122']:
    if sn not in odb.steps: continue
    step = odb.steps[sn]
    if not step.frames: continue
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    hots = []
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0].upper() == 'POWDER-1':
            hots.append((v.data, info[1][0]*1000, info[1][1]*1000, info[1][2]*1000))
    hots.sort(key=lambda x: -x[0])
    print(f"\n{sn}: Top 5 powder nodes:")
    for t, x, y, z in hots[:5]:
        print(f"  T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

odb.close()
