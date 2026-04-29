"""
Check ALL frames of Step-2 for P1000_V5
Look at the very first frame where heat flux is applied
"""
from odbAccess import openOdb

odb = openOdb('short_P1000_V5.odb', readOnly=True)

step = odb.steps['Step-2']
node_to_inst = {}
for inst_name, inst in odb.rootAssembly.instances.items():
    for n in inst.nodes:
        node_to_inst[n.label] = inst_name

print(f"Step-2 has {len(step.frames)} frames")

for fi, frame in enumerate(step.frames):
    nt = frame.fieldOutputs['NT11']
    
    # Max temp in powder
    max_t_powder = -1
    max_t_sub = -1
    for v in nt.values:
        iname = node_to_inst.get(v.nodeLabel)
        if iname and 'POWDER' in iname.upper():
            if v.data > max_t_powder:
                max_t_powder = v.data
                max_powder_nl = v.nodeLabel
        elif iname and 'SUBSTRATE' in iname.upper():
            if v.data > max_t_sub:
                max_t_sub = v.data
    
    if fi < 5 or fi == len(step.frames)-1:
        print(f"  Frame {fi}: powder max={max_t_powder:.1f}C, sub max={max_t_sub:.1f}C")

# Also check frame 0 (initial state of Step-2)
print("\n--- Frame 0 of Step-2 (initial) ---")
frame0 = step.frames[0]
nt0 = frame0.fieldOutputs['NT11']
# Find hottest powder nodes
hottest = []
for v in nt0.values:
    iname = node_to_inst.get(v.nodeLabel)
    if iname and 'POWDER' in iname.upper() and v.data > 500:
        hottest.append((v.data, v.nodeLabel))
hottest.sort(key=lambda x: x[0], reverse=True)
print(f"  Nodes > 500C in powder: {len(hottest)}")
for t, nl in hottest[:5]:
    for inst in odb.rootAssembly.instances.values():
        if 'POWDER' in inst.name.upper():
            for n in inst.nodes:
                if n.label == nl:
                    print(f"    Node {nl}: {t:.0f}C @ ({n.coordinates[0]*1000:.2f},{n.coordinates[1]*1000:.2f},{n.coordinates[2]*1000:.2f})mm")
                    break

# Frame 1
print("\n--- Frame 1 of Step-2 ---")
frame1 = step.frames[1]
nt1 = frame1.fieldOutputs['NT11']
hottest = []
for v in nt1.values:
    iname = node_to_inst.get(v.nodeLabel)
    if iname and 'POWDER' in iname.upper() and v.data > 500:
        hottest.append((v.data, v.nodeLabel))
hottest.sort(key=lambda x: x[0], reverse=True)
print(f"  Nodes > 500C in powder: {len(hottest)}")
for t, nl in hottest[:5]:
    for inst in odb.rootAssembly.instances.values():
        if 'POWDER' in inst.name.upper():
            for n in inst.nodes:
                if n.label == nl:
                    print(f"    Node {nl}: {t:.0f}C @ ({n.coordinates[0]*1000:.2f},{n.coordinates[1]*1000:.2f},{n.coordinates[2]*1000:.2f})mm")
                    break

# Also check: is Step-1 initial temp set correctly?
print("\n--- Step-1 (kill step) ---")
step1 = odb.steps['Step-1']
f1 = step1.frames[-1]
nt1f = f1.fieldOutputs['NT11']
powder_20 = 0
powder_300 = 0
for v in nt1f.values:
    iname = node_to_inst.get(v.nodeLabel)
    if iname and 'POWDER' in iname.upper():
        if abs(v.data - 20) < 5:
            powder_20 += 1
        elif abs(v.data - 300) < 5:
            powder_300 += 1
print(f"  Powder at ~20C: {powder_20}, at ~300C: {powder_300}")

odb.close()
