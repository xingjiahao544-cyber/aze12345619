"""
Detailed orthogonal experiment: extract per-step progression + gradient analysis
"""
from odbAccess import openOdb
import sys

CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

T_LIQ = 1400.0

# For each case, show step progression
for case in CASES:
    parts = case.split('_')
    power = int(parts[0].replace('P',''))
    speed = int(parts[1].replace('V',''))
    
    odb = openOdb(f'hybrid_{case}.odb', readOnly=True)
    print(f"\n{'='*60}")
    print(f"  {case}: P={power}W, v={speed}mm/s, Q_eff={power*0.4}W, dt={0.0006/(speed/1000):.4f}s")
    print(f"{'='*60}")
    
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
    
    # For each step
    print(f"  {'Step':>6s} {'Tmax(C)':>9s} {'Nhot':>5s} {'Ninc':>5s}")
    for sname in list(odb.steps.keys()):
        if sname == 'Step-1' or sname == 'Step-42':
            continue
        snum = int(sname.replace('Step-',''))
        
        step = odb.steps[sname]
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        ninc = len(step.frames)
        tmax = max(v.data for v in nt.values)
        
        # Hot nodes
        hot = []
        for v in nt.values:
            iname = node_inst.get(v.nodeLabel, list(node_coords.keys())[0][0])
            key = (iname, v.nodeLabel)
            if key in node_coords:
                c = node_coords[key]
                if v.data >= T_LIQ:
                    hot.append((v.data, c[0]*1000, c[2]*1000))
        
        print(f"  Step-{snum:2d} {tmax:9.1f} {len(hot):5d} {ninc:5d}")
    
    # Substrate max temp from Step-8
    step8 = odb.steps['Step-8']
    f8 = step8.frames[-1]
    nt8 = f8.fieldOutputs['NT11']
    sub_d = 0.0048  # substrate top Y
    
    sub_temps = []
    for v in nt8.values:
        iname = node_inst.get(v.nodeLabel, list(node_coords.keys())[0][0])
        key = (iname, v.nodeLabel)
        if key in node_coords:
            c = node_coords[key]
            if c[1] < sub_d - 0.0001:  # inside substrate (not at interface)
                sub_temps.append((c[1]*1000, v.data))
    
    if sub_temps:
        sub_max = max(s[1] for s in sub_temps)
        print(f"  Substrate max temp: {sub_max:.1f}C")
    
    odb.close()
