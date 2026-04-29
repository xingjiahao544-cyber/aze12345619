"""Extract all 9 ortho results with latest FOR fixes"""
from odbAccess import openOdb

T_LIQ = 1400.0
CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

print(f"{'Case':>10s}  {'Q(W)':>6s}  {'v':>6s}  {'L1max':>7s}  {'L2max':>7s}  {'L3max':>7s}  {'L1>1400':>8s}  {'L2>1400':>8s}  {'L3>1400':>8s}  {'SubMax':>7s}  {'L3poolW':>7s}  {'L3poolL':>7s}")
print("="*100)

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
    
    def get_powder_max(sn):
        if sn not in odb.steps: return 0, 0
        step = odb.steps[sn]
        if not step.frames: return 0, 0
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        pmax = 0
        p1400 = 0
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0].upper() == 'POWDER-1':
                if v.data > pmax: pmax = v.data
                if v.data >= T_LIQ: p1400 += 1
        return pmax, p1400
    
    # Layer 1: Step-41, Layer 2: Step-82, Layer 3: Step-122
    l1max, l1_1400 = get_powder_max('Step-41')
    l2max, l2_1400 = get_powder_max('Step-82')
    l3max, l3_1400 = get_powder_max('Step-122')
    
    # Substrate max at Step-122
    sub_max = 0
    if 'Step-122' in odb.steps:
        step = odb.steps['Step-122']
        if step.frames:
            nt = step.frames[-1].fieldOutputs['NT11']
            for v in nt.values:
                info = node_info.get(v.nodeLabel)
                if info and info[0].upper() != 'POWDER-1' and v.data > sub_max:
                    sub_max = v.data
    
    # L3 melt pool dimensions
    l3_w = 0; l3_l = 0
    if 'Step-122' in odb.steps:
        step = odb.steps['Step-122']
        if step.frames:
            nt = step.frames[-1].fieldOutputs['NT11']
            hots = []
            for v in nt.values:
                info = node_info.get(v.nodeLabel)
                if info and v.data >= T_LIQ:
                    hots.append((info[1][0]*1000, info[1][1]*1000, info[1][2]*1000))
            if hots:
                xs = [h[0] for h in hots]; zs = [h[2] for h in hots]
                l3_w = max(xs)-min(xs); l3_l = max(zs)-min(zs)
    
    print(f"{case:>10s}  {effq:6.0f}  {speed:6d}  {l1max:7.0f}  {l2max:7.0f}  {l3max:7.0f}  {l1_1400:8d}  {l2_1400:8d}  {l3_1400:8d}  {sub_max:7.0f}  {l3_w:7.2f}  {l3_l:7.2f}")
    
    # Save summary
    with open(f'_ortho_{case}_summary.txt', 'w') as rf:
        rf.write(f"Case: {case}\nP={power}W v={speed}mm/s eta=0.40 Q={effq}W\n")
        rf.write(f"L1_end: Peak={l1max:.0f}C Nodes>1400={l1_1400}\n")
        rf.write(f"L2_end: Peak={l2max:.0f}C Nodes>1400={l2_1400}\n")
        rf.write(f"L3_end: Peak={l3max:.0f}C Nodes>1400={l3_1400} SubMax={sub_max:.0f}C\n")
        if l3_w > 0:
            rf.write(f"L3_meltpool: W={l3_w:.2f}mm L={l3_l:.2f}mm\n")
    
    odb.close()
