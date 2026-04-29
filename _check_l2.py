"""Check Layer 2 progression"""
from odbAccess import openOdb
odb = openOdb('ortho_P1200_V5.odb', readOnly=True)
node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

# Check Layer 2 and 3 steps in detail
for sn in ['Step-42','Step-50','Step-60','Step-70','Step-80','Step-82']:
    if sn not in odb.steps:
        continue
    step = odb.steps[sn]
    if not step.frames: continue
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    tmax = max(v.data for v in nt.values)
    pow_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info and info[0] == 'POWDER-1' and v.data > pow_max:
            pow_max = v.data
    print(f"{sn}: Tmax={tmax:.0f}C  PowderMax={pow_max:.0f}C")

# Find the hottest powder node in Step-82 and check its Y
step = odb.steps['Step-82']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
hots = []
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if info and info[0] == 'POWDER-1':
        c = info[1]
        hots.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
hots.sort(key=lambda x: -x[0])
print(f"\nStep-82 top 5 powder nodes:")
for t, x, y, z in hots[:5]:
    print(f"  T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

# Check FOR Y0 for Layer 2
print(f"\nExpected: Y0(L2) = 4.8 + 2*0.6 = 6.0mm")
print(f"Powder Y range for Layer 2: 5.4~6.0mm")
print(f"For powder Y=5.4mm: DY = 5.4-6.0 = -0.6mm")
print(f"Condition: -0.0006 < -(0.00066)? FALSE -> NOT excluded")
print(f"For powder Y=6.0mm: DY = 6.0-6.0 = 0mm")
print(f"Condition: 0 > 1e-10? TRUE -> EXCLUDED!")
print(f"\n*** PROBLEM: Y=6.0mm is the Layer 2 TOP SURFACE")
print(f"But the top nodes at exactly Y=6.0mm are excluded!")
print(f"And there are very few nodes at Y=5.99mm vs 6.0mm")

odb.close()
