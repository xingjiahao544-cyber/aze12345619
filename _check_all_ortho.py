"""Check all ortho ODBs - find last step and peak temperatures"""
from odbAccess import openOdb
import sys

T_LIQ = 1400.0
CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

print(f"{'Case':>12s}  {'P(W)':>6s}  {'v(mm/s)':>8s}  {'EffQ':>6s}  {'LastStep':>10s}  {'Nsteps':>7s}  {'Tmax(C)':>8s}  {'Pmax(C)':>8s}  {'P>1400':>7s}  {'Smax(C)':>8s}  {'S>1400':>7s}")
print("=" * 95)

for case in CASES:
    parts = case.split('_')
    power = int(parts[0].replace('P', ''))
    speed = int(parts[1].replace('V', ''))
    effq = power * 0.4

    try:
        odb = openOdb(f'ortho_{case}.odb', readOnly=True)
    except:
        print(f"{case:>12s}  {power:6d}  {speed:8d}  {effq:6.0f}  {'NO ODB':>10s}")
        continue

    # Build node map
    node_info = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_info[n.label] = (inst.name, n.coordinates)

    all_steps = list(odb.steps.keys())
    
    # Find last step with frames
    last_step = None
    for sn in reversed(all_steps):
        step = odb.steps[sn]
        if step.frames:
            last_step = sn
            break
    
    if last_step is None:
        print(f"{case:>12s}  {power:6d}  {speed:8d}  {effq:6.0f}  {'NO FRAMES':>10s}")
        odb.close()
        continue
    
    step = odb.steps[last_step]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']

    tmax_global = max(v.data for v in nt.values)
    
    # Powder stats
    pow_tmax = 0
    pow_1400 = 0
    sub_tmax = 0
    sub_1400 = 0
    
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info is None:
            continue
        iname = info[0]
        y = info[1][1]
        if iname.upper() == 'POWDER-1':
            if v.data > pow_tmax:
                pow_tmax = v.data
            if v.data >= T_LIQ:
                pow_1400 += 1
        else:
            if v.data > sub_tmax:
                sub_tmax = v.data
            if v.data >= T_LIQ:
                sub_1400 += 1

    print(f"{case:>12s}  {power:6d}  {speed:8d}  {effq:6.0f}  {last_step:>10s}  {len(all_steps):7d}  {tmax_global:8.0f}  {pow_tmax:8.0f}  {pow_1400:7d}  {sub_tmax:8.0f}  {sub_1400:7d}")

    odb.close()
