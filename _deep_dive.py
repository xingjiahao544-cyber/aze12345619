"""
Really dig into P1000_V5 - what's happening
"""
from odbAccess import openOdb

odb = openOdb('short_P1000_V5.odb', readOnly=True)

# Check all steps
for sn in ['Step-1', 'Step-2', 'Step-3', 'Step-5', 'Step-8']:
    step = odb.steps[sn]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    
    node_to_inst = {}
    for inst_name, inst in odb.rootAssembly.instances.items():
        for n in inst.nodes:
            node_to_inst[n.label] = inst_name
    
    powder_temps = []
    for v in nt.values:
        iname = node_to_inst.get(v.nodeLabel)
        if iname and 'POWDER' in iname.upper():
            powder_temps.append(v.data)
    
    print(f"\n{sn}: {len(step.frames)} frames")
    print(f"  Powder: max={max(powder_temps):.0f}C, min={min(powder_temps):.0f}C")
    print(f"  Powder count: {len(powder_temps)}")
    
    # Check Node 1717 specifically
    for v in nt.values:
        if v.nodeLabel == 1717:
            print(f"  Node 1717: {v.data:.1f}C")
            break

# Check which element sets are active
print("\n=== All element sets with sizes ===")
es_count = 0
for es_name, es in odb.rootAssembly.elementSets.items():
    size = len(es.elements)
    if size > 0:
        print(f"  {es_name}: {size} elements")
        es_count += 1
    if es_count > 10:
        print("  ...")
        break

# Check number of elements in Powder-1
inst = odb.rootAssembly.instances['POWDER-1']
print(f"\nPOWDER-1 has {len(inst.elements)} elements")

# Check a couple element coordinates
for el in inst.elements[:2]:
    node_coords = []
    for nl in el.connectivity:
        for n in inst.nodes:
            if n.label == nl:
                node_coords.append((n.coordinates[0]*1000, n.coordinates[1]*1000, n.coordinates[2]*1000))
    print(f"  Element {el.label}: nodes at {node_coords}")

odb.close()
