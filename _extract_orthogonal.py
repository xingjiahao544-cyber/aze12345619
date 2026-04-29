"""
Extract duoceng3 short INP results using cmd.exe /c "abaqus cae noGUI=..."
This script runs inside Abaqus Python
"""
from odbAccess import openOdb

CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

T_LIQ = 1400.0

print("=" * 100)
print("Hybrid Coupled Heat Source 3x3 Orthogonal Experiment (eta=0.40)")
print("Short INP - Layer 1, first 8 heating steps (Step-2~9) + cooling (Step-42)")
print("Extraction at Step-8 (last heating step)")
print("=" * 100)
print(f"{'Case':>12s}  {'P(W)':>6s}  {'v':>4s}  {'EffQ':>6s}  {'Tmax(C)':>8s}  {'SubTmax(C)':>10s}  {'Nhot':>5s}  {'W(mm)':>7s}  {'D(mm)':>7s}  {'L(mm)':>7s}  {'IW(mm)':>7s}  {'Grad(C/mm)':>11s}")
print("-" * 105)

for case in CASES:
    parts = case.split('_')
    power = int(parts[0].replace('P', ''))
    speed = int(parts[1].replace('V', ''))
    effq = power * 0.4
    
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
    
    # Max temperature and location
    tmax_val = -1
    tmax_node = None
    tmax_coord = None
    for v in nt.values:
        if v.data > tmax_val:
            tmax_val = v.data
            tmax_node = v.nodeLabel
    
    if tmax_node:
        iname = node_inst.get(tmax_node)
        tmax_coord = node_coords.get((iname, tmax_node), (0,0,0))
    
    # Melt pool analysis
    hot = []
    sub_hot_temps = []
    sub_y = 0.0048  # substrate surface Y
    
    for v in nt.values:
        iname = node_inst.get(v.nodeLabel)
        key = (iname, v.nodeLabel)
        if key in node_coords:
            c = node_coords[key]
            if v.data >= T_LIQ:
                hot.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
                if c[1] < sub_y:
                    sub_hot_temps.append(v.data)
    
    sub_tmax = max(sub_hot_temps) if sub_hot_temps else 0
    
    if hot and len(hot) > 2:
        xs = [h[1] for h in hot]; ys = [h[2] for h in hot]; zs = [h[3] for h in hot]
        w = max(xs) - min(xs); d = max(ys) - min(ys); l = max(zs) - min(zs)
        
        # Interface width at Y = SUB_D * 1000 = 4.8mm
        interface_x = [h[1] for h in hot if abs(h[2] - 4.8) < 0.15]
        iw = max(interface_x) - min(interface_x) if interface_x else 0
        
        # Temperature gradient: find nodes near T_LIQ in Z direction
        tmax_z = max(zs)
        grad_nodes = [(h[0], h[3]) for h in hot if T_LIQ - 30 < h[0] < T_LIQ + 30]
        if grad_nodes and tmax_val > T_LIQ:
            avg_grad = abs(tmax_val - T_LIQ) / (tmax_z - min(z for _,z in grad_nodes)) if (tmax_z - min(z for _,z in grad_nodes)) > 0.3 else 0
        else:
            avg_grad = 0
    else:
        w = d = l = iw = avg_grad = 0
    
    print(f"{case:>12s}  {power:6d}  {speed:4d}  {effq:6.0f}  {tmax_val:8.1f}  {sub_tmax:10.0f}  {len(hot):5d}  {w:7.3f}  {d:7.3f}  {l:7.3f}  {iw:7.3f}  {avg_grad:11.1f}")
    
    # Save result
    with open(f'D:\\temp\\duoceng3\\_{case}_result.txt', 'w') as rf:
        rf.write(f"{case}: Q={effq:.0f}W v={speed}mm/s | Tmax={tmax_val:.0f}C @({tmax_coord[0]*1000:.2f},{tmax_coord[1]*1000:.2f},{tmax_coord[2]*1000:.2f})mm | SubTmax={sub_tmax:.0f}C | Pool:N={len(hot)} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm IW={iw:.3f}mm G={avg_grad:.0f}C/mm | Step=Step-8\n")
        rf.write(f"Q={effq:.0f}W v={speed}mm/s\n")
        rf.write(f"PeakT={tmax_val:.0f}C\n")
        rf.write(f"MaxPowderT={tmax_val:.0f}C MaxSubT={sub_tmax:.0f}C\n")
        if hot:
            rf.write(f"MeltPool:N={len(hot)} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm IW={iw:.3f}mm G={avg_grad:.0f}C/mm\n")
        rf.write(f"LastStep=Step-8\n")
    
    odb.close()

print("-" * 105)
print("\nLegend: Tmax=peak temp, SubTmax=substrate peak temp, Nhot=melt pool nodes")
print("W=width, D=depth, L=length, IW=interface width, Grad=temperature gradient")
