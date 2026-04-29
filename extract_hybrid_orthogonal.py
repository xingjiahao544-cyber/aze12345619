"""
Extract orthogonal experiment results for hybrid heat source in duoceng3
Each case: 8 heating steps (Layer 1 Z1-Z7) + 1 cooling step
Use Step-8 (last heating step, Z7 position) for comparison
"""
from odbAccess import openOdb
import sys

CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

T_LIQ = 1400.0

print("="*90)
print("Hybrid Heat Source 3x3 Orthogonal Experiment Results (duoceng3, 7-layer test)")
print("="*90)
print(f"{'Case':>12s}  {'P(W)':>6s}  {'v(mm/s)':>8s}  {'Q(W)':>6s}  {'Tmax(C)':>8s}  {'Nhot':>5s}  {'Ninc':>5s}  {'W(mm)':>6s}  {'D(mm)':>6s}  {'L(mm)':>6s}")
print("-"*90)

for case in CASES:
    parts = case.split('_')
    power = int(parts[0].replace('P',''))
    speed = int(parts[1].replace('V',''))
    q = power * 0.4  # eta=0.4
    
    odb = openOdb(f'hybrid_{case}.odb', readOnly=True)
    
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
    for v in nt.values:
        iname = node_inst.get(v.nodeLabel, list(node_coords.keys())[0][0])
        key = (iname, v.nodeLabel)
        if key in node_coords:
            c = node_coords[key]
            if v.data >= T_LIQ:
                hot.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
    
    if hot:
        xs = [h[1] for h in hot]; ys = [h[2] for h in hot]; zs = [h[3] for h in hot]
        w = max(xs)-min(xs); d = max(ys)-min(ys); l = max(zs)-min(zs)
        print(f"{case:>12s}  {power:6d}  {speed:8d}  {q:6.0f}  {tmax:8.1f}  {len(hot):5d}  {ninc:5d}  {w:6.3f}  {d:6.3f}  {l:6.3f}")
    else:
        print(f"{case:>12s}  {power:6d}  {speed:8d}  {q:6.0f}  {tmax:8.1f}      0  {ninc:5d}      -      -      -")
    
    odb.close()
