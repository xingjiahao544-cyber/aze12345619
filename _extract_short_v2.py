"""
Extract short INP results for duoceng3 orthogonal experiment
Uses Step-8 (last heating step) for comparison
"""
from odbAccess import openOdb
import sys

CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

T_LIQ = 1400.0

print("="*90)
print("Hybrid Heat Source 3x3 Orthogonal Experiment (eta=0.40, short INP)")
print("="*90)
print(f"{'Case':>12s}  {'P(W)':>6s}  {'v(mm/s)':>8s}  {'Q(W)':>6s}  {'Tmax(C)':>8s}  {'Nhot':>5s}  {'W(mm)':>6s}  {'D(mm)':>6s}  {'L(mm)':>6s}  {'IW(mm)':>6s}")
print("-"*92)

for case in CASES:
    parts = case.split('_')
    power = int(parts[0].replace('P',''))
    speed = int(parts[1].replace('V',''))
    q = power * 0.4
    
    odb = openOdb(f'short_{case}.odb', readOnly=True)
    
    # Build node coords
    node_coords = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_coords[(inst.name, n.label)] = (
                n.coordinates[0], n.coordinates[1], n.coordinates[2])
    
    node_inst = {}
    for inst in odb.rootAssembly.instances.values():
        for el in inst.elements:
            for nl in el.connectivity:
                node_inst[nl] = inst.name
    
    # Step-8 = last heating step  
    step = odb.steps['Step-8']
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    ninc = len(step.frames)
    
    tmax = max(v.data for v in nt.values)
    
    # Melt pool
    hot = []
    sub_hot = []
    for v in nt.values:
        iname = node_inst.get(v.nodeLabel, list(node_coords.keys())[0][0])
        key = (iname, v.nodeLabel)
        if key in node_coords:
            c = node_coords[key]
            if v.data >= T_LIQ:
                hot.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
                # Substrate Y < SUB_D = 4.8mm
                if c[1] < 0.0048:
                    sub_hot.append(v.data)
    
    sub_tmax = max(sub_hot) if sub_hot else 0
    
    if hot:
        xs = [h[1] for h in hot]; ys = [h[2] for h in hot]; zs = [h[3] for h in hot]
        w = max(xs)-min(xs); d = max(ys)-min(ys); l = max(zs)-min(zs)
        
        # Interface width at Y = SUB_D (4.8mm)
        interface_x = [h[1] for h in hot if abs(h[2] - 4.8) < 0.15]
        iw = max(interface_x)-min(interface_x) if interface_x else 0
        
        print(f"{case:>12s}  {power:6d}  {speed:8d}  {q:6.0f}  {tmax:8.1f}  {len(hot):5d}  {w:6.3f}  {d:6.3f}  {l:6.3f}  {iw:6.3f}")
    else:
        print(f"{case:>12s}  {power:6d}  {speed:8d}  {q:6.0f}  {tmax:8.1f}      0      -      -      -      -")
    
    # Save individual result
    with open(f'D:\\temp\\duoceng3\\_{case}_result.txt', 'w') as rf:
        rf.write(f"{case}: Q={q:.0f}W v={speed}mm/s | Tmax={tmax:.0f}C | SubTmax={sub_tmax:.0f}C | "
                 f"Pool:N={len(hot)} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm IW={iw:.3f}mm | Step=Step-8\n")
        rf.write(f"Q={q:.0f}W v={speed}mm/s\n")
        rf.write(f"PeakT={tmax:.0f}C\n")
        rf.write(f"MaxPowderT={tmax:.0f}C MaxSubT={sub_tmax:.0f}C\n")
        if hot:
            rf.write(f"MeltPool:N={len(hot)} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm IW={iw:.3f}mm\n")
        rf.write(f"LastStep=Step-8\n")
    
    odb.close()

print("-"*92)
