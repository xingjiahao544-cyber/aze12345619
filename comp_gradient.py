"""
Temperature gradient analysis for 3 Goldak variants
Use Step-25 (center of scan) data
"""
from odbAccess import openOdb
import sys

CASES = ['compare_de_std', 'compare_de_ext', 'compare_de_hyb']
NAMES = ['Standard_DE', 'Tapered_DE', 'Hybrid_DE']
T_LIQ = 1400.0

for i, case in enumerate(CASES):
    odb = openOdb(f'{case}.odb', readOnly=True)
    
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
    
    # Step-25 center analysis
    step = odb.steps['Step-25']
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    
    # Find hotspot center
    hot_all = [(v.data, v.nodeLabel) for v in nt.values]
    hot_all.sort(key=lambda x: x[0], reverse=True)
    peak_node = hot_all[0][1]
    iname = node_inst.get(peak_node, list(node_coords.keys())[0][0])
    pc = node_coords[(iname, peak_node)]
    x0, y0, z0 = pc[0]*1000, pc[1]*1000, pc[2]*1000
    
    print(f"\n{NAMES[i]} — Step-25 Hotspot at ({x0:.2f}, {y0:.2f}, {z0:.2f})mm")
    
    # Z-direction gradient (along scan direction)
    z_temps = []
    for v in nt.values:
        iname2 = node_inst.get(v.nodeLabel, list(node_coords.keys())[0][0])
        if (iname2, v.nodeLabel) in node_coords:
            c = node_coords[(iname2, v.nodeLabel)]
            if abs(c[2]*1000 - z0) < 0.15 and abs(c[0]*1000 - x0) < 0.15:
                z_temps.append((c[2]*1000, v.data))
    
    z_temps.sort(key=lambda x: x[0])
    if len(z_temps) >= 3:
        z_mid = [z for z in z_temps if abs(z[0]-z0) < 0.3]
        if len(z_mid) >= 2:
            # Gradient = max temp diff / distance
            t_peak = max(z[1] for z in z_mid)
            z_peak_idx = min(range(len(z_temps)), key=lambda i: abs(z_temps[i][1]-t_peak))
            
            # Forward gradient (ahead of hotspot)
            forward = [z for z in z_temps if z[0] > z0]
            if forward:
                grad_f = (t_peak - forward[0][1]) / (forward[0][0] - z0) if forward[0][1] < t_peak else 0
            else:
                grad_f = 0
            
            # Backward gradient (behind hotspot)
            backward = [z for z in z_temps if z[0] < z0]
            if backward:
                grad_b = (t_peak - backward[-1][1]) / (z0 - backward[-1][0]) if backward[-1][1] < t_peak else 0
            else:
                grad_b = 0
            
            print(f"  Forward gradient (ahead): {abs(grad_f):.0f} C/mm")
            print(f"  Backward gradient (behind): {abs(grad_b):.0f} C/mm")
            
            # Z profile
            z_near = [z for z in z_temps if abs(z[0]-z0) < 0.8]
            for z, t in z_near:
                m = ' <-- PEAK' if abs(z-z0)<0.05 and abs(t-t_peak)<1 else (' *' if t>=T_LIQ else '')
                print(f"    Z={z:.2f}mm T={t:.0f}C{m}")
    
    # X-direction gradient (width direction)
    x_temps = []
    for v in nt.values:
        iname2 = node_inst.get(v.nodeLabel, list(node_coords.keys())[0][0])
        if (iname2, v.nodeLabel) in node_coords:
            c = node_coords[(iname2, v.nodeLabel)]
            if abs(c[2]*1000 - z0) < 0.15 and abs(c[1]*1000 - y0) < 0.15:
                x_temps.append((c[0]*1000, v.data))
    
    x_temps.sort(key=lambda x: x[0])
    if len(x_temps) >= 3:
        x_near = [x for x in x_temps if abs(x[0]-x0) < 0.8]
        if x_near:
            max_t = max(x[1] for x in x_near)
            # Left gradient
            left = [x for x in x_near if x[0] < x0]
            right = [x for x in x_near if x[0] > x0]
            if left:
                gl = (max_t - left[-1][1]) / (x0 - left[-1][0]) if left[-1][1] < max_t else 0
            else: gl = 0
            if right:
                gr = (max_t - right[0][1]) / (right[0][0] - x0) if right[0][1] < max_t else 0
            else: gr = 0
            print(f"  Left gradient: {gl:.0f} C/mm")
            print(f"  Right gradient: {gr:.0f} C/mm")
            for x, t in x_near:
                m = ' <-- PEAK' if abs(x-x0)<0.05 and abs(t-max_t)<1 else (' *' if t>=T_LIQ else '')
                print(f"    X={x:.3f}mm T={t:.0f}C{m}")
    
    odb.close()
