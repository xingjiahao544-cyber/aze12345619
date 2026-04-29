"""Check hyb_v9 - NEW version (STEP1_TIME=0.1, Powder-1.All-Powder)"""
from odbAccess import openOdb
odb = openOdb('hyb_v9.odb', readOnly=True)

coords = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        coords[n.label] = (inst.name, n.coordinates)

print(f"Steps in ODB: {list(odb.steps.keys())[:12]}")

for sname in ['Step-2', 'Step-4', 'Step-6', 'Step-8']:
    if sname not in odb.steps:
        continue
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    vals = list(nt.values)
    tmax = max(v.data for v in vals)
    nframes = len(step.frames)
    
    pow_temps = []
    pow_max_t = 0
    for v in vals:
        tup = coords.get(v.nodeLabel)
        if tup:
            nm, c = tup
            if nm == 'POWDER-1':
                pow_temps.append(v.data)
                if v.data > pow_max_t:
                    pow_max_t = v.data
    
    pow_hot_1400 = sum(1 for t in pow_temps if t >= 1400)
    pow_hot_500 = sum(1 for t in pow_temps if t >= 500)
    
    print(f"  {sname}: Tmax={tmax:.0f}C  PowderTmax={pow_max_t:.0f}C  "
          f"Powder>500={pow_hot_500}  Powder>1400={pow_hot_1400}  Nframes={nframes}")

# Detailed powder hotspot
step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

hots = []
for v in nt.values:
    tup = coords.get(v.nodeLabel)
    if tup:
        nm, c = tup
        if nm == 'POWDER-1':
            hots.append((v.data, v.nodeLabel, c[0]*1000, c[1]*1000, c[2]*1000))

hots.sort(key=lambda x: -x[0])
print(f"\n=== Step-8: Hottest powder nodes ({len(hots)} total) ===")
for t, nl, x, y, z in hots[:15]:
    print(f"  N{nl:>5d}: T={t:.0f}C @ X={x:.2f} Y={y:.2f} Z={z:.2f}")

# Check step times from STA
print(f"\n=== Expected Z positions ===")
import math
for sn in [2, 4, 6, 8]:
    heat_time = (sn - 2) * 0.12
    if sn == 2:
        heat_time += 0.12  # end of step
    z = 0.005 * heat_time
    print(f"  Step-{sn} end: HEAT_TIME={heat_time:.2f}s, Z={z*1000:.2f}mm")

# Step-1 total time
from sta_reader import parse_sta  # might not exist
# Let's just read from the sta file we know
print(f"\nStep-1 total time from design: period=0.1s")

# Check msg for zero heat flux
import subprocess
result = subprocess.run(['grep', '-c', 'ZERO HEAT FLUX', 'hyb_v9.msg'], capture_output=True, text=True)
print(f"\nZERO HEAT FLUX warnings: {result.stdout.strip() or '0'}")

result2 = subprocess.run(['grep', 'LARGEST INCREMENT', 'hyb_v9.msg'], capture_output=True, text=True)
lines = result2.stdout.strip().split('\n')
if lines:
    print(f"Last LARGEST INCREMENT: {lines[-1]}")

odb.close()
