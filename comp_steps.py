"""
Extract melt pool at multiple reference steps for each case
"""
from odbAccess import openOdb
import sys

CASES = ['compare_de_std', 'compare_de_ext', 'compare_de_hyb']
NAMES = ['Standard_DE', 'Tapered_DE', 'Hybrid_DE']
T_LIQ = 1400.0

for i, case in enumerate(CASES):
    odb = openOdb(f'{case}.odb', readOnly=True)
    
    # Build node coords once
    node_coords = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_coords[(inst.name, n.label)] = (
                n.coordinates[0], n.coordinates[1], n.coordinates[2])
    
    # Build node->instance map once
    node_inst = {}
    for inst in odb.rootAssembly.instances.values():
        for el in inst.elements:
            for nl in el.connectivity:
                node_inst[nl] = inst.name
    
    keys = list(odb.steps.keys())
    print(f"\n{NAMES[i]}: {len(keys)} steps total")
    print(f"Steps: {keys[0]} ... {keys[-1]}")
    
    # For each step, extract
    for sname in keys:
        if sname == 'Step-1':
            continue
        snum = int(sname.replace('Step-', ''))
        if snum not in [5, 10, 15, 20, 25, 30, 35, 40]:
            continue
        
        step = odb.steps[sname]
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        
        # Find hot
        hot = []
        for v in nt.values:
            iname = node_inst.get(v.nodeLabel, list(node_coords.keys())[0][0])
            key = (iname, v.nodeLabel)
            if key in node_coords:
                c = node_coords[key]
                if v.data >= T_LIQ:
                    hot.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
        
        tmax = max(v.data for v in nt.values)
        
        if hot:
            xs = [h[1] for h in hot]; ys = [h[2] for h in hot]; zs = [h[3] for h in hot]
            w = max(xs)-min(xs); d = max(ys)-min(ys); l = max(zs)-min(zs)
            # Substrate interface melt
            sub_m = [h for h in hot if abs(h[2]-3.0)<0.15]
            sw = max([s[1] for s in sub_m])-min([s[1] for s in sub_m]) if sub_m else 0
            print(f"  {sname:>7s} Tmax={tmax:7.1f}C  W={w:.3f} D={d:.3f} L={l:.3f}  Nh={len(hot):3d} SubW={sw:.3f}")
        else:
            print(f"  {sname:>7s} Tmax={tmax:7.1f}C  No melt pool")
    
    odb.close()
