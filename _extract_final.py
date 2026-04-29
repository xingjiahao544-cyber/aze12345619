"""Extract ortho results for completed cases"""
from odbAccess import openOdb
import sys

T_LIQ = 1400.0
CASES = ['P1200_V3', 'P1200_V5', 'P1200_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8']

print(f"{'Case':>10s}  {'Q(W)':>6s}  {'v':>5s}  {'L1max':>7s}  {'L2max':>7s}  {'L3max':>7s}  {'L1n':>5s}  {'L2n':>5s}  {'L3n':>5s}  {'SubMax':>7s}  {'L3W(mm)':>8s}  {'L3L(mm)':>8s}")
print("="*95)

for case in CASES:
    parts = case.split('_')
    power = int(parts[0].replace('P', ''))
    speed = int(parts[1].replace('V', ''))
    effq = power * 0.4
    
    odb = openOdb(f'ortho_{case}.odb', readOnly=True)
    
    node_info = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_info[n.label] = (inst.name, n.coordinates)
    
    def analyze_step(sn):
        if sn not in odb.steps: return 0, 0, []
        step = odb.steps[sn]
        if not step.frames: return 0, 0, []
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        pmax = 0; pn = 0; hots = []
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0].upper() == 'POWDER-1':
                if v.data > pmax: pmax = v.data
                if v.data >= T_LIQ:
                    pn += 1
                    hots.append((info[1][0]*1000, info[1][2]*1000))
        return pmax, pn, hots
    
    l1max, l1n, _ = analyze_step('Step-41')
    l2max, l2n, _ = analyze_step('Step-82')
    l3max, l3n, l3hots = analyze_step('Step-122')
    
    # Substrate max (Step-122)
    sub_max = 0
    if 'Step-122' in odb.steps:
        step = odb.steps['Step-122']
        if step.frames:
            nt = step.frames[-1].fieldOutputs['NT11']
            for v in nt.values:
                info = node_info.get(v.nodeLabel)
                if info and info[0].upper() != 'POWDER-1' and v.data > sub_max:
                    sub_max = v.data
    
    l3w = max(h[0] for h in l3hots) - min(h[0] for h in l3hots) if l3hots else 0
    l3l = max(h[1] for h in l3hots) - min(h[1] for h in l3hots) if l3hots else 0
    
    print(f"{case:>10s}  {effq:6.0f}  {speed:5d}  {l1max:7.0f}  {l2max:7.0f}  {l3max:7.0f}  {l1n:5d}  {l2n:5d}  {l3n:5d}  {sub_max:7.0f}  {l3w:8.2f}  {l3l:8.2f}")
    
    # Save summary
    with open(f'_ortho_{case}_summary.txt', 'w') as rf:
        rf.write(f"Case: {case}\nP={power}W v={speed}mm/s eta=0.40 Q={effq}W\n")
        rf.write(f"L1: Peak={l1max:.0f}C Melts={l1n} nodes\n")
        rf.write(f"L2: Peak={l2max:.0f}C Melts={l2n} nodes\n")
        rf.write(f"L3: Peak={l3max:.0f}C Melts={l3n} nodes SubPeak={sub_max:.0f}C\n")
        if l3hots:
            rf.write(f"L3_Pool: W={l3w:.2f}mm L={l3l:.2f}mm\n")
    
    odb.close()
