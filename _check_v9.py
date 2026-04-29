"""Check hyb_v9 (STEP1_TIME=10.0, old version)"""
from odbAccess import openOdb
odb = openOdb('hyb_v9.odb', readOnly=True)

coords = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        coords[n.label] = (inst.name, n.coordinates)

for sname in ['Step-2', 'Step-5', 'Step-8', 'Step-42']:
    if sname not in odb.steps:
        continue
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    vals = list(nt.values)
    tmax = max(v.data for v in vals)
    
    pow_temps = [v.data for v in vals if coords.get(v.nodeLabel,('',))[0]=='POWDER-1']
    pow_tmax = max(pow_temps) if pow_temps else 0
    pow_hot = sum(1 for t in pow_temps if t>=500)
    
    print(f"{sname}: Tmax={tmax:.0f}C  PowderTmax={pow_tmax:.0f}C  Powder>500C={pow_hot}")

# Check Z positions by finding hottest powder node
step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']
hots = []
for v in nt.values:
    if v.nodeLabel in coords:
        nm, c = coords[v.nodeLabel]
        if nm == 'POWDER-1':
            hots.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
hots.sort(key=lambda x: -x[0])
print(f"\nHottest powder nodes Step-8:")
for t, x, y, z in hots[:5]:
    print(f"  T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

print(f"\nTotal Time at Step-8 end:")
print(f"Step-1: 0.1s, Step-2~8: 7*0.12=0.84s, Total=0.94s")
print(f"If STEP1_TIME=10.0: HEAT_TIME=0.94-10=-9.06→0, Z=0mm (WRONG!)")
print(f"If STEP1_TIME=0.1:  HEAT_TIME=0.94-0.1=0.84, Z=0.005*0.84=4.2mm (CORRECT!)")

odb.close()
