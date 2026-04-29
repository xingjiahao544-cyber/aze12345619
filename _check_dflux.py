"""Quick check: does DFLUX actually heat powder in P800_V3?"""
from odbAccess import openOdb

odb = openOdb('ortho_P800_V3.odb', readOnly=True)

# Build node map
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

# Check Step-2 frame-by-frame
step = odb.steps['Step-2']
for i, frame in enumerate(step.frames):
    nt = frame.fieldOutputs['NT11']
    pow_max = 0
    glob_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info is None: continue
        if info[0].upper() == 'POWDER-1' and v.data > pow_max:
            pow_max = v.data
        if v.data > glob_max:
            glob_max = v.data
    print(f"  Frame {i}: PowderMax={pow_max:.0f}C, GlobalMax={glob_max:.0f}C")

# Also check Step-7 (last heating step before cooling)
for sn in ['Step-7', 'Step-8', 'Step-9', 'Step-10', 'Step-11']:
    if sn in odb.steps:
        step = odb.steps[sn]
        if not step.frames: continue
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        pow_max = 0
        glob_max = 0
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info is None: continue
            if info[0].upper() == 'POWDER-1' and v.data > pow_max:
                pow_max = v.data
            if v.data > glob_max:
                glob_max = v.data
        print(f"{sn} last frame: PowderMax={pow_max:.0f}C, GlobalMax={glob_max:.0f}C")

odb.close()
