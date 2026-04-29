"""
Detailed check v2 - fix instance detection
"""
from odbAccess import openOdb

odb = openOdb('short_P1000_V5.odb', readOnly=True)

# Get all nodes by instance
print("=== Instances ===")
for inst_name, inst in odb.rootAssembly.instances.items():
    print(f"  {inst_name}: {len(inst.nodes)} nodes, {len(inst.elements)} elements")

# Get the field output
step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

# For field values, determine instance from nodeSet
# Build node->instance mapping from nodeSets
node_to_inst = {}
for inst_name, inst in odb.rootAssembly.instances.items():
    for n in inst.nodes:
        node_to_inst[n.label] = inst_name

print(f"\nTotal unique nodes mapped: {len(node_to_inst)}")

# Get all NT11 values with instance info
powder_temps = []
sub_temps = []

for v in nt.values:
    iname = node_to_inst.get(v.nodeLabel, 'unknown')
    if iname.startswith('Powder'):
        powder_temps.append(v.data)
    elif iname.startswith('Substrate'):
        sub_temps.append(v.data)

print(f"\nPowder nodes with NT11: {len(powder_temps)}")
if powder_temps:
    print(f"  T range: {min(powder_temps):.0f} ~ {max(powder_temps):.0f} C")
    print(f"  T > 1400: {sum(1 for t in powder_temps if t > 1400)}")
    print(f"  T > 1000: {sum(1 for t in powder_temps if t > 1000)}")
    
    # Top 20 hottest
    print("\n  Top 20 hottest powder nodes:")
    hots = [(v.data, v.nodeLabel) for v in nt.values if node_to_inst.get(v.nodeLabel,'').startswith('Powder') and v.data > 1200]
    hots.sort(key=lambda x: x[0], reverse=True)
    for t, nl in hots[:20]:
        c = [n.coordinates for n in odb.rootAssembly.instances['Powder-1'].nodes if n.label == nl]
        if c:
            coord = c[0]
            print(f"    Node {nl}: {t:.0f}C @ ({coord[0]*1000:.2f}, {coord[1]*1000:.2f}, {coord[2]*1000:.2f})mm")
    
print(f"\nSubstrate nodes with NT11: {len(sub_temps)}")
if sub_temps:
    print(f"  T range: {min(sub_temps):.0f} ~ {max(sub_temps):.0f} C")
    print(f"  T > 1400: {sum(1 for t in sub_temps if t > 1400)}")

odb.close()
