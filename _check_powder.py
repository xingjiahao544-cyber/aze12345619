"""
Check powder temperature distribution in detail for P1000_V5
"""
from odbAccess import openOdb

odb = openOdb('short_P1000_V5.odb', readOnly=True)

step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

node_to_inst = {}
for inst_name, inst in odb.rootAssembly.instances.items():
    for n in inst.nodes:
        node_to_inst[n.label] = inst_name

# All powder temps
powder_temps = []
for v in nt.values:
    iname = node_to_inst.get(v.nodeLabel)
    if iname and 'POWDER' in iname.upper():
        powder_temps.append(v.data)

print(f"Powder nodes: {len(powder_temps)}")
print(f"Powder T max: {max(powder_temps):.0f}C")
print(f"Powder T min: {min(powder_temps):.0f}C")

# Distribution
for tr in [(0,50), (50,100), (100,200), (200,300), (300,400), (400,500), (500,700), (700,1000), (1000,1400), (1400, 2000)]:
    cnt = sum(1 for t in powder_temps if tr[0] <= t < tr[1])
    if cnt > 0:
        print(f"  {tr[0]}-{tr[1]}C: {cnt} nodes")

# Top 10 powder nodes with coordinates
print("\n--- Top 10 powder nodes ---")
powder = [(v.data, v.nodeLabel) for v in nt.values if node_to_inst.get(v.nodeLabel,'').upper().startswith('POWDER')]
powder.sort(key=lambda x: x[0], reverse=True)

# Get all Powder-1 node coordinates
powder_coords = {}
for n in odb.rootAssembly.instances['POWDER-1'].nodes:
    powder_coords[n.label] = n.coordinates

for t, nl in powder[:10]:
    c = powder_coords.get(nl, None)
    if c:
        print(f"  Node {nl}: {t:.0f}C @ ({c[0]*1000:.3f}, {c[1]*1000:.3f}, {c[2]*1000:.3f})mm")

# Check Y=6.3mm layer (Layer 3 top)
print("\n--- Layer 3 top (Y ~ 6.3mm) temps ---")
l3top = [(v.data, v.nodeLabel) for v in nt.values 
         if node_to_inst.get(v.nodeLabel,'').upper().startswith('POWDER')]
l3top_with_y = []
for t, nl in l3top:
    c = powder_coords.get(nl)
    if c and abs(c[1]*1000 - 6.3) < 0.2:
        l3top_with_y.append((t, nl, c))
l3top_with_y.sort(key=lambda x: x[0], reverse=True)
print(f"  Nodes near Y=6.3mm (Layer 3 top): {len(l3top_with_y)}")
for t, nl, c in l3top_with_y[:5]:
    print(f"  Node {nl}: {t:.0f}C @ ({c[0]*1000:.3f}, {c[1]*1000:.3f}, {c[2]*1000:.3f})mm")

# Check Y=4.8mm layer (Layer 1 bottom)
print("\n--- Layer 1 bottom (Y ~ 4.8mm) temps ---")
l1bot = [(v.data, v.nodeLabel, c) for t, nl, c in l3top_with_y if abs(c[1]*1000 - 4.8) < 0.2]
# Actually find nodes near Y=4.8
l1bot = []
for t, nl in l3top:
    c = powder_coords.get(nl)
    if c and abs(c[1]*1000 - 4.8) < 0.3:
        l1bot.append((t, nl, c))
l1bot.sort(key=lambda x: x[0], reverse=True)
print(f"  Nodes near Y=4.8mm: {len(l1bot)}")
for t, nl, c in l1bot[:5]:
    print(f"  Node {nl}: {t:.0f}C @ ({c[0]*1000:.3f}, {c[1]*1000:.3f}, {c[2]*1000:.3f})mm")

odb.close()
