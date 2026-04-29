"""Check each ortho ODB status: last step with data"""
from odbAccess import openOdb

CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

print("Case       Step   PowMax  GlobMax  Status")
print("="*45)

for case in CASES:
    try:
        odb = openOdb(f'ortho_{case}.odb', readOnly=True)
    except:
        print(f"{case:>10s}  NO ODB")
        continue

    all_steps = list(odb.steps.keys())
    last_frame_step = None
    for sn in reversed(all_steps):
        if odb.steps[sn].frames:
            last_frame_step = sn
            break

    if last_frame_step is None:
        print(f"{case:>10s}  NO FRAMES")
        odb.close()
        continue

    step = odb.steps[last_frame_step]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']

    node_info = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_info[n.label] = (inst.name, n.coordinates)

    pow_max = 0
    glob_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0].upper() == 'POWDER-1' and v.data > pow_max:
            pow_max = v.data
        if v.data > glob_max:
            glob_max = v.data

    status = "running"
    try:
        with open(f'ortho_{case}.sta', 'r') as sf:
            content = sf.read()
            if 'COMPLETED' in content:
                status = "DONE!"
    except:
        pass

    print(f"{case:>10s}  {last_frame_step:>10s}  {pow_max:>6.0f}  {glob_max:>6.0f}  {status}")
    odb.close()
