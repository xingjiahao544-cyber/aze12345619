"""Check hyb_dbg - debug version"""
from odbAccess import openOdb
odb = openOdb('hyb_dbg.odb', readOnly=True)
coords = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        coords[n.label] = (inst.name, n.coordinates)

for sname in ['Step-2', 'Step-4']:
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    
    tmax = 0
    hot_powder = []
    for v in nt.values:
        if v.data > tmax: tmax = v.data
        tup = coords.get(v.nodeLabel)
        if tup:
            nm, c = tup
            if nm == 'POWDER-1':
                hot_powder.append((v.data, v.nodeLabel, c[0]*1000, c[1]*1000, c[2]*1000))
    
    hot_powder.sort(key=lambda x: -x[0])
    print(f"{sname}: Tmax={tmax:.0f}C")
    if hot_powder:
        print(f"  Hottest powder: T={hot_powder[0][0]:.0f}C @ Z={hot_powder[0][3]:.2f}mm")

# Also check step times
print(f"\n=== STA time analysis ===")
with open('hyb_dbg.sta', 'r') as f:
    lines = f.readlines()
for line in lines[-5:]:
    print(line.strip())
odb.close()
