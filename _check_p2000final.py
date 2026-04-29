"""full_p2000 all 3 layers"""
from odbAccess import openOdb
odb = openOdb('full_p2000.odb', readOnly=True)
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)
for sn in ['Step-41', 'Step-82', 'Step-122']:
    if sn in odb.steps:
        step = odb.steps[sn]
        if step.frames:
            f = step.frames[-1]
            nt = f.fieldOutputs['NT11']
            tmax = max(v.data for v in nt.values)
            pow_max = 0; pow_1400 = 0
            for v in nt.values:
                info = node_info.get(v.nodeLabel)
                if info and info[0] == 'POWDER-1':
                    if v.data > pow_max: pow_max = v.data
                    if v.data >= 1400: pow_1400 += 1
            print(f"{sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  P>1400={pow_1400}")
odb.close()
