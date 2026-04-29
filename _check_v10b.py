"""Step-2 frame-by-frame powder temp"""
from odbAccess import openOdb
odb = openOdb('hyb_v10.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

step2 = odb.steps['Step-2']
frames = step2.frames
print(f"Step-2 has {len(frames)} frames")

# Each frame's hottest powder
for i, f in enumerate(frames):
    nt = f.fieldOutputs['NT11']
    pow_max = 0
    sub_max = 0
    for v in nt.values:
        info = node_info.get(v.nodeLabel)
        if info:
            nm, c = info
            if nm == 'POWDER-1' and v.data > pow_max:
                pow_max = v.data
            if nm == 'SUBSTRATE-1' and v.data > sub_max:
                sub_max = v.data
    print(f"  Frame {i}: StepTime={f.frameValue:.6f}s  PowderMax={pow_max:.0f}C  SubstrateMax={sub_max:.0f}C")

odb.close()
