"""Uniform extraction for all ortho cases"""
import os, sys
from odbAccess import openOdb

CASES = ['P800_V3','P800_V5','P800_V8',
         'P1000_V3','P1000_V5','P1000_V8',
         'P1200_V3','P1200_V5','P1200_V8']

T_LIQ = 1400.0
SUB_D = 0.0048  # substrate top

for case in CASES:
    inp_path = f'ortho_{case}.inp'
    odb_path = f'ortho_{case}.odb'
    
    # Parse power and speed from case name
    parts = case.split('_')
    power = int(parts[0][1:])  # P800 -> 800
    speed = int(parts[1][1:])  # V5 -> 5
    q_eff = power * 0.4  # eta=0.4
    
    if not os.path.exists(odb_path):
        print(f"{case:>12s}: NO ODB")
        continue
    
    print(f"\n{'='*60}")
    print(f"{case:>12s}  P={power}W  v={speed}mm/s  Qeff={q_eff:.0f}W")
    print(f"{'='*60}")
    
    try:
        odb = openOdb(odb_path, readOnly=True)
    except:
        print(f"  Cannot open ODB")
        continue
    
    # Build node info
    node_info = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_info[n.label] = (inst.name, n.coordinates)
    
    # Check Step-41 (Layer 1 last heating step)
    for target_step in ['Step-20', 'Step-41', 'Step-42']:
        if target_step not in odb.steps:
            continue
        step = odb.steps[target_step]
        if not step.frames:
            print(f"  {target_step}: no frames")
            continue
        
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        n_frames = len(step.frames)
        
        tmax = 0
        pow_max = 0
        n_hot = 0
        hot_nodes = []
        for v in nt.values:
            if v.data > tmax: tmax = v.data
            info = node_info.get(v.nodeLabel)
            if info:
                nm, c = info
                if nm == 'POWDER-1':
                    if v.data > pow_max: pow_max = v.data
                    if v.data >= T_LIQ:
                        n_hot += 1
                        hot_nodes.append((v.data, c))
        
        if hot_nodes:
            xs = [n[1][0]*1000 for n in hot_nodes]
            ys = [n[1][1]*1000 for n in hot_nodes]
            zs = [n[1][2]*1000 for n in hot_nodes]
            w = max(xs)-min(xs) if xs else 0
            d = max(ys)-min(ys) if ys else 0
            l = max(zs)-min(zs) if zs else 0
            
            if target_step == 'Step-41':
                print(f"  Layer1: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  "
                      f"Melt: N={n_hot} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm")
            else:
                print(f"  {target_step}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  N>1400={n_hot}")
        else:
            if target_step == 'Step-41':
                print(f"  Layer1: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  NO MELT")
            else:
                print(f"  {target_step}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C")
    
    odb.close()
