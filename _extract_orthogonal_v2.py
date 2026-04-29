"""
Extract duoceng3 short INP results - FIXED version
Only analyze melt pool in powder region (Y >= 4.8mm, the powder track)
Substrate max temperature reported separately
"""
from odbAccess import openOdb

CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

T_LIQ = 1400.0    # 316L liquidus
SUB_Y = 0.0048    # substrate top / powder bottom Y in meters

print("=" * 110)
print("Hybrid Coupled Heat Source 3x3 Orthogonal Experiment (eta=0.40, short INP)")
print("Melt pool analyzed in powder region only (Y >= 4.8mm)")
print("Step-8 (last heating step)")
print("=" * 110)
print(f"{'Case':>12s}  {'P(W)':>6s}  {'v':>4s}  {'EffQ':>6s}  {'Tmax(C)':>8s}  {'SubTmax(C)':>10s}  {'Nhot':>5s}  {'W(mm)':>7s}  {'D(mm)':>7s}  {'L(mm)':>7s}  {'IW(mm)':>7s}  {'Grad(C/mm)':>11s}")
print("-" * 110)

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
    
    # Analyze all nodes
    tmax_powder = -1
    tmax_sub = -1
    hot_powder = []  # melt pool nodes (Y >= SUB_Y)
    
    for v in nt.values:
        iname = node_inst.get(v.nodeLabel)
        key = (iname, v.nodeLabel)
        if key in node_coords:
            c = node_coords[key]
            cx_mm = c[0] * 1000
            cy_mm = c[1] * 1000
            cz_mm = c[2] * 1000
            
            if c[1] >= SUB_Y:  # powder region
                if v.data > tmax_powder:
                    tmax_powder = v.data
                    tmax_powder_coord = (cx_mm, cy_mm, cz_mm)
                if v.data >= T_LIQ:
                    hot_powder.append((v.data, cx_mm, cy_mm, cz_mm))
            else:  # substrate region
                if v.data > tmax_sub:
                    tmax_sub = v.data
    
    # Melt pool metrics (powder only)
    if hot_powder and len(hot_powder) > 2:
        xs = [h[1] for h in hot_powder]
        ys = [h[2] for h in hot_powder]
        zs = [h[3] for h in hot_powder]
        w = max(xs) - min(xs)
        d = max(ys) - min(ys)
        l = max(zs) - min(zs)
        
        # Interface width at powder bottom (Y just above SUB_Y)
        interface_x = [h[1] for h in hot_powder if abs(h[2] - 4.8) < 0.15]
        iw = max(interface_x) - min(interface_x) if len(interface_x) > 1 else 0
        
        # Temperature gradient (approx: difference across melt length)
        if l > 0.5:
            avg_grad = (tmax_powder - T_LIQ) / (max(zs) - min(z for _,_,_,z in hot_powder if abs(_ - T_LIQ) < 100)) if any(abs(_-T_LIQ) < 100 for _,_,_,_ in hot_powder) else (tmax_powder - T_LIQ) / l * 2
        else:
            avg_grad = 0
    else:
        w = d = l = iw = avg_grad = 0
    
    print(f"{case:>12s}  {power:6d}  {speed:4d}  {effq:6.0f}  {tmax_powder:8.1f}  {tmax_sub:10.0f}  {len(hot_powder):5d}  {w:7.3f}  {d:7.3f}  {l:7.3f}  {iw:7.3f}  {avg_grad:11.1f}")
    
    # Save result
    tmax_coord_str = f"@({tmax_powder_coord[0]:.2f},{tmax_powder_coord[1]:.2f},{tmax_powder_coord[2]:.2f})mm" if hot_powder else ""
    with open(f'D:\\temp\\duoceng3\\_{case}_result.txt', 'w') as rf:
        rf.write(f"{case}: Q={effq:.0f}W v={speed}mm/s | Tmax={tmax_powder:.0f}C {tmax_coord_str} | SubTmax={tmax_sub:.0f}C | Pool:N={len(hot_powder)} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm IW={iw:.3f}mm G={avg_grad:.0f}C/mm | Step=Step-8\n")
        rf.write(f"Q={effq:.0f}W v={speed}mm/s\n")
        rf.write(f"PeakT={tmax_powder:.0f}C\n")
        rf.write(f"MaxPowderT={tmax_powder:.0f}C MaxSubT={tmax_sub:.0f}C\n")
        if hot_powder:
            rf.write(f"MeltPool:N={len(hot_powder)} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm IW={iw:.3f}mm G={avg_grad:.0f}C/mm\n")
        rf.write(f"LastStep=Step-8\n")
    
    odb.close()

print("-" * 110)
print("Tmax = peak powder temp, SubTmax = max substrate temp (preheated to 300C)")
print("W = melt pool width in powder, D = melt depth in powder, L = melt length")
print("IW = interface width at powder-substrate boundary")
