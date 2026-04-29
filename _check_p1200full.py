"""full_p1200 all layers"""
from odbAccess import openOdb
odb = openOdb('full_p1200.odb', readOnly=True)
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

for sn in ['Step-41', 'Step-82', 'Step-122']:
    if sn in odb.steps:
        step = odb.steps[sn]
        f = step.frames[-1]
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

# Check also the full_p2000 final steps
print("\nfull_p2000 (still running) last check:")
try:
    odb2 = openOdb('full_p2000.odb', readOnly=True)
    for sn in ['Step-41']:
        if sn in odb2.steps:
            step = odb2.steps[sn]
            f = step.frames[-1]
            nt = f.fieldOutputs['NT11']
            tmax = max(v.data for v in nt.values)
            pow_max = 0
            for v in nt.values:
                info = node_info.get(v.nodeLabel)
                if info and info[0] == 'POWDER-1' and v.data > pow_max: pow_max = v.data
            print(f"  full_p2000 {sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C")
    odb2.close()
except:
    print("   not available yet")

odb.close()
