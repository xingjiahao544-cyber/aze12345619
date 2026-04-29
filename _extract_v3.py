"""
Extract at the FRAME where heat source is active, not the last increment (cooled)
For short INP with 8 heating steps, Step-8 is the last heating step.
The heat source is at Z = (ACTIVE_STEP)*DT_PER_STEP*SCAN_SPEED
For ACTIVE_STEP = 8: Z = 8 * 0.12s * 5mm/s = 4.8mm 
So the hottest powder node should be near Z=4.8mm in Step-8's LAST frame
"""
from odbAccess import openOdb

CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

T_LIQ = 1400.0
SUB_Y = 0.0048

print("=" * 110)
print("Hybrid 3x3 Orthogonal - Extracting Step-8 FINAL frame (heat source at end)")
print("=" * 110)
print(f"{'Case':>12s}  {'P(W)':>6s}  {'v':>4s}  {'EffQ':>6s}  {'Tmax(C)':>8s}  {'SubTmax(C)':>10s}  {'Nhot':>5s}  {'W(mm)':>7s}  {'D(mm)':>7s}  {'L(mm)':>7s}  {'IW(mm)':>7s}")
print("-" * 100)

for case in CASES:
    parts = case.split('_')
    power = int(parts[0].replace('P', ''))
    speed = int(parts[1].replace('V', ''))
    effq = power * 0.4
    
    odb = openOdb(f'short_{case}.odb', readOnly=True)
    
    node_to_inst = {}
    for inst_name, inst in odb.rootAssembly.instances.items():
        for n in inst.nodes:
            node_to_inst[n.label] = inst_name
    
    # Get powder node coordinates
    powder_coords = {}
    for n in odb.rootAssembly.instances['POWDER-1'].nodes:
        powder_coords[n.label] = n.coordinates
    
    # Try Step-8 (should be last heating step before cooling)  
    for target_step in ['Step-8', 'Step-9']:
        if target_step not in odb.steps.keys():
            continue
        
        step = odb.steps[target_step]
        # Use LAST frame (final increment)
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        
        # Max temp in powder
        max_t_powder = -1
        max_t_sub = -1
        hot_powder = []
        
        for v in nt.values:
            iname = node_to_inst.get(v.nodeLabel)
            key = ('POWDER-1', v.nodeLabel)
            c = powder_coords.get(v.nodeLabel)
            
            if iname and 'POWDER' in iname.upper() and c is not None:
                if v.data > max_t_powder:
                    max_t_powder = v.data
                    max_coord = (c[0]*1000, c[1]*1000, c[2]*1000)
                if v.data >= T_LIQ:
                    hot_powder.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
            elif iname and 'SUBSTRATE' in iname.upper():
                if v.data > max_t_sub:
                    max_t_sub = v.data
    
        if max_t_powder > 0:
            break
    
    if not hot_powder or len(hot_powder) < 3:
        print(f"{case:>12s}  {power:6d}  {speed:4d}  {effq:6.0f}  {max_t_powder:8.1f}  {max_t_sub:10.0f}  {len(hot_powder):5d}      -      -      -      -")
    else:
        xs = [h[1] for h in hot_powder]; ys = [h[2] for h in hot_powder]; zs = [h[3] for h in hot_powder]
        w = max(xs)-min(xs); d = max(ys)-min(ys); l = max(zs)-min(zs)
        interface_x = [h[1] for h in hot_powder if abs(h[2] - 4.8) < 0.15]
        iw = max(interface_x)-min(interface_x) if len(interface_x) > 1 else 0
        print(f"{case:>12s}  {power:6d}  {speed:4d}  {effq:6.0f}  {max_t_powder:8.1f}  {max_t_sub:10.0f}  {len(hot_powder):5d}  {w:7.3f}  {d:7.3f}  {l:7.3f}  {iw:7.3f}")
    
    # Also print the hottest 5 powder nodes for debugging
    all_powder = [(v.data, v.nodeLabel) for v in nt.values 
                  if node_to_inst.get(v.nodeLabel,'').upper().startswith('POWDER')]
    all_powder.sort(key=lambda x: x[0], reverse=True)
    print(f"    Hot powder nodes: {all_powder[:3] if all_powder else 'none'}")
    
    odb.close()

print("-" * 100)
