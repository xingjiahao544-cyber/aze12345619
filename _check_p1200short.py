"""p1200 short final check"""
from odbAccess import openOdb
odb = openOdb('p1200.odb', readOnly=True)
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)
for sn in ['Step-8', 'Step-42']:
    if sn in odb.steps:
        step = odb.steps[sn]
        f = step.frames[-1]
        nt = f.fieldOutputs['NT11']
        tmax = max(v.data for v in nt.values)
        pow_max = 0
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0] == 'POWDER-1' and v.data > pow_max: pow_max = v.data
        print(f"{sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C")
odb.close()
