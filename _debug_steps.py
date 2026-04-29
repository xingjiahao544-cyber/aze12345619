"""
Debug: check what the FOR file is actually doing for P1000_V5
"""
from odbAccess import openOdb

odb = openOdb('short_P1000_V5.odb', readOnly=True)
step = odb.steps['Step-8']

# Check step info
print(f"Step-8: {len(step.frames)} frames")

# Also check if Step-8 even has proper heating by looking at Step-2
for sn in ['Step-2', 'Step-3', 'Step-4', 'Step-5', 'Step-6', 'Step-7', 'Step-8']:
    s = odb.steps[sn]
    f = s.frames[-1]
    nt = f.fieldOutputs['NT11']
    
    # Max temp in powder
    node_to_inst = {}
    for inst_name, inst in odb.rootAssembly.instances.items():
        for n in inst.nodes:
            node_to_inst[n.label] = inst_name
    
    max_t_powder = -1
    max_t_sub = -1
    for v in nt.values:
        iname = node_to_inst.get(v.nodeLabel)
        if iname and 'POWDER' in iname.upper():
            if v.data > max_t_powder:
                max_t_powder = v.data
        elif iname and 'SUBSTRATE' in iname.upper():
            if v.data > max_t_sub:
                max_t_sub = v.data
    
    print(f"  {sn}: powder max={max_t_powder:.0f}C, substrate max={max_t_sub:.0f}C")

# Also check Model Change steps - which layers are active?
print("\n=== Checking SET activations ===")
# From INP: Step-2 activates Set-Layer-001, Step-3 activates Set-Layer-002, etc
# In the short INP, Step-8 means 7 layers activated (001-007)
# For Layer 1, there are 40 layers total (001-040)
# Each layer has 14 elements (7X × 2Y)
# So Set-Layer-001 has 14 elements

# Check which sets exist in the model
print("\n=== Node sets ===")
for ns_name, ns in odb.rootAssembly.nodeSets.items():
    print(f"  {ns_name}: {len(ns.nodes)} nodes")

print("\n=== Element sets ===")
# Can't list ElementSets easily, just check known ones
try:
    es = odb.rootAssembly.elementSets['ALL ELEMENTS']
    print(f"  ALL ELEMENTS: {len(es.elements)} elements")
except:
    print("  No 'ALL ELEMENTS' set")

odb.close()
