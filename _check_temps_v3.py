"""
Check v3 - use full instance names
"""
from odbAccess import openOdb

odb = openOdb('short_P1000_V5.odb', readOnly=True)

# Print ALL instance names exactly
for inst_name, inst in odb.rootAssembly.instances.items():
    print(f"Instance: '{inst_name}'")
    for n in inst.nodes[:3]:
        print(f"  Node {n.label}: ({n.coordinates[0]:.4f}, {n.coordinates[1]:.4f}, {n.coordinates[2]:.4f})")

# Get NT11
step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

# Build node->instance mapping from instances directly
node_to_inst = {}
for inst_name, inst in odb.rootAssembly.instances.items():
    for n in inst.nodes:
        node_to_inst[n.label] = inst_name

print(f"\nMapped nodes: {len(node_to_inst)}")

# Count by instance
powder_nodes = [nl for nl, iname in node_to_inst.items() if 'POWDER' in iname.upper()]
sub_nodes = [nl for nl, iname in node_to_inst.items() if 'SUBSTRATE' in iname.upper()]
print(f"Powder nodes: {len(powder_nodes)}, Substrate nodes: {len(sub_nodes)}")

# Analyze temperatures
powder_temps = []
sub_temps = []

for v in nt.values:
    iname = node_to_inst.get(v.nodeLabel)
    if iname:
        if 'POWDER' in iname.upper():
            powder_temps.append((v.data, v.nodeLabel))
        elif 'SUBSTRATE' in iname.upper():
            sub_temps.append((v.data, v.nodeLabel))

print(f"\nPowder field values: {len(powder_temps)}")
if powder_temps:
    max_t = max(t for t,_ in powder_temps)
    min_t = min(t for t,_ in powder_temps)
    print(f"  T range: {min_t:.0f} ~ {max_t:.0f} C")
    print(f"  T > 1400: {sum(1 for t,_ in powder_temps if t > 1400)}")
    print(f"  T > 1000: {sum(1 for t,_ in powder_temps if t > 1000)}")
    
    # Top 5
    powder_temps.sort(key=lambda x: x[0], reverse=True)
    for t, nl in powder_temps[:5]:
        inst_n = node_to_inst.get(nl)
        for inst_name, inst in odb.rootAssembly.instances.items():
            if inst_name == inst_n:
                nodes_found = [n for n in inst.nodes if n.label == nl]
                if nodes_found:
                    n = nodes_found[0]
                    print(f"  {inst_name} Node {nl}: {t:.0f}C @ ({n.coordinates[0]*1000:.2f},{n.coordinates[1]*1000:.2f},{n.coordinates[2]*1000:.2f})mm")

print(f"\nSubstrate field values: {len(sub_temps)}")
if sub_temps:
    max_t = max(t for t,_ in sub_temps)
    min_t = min(t for t,_ in sub_temps)
    print(f"  T range: {min_t:.0f} ~ {max_t:.0f} C")
    print(f"  T > 1400: {sum(1 for t,_ in sub_temps if t > 1400)}")

odb.close()
