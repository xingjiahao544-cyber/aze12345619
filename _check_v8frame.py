"""Step-2 frame check for hyb_v8 (1e10 constant + Powder-1.All-Powder)"""
from odbAccess import openOdb
odb = openOdb('hyb_v8.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

step2 = odb.steps['Step-2']
frames = step2.frames
print(f"hyb_v8 Step-2 has {len(frames)} frames")
for i in range(min(5, len(frames))):
    f = frames[i]
    nt = f.fieldOutputs['NT11']
    pow_max = 0
    sub_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info:
            nm, c = info
            if nm == 'POWDER-1' and v.data > pow_max: pow_max = v.data
            if nm == 'SUBSTRATE-1' and v.data > sub_max: sub_max = v.data
    print(f"  Frame {i}: StepTime={f.frameValue:.4f}s  Powder={pow_max:.0f}C  Sub={sub_max:.0f}C")

# Last frame
f = frames[-1]
nt = f.fieldOutputs['NT11']
pow_max = 0
sub_max = 0
for v in nt.values:
    info = node_info.get(v.nodeLabel)
    if info:
        nm, c = info
        if nm == 'POWDER-1' and v.data > pow_max: pow_max = v.data
        if nm == 'SUBSTRATE-1' and v.data > sub_max: sub_max = v.data
print(f"  Frame {len(frames)-1}: StepTime={f.frameValue:.4f}s  Powder={pow_max:.0f}C  Sub={sub_max:.0f}C")

odb.close()
