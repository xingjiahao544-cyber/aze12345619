"""Find when P1200_V5 powder first starts heating"""
from odbAccess import openOdb

odb = openOdb('ortho_P1200_V5.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

for sn_name in odb.steps.keys():
    step = odb.steps[sn_name]
    if not step.frames:
        continue
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    pow_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0].upper() == 'POWDER-1' and v.data > pow_max:
            pow_max = v.data
    if pow_max > 500:
        print(f"{sn_name}: PowderMax={pow_max:.0f}C (FIRST > 500!)")
        break

odb.close()
