"""
Detailed check: temperature distribution in powder for P1000_V5 at Step-8
"""
from odbAccess import openOdb

odb = openOdb('short_P1000_V5.odb', readOnly=True)

SUB_Y = 0.0048
T_LIQ = 1400.0

# Build node coords + find powder nodes
powder_nodes = []
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        c = n.coordinates
        if c[1] >= SUB_Y:  # powder
            powder_nodes.append({
                'label': n.label,
                'inst': inst.name,
                'x': c[0]*1000, 'y': c[1]*1000, 'z': c[2]*1000
            })

print(f"Total powder nodes: {len(powder_nodes)}")

step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

node_inst = {}
for inst in odb.rootAssembly.instances.values():
    for el in inst.elements:
        for nl in el.connectivity:
            node_inst[nl] = inst.name

# Get temperatures for all powder nodes
powder_temps = []
for v in nt.values:
    iname = node_inst.get(v.nodeLabel)
    if iname and iname.startswith('Powder'):
        powder_temps.append(v.data)
        
print(f"Powder nodes with NT11: {len(powder_temps)}")
if powder_temps:
    print(f"Powder T range: {min(powder_temps):.0f} ~ {max(powder_temps):.0f} C")
    print(f"Powder T > 1400: {sum(1 for t in powder_temps if t > 1400)} nodes")
    print(f"Powder T > 1000: {sum(1 for t in powder_temps if t > 1000)} nodes")

# Check highest powder nodes detail
print("\n--- Top 20 hottest powder nodes ---")
hots = []
for v in nt.values:
    iname = node_inst.get(v.nodeLabel)
    if iname and iname.startswith('Powder') and v.data > 1200:
        hots.append((v.data, v.nodeLabel))

hots.sort(key=lambda x: x[0], reverse=True)
for t, nl in hots[:20]:
    for pn in powder_nodes:
        if pn['label'] == nl:
            print(f"  Node {nl}: {t:.0f}C @ ({pn['x']:.2f}, {pn['y']:.2f}, {pn['z']:.2f})mm")
            break

# Check substrate hottest
sub_temps = []
for v in nt.values:
    iname = node_inst.get(v.nodeLabel)
    if iname and iname.startswith('Substrate'):
        sub_temps.append(v.data)
print(f"\nSubstrate T range: {min(sub_temps):.0f} ~ {max(sub_temps):.0f} C")
print(f"Substrate T > 1400: {sum(1 for t in sub_temps if t > 1400)} nodes")
print(f"Substrate T > 1000: {sum(1 for t in sub_temps if t > 1000)} nodes")

odb.close()
