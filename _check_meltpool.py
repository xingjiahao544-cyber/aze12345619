"""
Detailed melt pool analysis for P1000_V5 - check what's actually melting
"""
from odbAccess import openOdb

odb = openOdb('short_P1000_V5.odb', readOnly=True)

step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

# Build node->instance mapping
node_to_inst = {}
for inst_name, inst in odb.rootAssembly.instances.items():
    for n in inst.nodes:
        node_to_inst[n.label] = inst_name

T_LIQ = 1400.0

print("=== Powder nodes above T_LIQ ===")
hots = []
for v in nt.values:
    iname = node_to_inst.get(v.nodeLabel)
    if iname and 'POWDER' in iname.upper() and v.data >= T_LIQ:
        # Get coordinates
        for inst in odb.rootAssembly.instances.values():
            if inst.name == iname:
                for n in inst.nodes:
                    if n.label == v.nodeLabel:
                        hots.append((v.data, n.coordinates[0]*1000, n.coordinates[1]*1000, n.coordinates[2]*1000, iname))

hots.sort(key=lambda x: x[0], reverse=True)
print(f"Total molten powder nodes: {len(hots)}")
for t, x, y, z, nm in hots:
    print(f"  {nm} Node: {t:.0f}C @ X={x:.3f}mm, Y={y:.3f}mm, Z={z:.3f}mm")

# Check powder Y range
print("\n=== Powder node Y range ===")
powder_ys = []
for inst in odb.rootAssembly.instances.values():
    if 'POWDER' in inst.name.upper():
        for n in inst.nodes:
            powder_ys.append(n.coordinates[1]*1000)
print(f"Y range: {min(powder_ys):.3f} ~ {max(powder_ys):.3f} mm")

# Check powder X and Z ranges
print(f"\n=== All powder nodes temp distribution ===")
for temp_range_name, tmin, tmax in [(">1400C", 1400, 1e9), ("1000-1400", 1000, 1400), ("500-1000", 500, 1000)]:
    count = 0
    for v in nt.values:
        iname = node_to_inst.get(v.nodeLabel)
        if iname and 'POWDER' in iname.upper() and tmin <= v.data < tmax:
            count += 1
    print(f"  {temp_range_name}: {count} nodes")

# Check substrate Y range
print("\n=== Substrate Y range ===")
sub_ys = []
for inst in odb.rootAssembly.instances.values():
    if 'SUBSTRATE' in inst.name.upper():
        for n in inst.nodes:
            sub_ys.append(n.coordinates[1]*1000)
print(f"Y range: {min(sub_ys):.3f} ~ {max(sub_ys):.3f} mm")

# Substrate hottest nodes
print("\n=== Top 5 substrate nodes ===")
sub_hots = []
for v in nt.values:
    iname = node_to_inst.get(v.nodeLabel)
    if iname and 'SUBSTRATE' in iname.upper():
        sub_hots.append((v.data, v.nodeLabel))
sub_hots.sort(key=lambda x: x[0], reverse=True)
for t, nl in sub_hots[:5]:
    for inst in odb.rootAssembly.instances.values():
        if 'SUBSTRATE' in inst.name.upper():
            for n in inst.nodes:
                if n.label == nl:
                    print(f"  Node {nl}: {t:.0f}C @ ({n.coordinates[0]*1000:.3f},{n.coordinates[1]*1000:.3f},{n.coordinates[2]*1000:.3f})mm")

odb.close()
