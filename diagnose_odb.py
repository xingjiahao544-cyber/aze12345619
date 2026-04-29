"""diagnose_odb.py — 检查 ODB 步名和框架数"""
from odbAccess import openOdb
import sys

case = sys.argv[-1]
odb = openOdb(f'ortho3t_{case}.odb', readOnly=True)

print(f"ODB: ortho3t_{case}.odb")
print(f"Steps in ODB: {len(list(odb.steps.keys()))}")

# List first & last 5 step names
steps = list(odb.steps.keys())
for s in steps[:5]:
    print(f"  Step: '{s}'")
print("  ...")
for s in steps[-5:]:
    print(f"  Step: '{s}'")

# Check our target steps
targets = ['Step-121', 'Step-242', 'Step-363']
for t in targets:
    exists = t in odb.steps
    frames = 0
    if exists:
        frames = len(odb.steps[t].frames)
    print(f"  Target '{t}': exists={exists}, frames={frames}")

# NT11 nodes
step = odb.steps[steps[-1]]
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
print(f"\nLast step '{steps[-1]}': {len(nt.values)} NT11 values")
print(f"  Max temp: {max(v.data for v in nt.values):.1f}C")

# Count nodes per instance
from collections import Counter
inst_counter = Counter()
for v in nt.values:
    inst_counter[v.instance.name] += 1
for name, cnt in inst_counter.most_common():
    print(f"  Instance '{name}': {cnt} nodes")

odb.close()
