"""检查 P800_V5 的 Step-2 温度"""
from odbAccess import openOdb
odb = openOdb('ortho3t_P800_V5.odb', readOnly=True)

step = odb.steps['Step-121']  # L1最后一步
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

from collections import Counter
inst_counter = Counter()
by_inst = {'POWDER-1-1': [], 'POWDER-2-1': [], 'POWDER-3-1': [], 'SUBSTRATE-1': []}

for v in nt.values:
    name = v.instance.name
    if name not in by_inst:
        by_inst[name] = []
    by_inst[name].append(v.data)

for name, temps in by_inst.items():
    if temps:
        print(f"{name}: max={max(temps):.1f}C, min={min(temps):.1f}C, n={len(temps)}")
    else:
        print(f"{name}: no data")

# Also check Step-2
print("\n=== Step-2 last frame ===")
step2 = odb.steps['Step-2']
f2 = step2.frames[-1]
nt2 = f2.fieldOutputs['NT11']
by_inst2 = {}
for v in nt2.values:
    n = v.instance.name
    if n not in by_inst2: by_inst2[n] = []
    by_inst2[n].append(v.data)
for n, ts in sorted(by_inst2.items()):
    print(f"  {n}: max={max(ts):.1f}C, min={min(ts):.1f}C, count={len(ts)}")
    
odb.close()
