"""Debug node_info construction"""
from odbAccess import openOdb
odb = openOdb('ortho3t_P800_V5.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

# Check a few entries
print(f"node_info has {len(node_info)} entries")
counts = {}
for nid, (iname, _) in node_info.items():
    counts[iname] = counts.get(iname, 0) + 1
for iname, cnt in sorted(counts.items()):
    print(f"  {iname}: {cnt} nodes")

# Step-121: match labels
step = odb.steps['Step-121']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

powder_hits = {pn: 0 for pn in ['Powder-1', 'Powder-2', 'Powder-3']}
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if not info:
        continue
    iname = info[0].upper()
    for pn in ['Powder-1', 'Powder-2', 'Powder-3']:
        if pn.upper() in iname:
            powder_hits[pn] += 1
            break

print(f"\nPowder hits in Step-121:")
for pn, cnt in powder_hits.items():
    print(f"  {pn}: {cnt}")

odb.close()
