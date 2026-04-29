"""Check full_cool10s - Layer 1 and layer 2"""
from odbAccess import openOdb
odb = openOdb('full_cool10s.odb', readOnly=True)
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

# Step-41 = Layer 1 end, Step-42 = cool, Step-43~47 = Layer 2
for sn in ['Step-41', 'Step-42', 'Step-47']:
    if sn in odb.steps:
        step = odb.steps[sn]
        if step.frames:
            f = step.frames[-1]
        else:
            print(f"{sn}: NO FRAMES!"); continue
        nt = f.fieldOutputs['NT11']
        tmax = max(v.data for v in nt.values)
        pow_max = 0; pow_1400 = 0; pow_500 = 0
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0] == 'POWDER-1':
                if v.data > pow_max: pow_max = v.data
                if v.data >= 1400: pow_1400 += 1
                if v.data >= 500: pow_500 += 1
        print(f"{sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C  P>500={pow_500}  P>1400={pow_1400}")

odb.close()
