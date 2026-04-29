"""Check powder top surface temps"""
from odbAccess import openOdb
import math

odb = openOdb('hyb_v6c.odb', readOnly=True)

coords = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        coords[n.label] = (inst.name, n.coordinates)

step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

# ALL nodes, not just powder, check if DFLUX is working
print("=== All nodes > 300C in Step-8 ===")
hots = []
for v in nt.values:
    if v.nodeLabel in coords:
        iname, c = coords[v.nodeLabel]
        if v.data > 300:
            hots.append((v.data, v.nodeLabel, iname, c[0]*1000, c[1]*1000, c[2]*1000))

hots.sort(key=lambda x: -x[0])
for t, nl, nm, x, y, z in hots[:30]:
    print(f"  {nm:>12s} Node {nl:>5d}: T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

# Check powder nodes at top surface (Y near 5.4mm)
print("\n=== Powder top surface (Y>5.3mm), Z near 4.2mm ===")
for v in nt.values:
    if v.nodeLabel in coords:
        iname, c = coords[v.nodeLabel]
        if iname == 'POWDER-1' and c[1]*1000 > 5.3 and abs(c[2]*1000-4.2) < 0.3:
            print(f"  Node {v.nodeLabel:>5d}: T={v.data:.1f}C @ X={c[0]*1000:.2f} Y={c[1]*1000:.2f} Z={c[2]*1000:.2f}")

# Check what Y values powder nodes have
print("\n=== Y range of powder nodes with T > 299C ===")
for v in nt.values:
    if v.nodeLabel in coords:
        iname, c = coords[v.nodeLabel]
        if iname == 'POWDER-1' and v.data > 299:
            print(f"  Y={c[1]*1000:.3f}mm T={v.data:.0f}C (max powder is 299 = step1 preheat)")

# Let me check at Step-2 first increment - is DFLUX even applied?
step2 = odb.steps['Step-2']
f2 = step2.frames[-1]
nt2 = f2.fieldOutputs['NT11']

print("\n=== Step-2: Powder nodes > 100C ===")
for v in nt2.values:
    if v.nodeLabel in coords:
        iname, c = coords[v.nodeLabel]
        if iname == 'POWDER-1' and v.data > 100:
            print(f"  Node {v.nodeLabel:>5d}: T={v.data:.0f}C @ X={c[0]*1000:.2f} Y={c[1]*1000:.2f} Z={c[2]*1000:.2f}")

odb.close()
