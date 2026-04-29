"""Check each ortho ODB status: last step with data"""
from odbAccess import openOdb
import sys

CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

print(f"{'Case':>10s}  {'ODB(mb)':>8s}  {'LastStep':>10s}  {'PowMax(C)':>9s}  {'GlobMax(C)':>10s}  {'Status'}")
print("=" * 55)

for case in CASES:
    try:
        odb = openOdb(f'ortho_{case}.odb', readOnly=True)
    except:
        print(f"{case:>10s}  {'N/A':>8s}")
        continue
    
    size = 0  # We'll skip size check
    all_steps = list(odb.steps.keys())
    
    # Find last step with frames
    last_frame_step = None
    for sn in reversed(all_steps):
        if odb.steps[sn].frames:
            last_frame_step = sn
            break
    
    if last_frame_step is None:
        print(f"{case:>10s}  {'N/A':>8s}  {'NO FRAMES':>10s}")
        odb.close()
        continue
    
    # Get temp from last frame
    step = odb.steps[last_frame_step]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    
    # Build node info
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
    
    # Check if completed
    status = "RUNNING"
    try:
        with open(f'ortho_{case}.sta', 'r') as sf:
            content = sf.read()
            if 'COMPLETED' in content:
                status = "DONE!"
            elif 'ERROR' in content:
                status = "DONE!"
    except:
        pass
    
    print(f"{case:>10s}  {'-':>8s}  {last_frame_step:>10s}  {pow_max:>9.0f}  {glob_max:>10.0f}  {status}")
    odb.close()
