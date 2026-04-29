"""Check full_p1200 at Step-41"""
from odbAccess import openOdb
odb = openOdb('full_p1200.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

if 'Step-41' in odb.steps:
    step = odb.steps['Step-41']
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    
    tmax = 0
    pow_max = 0
    pow_500 = 0
    pow_1400 = 0
    sub_max = 0
    for v in nt.values:
        if v.data > tmax: tmax = v.data
        info = node_info.get(v.nodeLabel)
        if info:
            nm, c = info
            if nm == 'POWDER-1':
                if v.data > pow_max: pow_max = v.data
                if v.data >= 500: pow_500 += 1
                if v.data >= 1400: pow_1400 += 1
            if nm == 'SUBSTRATE-1' and v.data > sub_max: sub_max = v.data
    
    print(f"Step-41: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  SubMax={sub_max:.0f}C  P>500={pow_500}  P>1400={pow_1400}")
    
    hots = []
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0] == 'POWDER-1':
            hots.append((v.data, info[1][0]*1000, info[1][1]*1000, info[1][2]*1000))
    hots.sort(key=lambda x: -x[0])
    print(f"Hottest powder:")
    for t, x, y, z in hots[:5]:
        print(f"  T={t:.0f}C @ X={x:.1f} Y={y:.1f} Z={z:.1f}")

# Also Step-40 and earlier to see trend
for sn in ['Step-20', 'Step-25', 'Step-30', 'Step-35', 'Step-40']:
    if sn in odb.steps:
        step = odb.steps[sn]
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        pow_max = 0
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0] == 'POWDER-1' and v.data > pow_max:
                pow_max = v.data
        tmax = max(v.data for v in nt.values)
        print(f"  {sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C")

odb.close()
