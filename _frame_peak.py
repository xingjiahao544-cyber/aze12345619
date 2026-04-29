"""
Check ALL frames of Step-2 to find the peak temperature
"""
from odbAccess import openOdb

odb = openOdb('short_P1000_V5.odb', readOnly=True)

node_to_inst = {}
for inst_name, inst in odb.rootAssembly.instances.items():
    for n in inst.nodes:
        node_to_inst[n.label] = inst_name

for sn in ['Step-2', 'Step-3', 'Step-5', 'Step-8']:
    step = odb.steps[sn]
    max_powder_across_frames = []
    
    for fi, frame in enumerate(step.frames):
        nt = frame.fieldOutputs['NT11']
        max_t_powder = -1
        for v in nt.values:
            iname = node_to_inst.get(v.nodeLabel)
            if iname and 'POWDER' in iname.upper() and v.data > max_t_powder:
                max_t_powder = v.data
        max_powder_across_frames.append((fi, max_t_powder))
    
    # Find peak frame
    peak = max(max_powder_across_frames, key=lambda x: x[1])
    print(f"{sn}: {len(step.frames)} frames, peak powder T={peak[1]:.0f}C at frame {peak[0]}")
    
    # Show first 5 and last 3
    for fi, t in max_powder_across_frames[:5]:
        print(f"  Frame {fi}: {t:.1f}C")
    if len(max_powder_across_frames) > 8:
        print(f"  ...")
        for fi, t in max_powder_across_frames[-3:]:
            print(f"  Frame {fi}: {t:.1f}C")

odb.close()
