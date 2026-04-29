"""Deep check - why is powder not hot?"""
from odbAccess import openOdb
odb = openOdb('hyb_v6.odb', readOnly=True)

# Powder node coords
inst = odb.rootAssembly.instances['POWDER-1']

print("=== Powder Y range ===")
ys = [n.coordinates[1]*1000 for n in inst.nodes]
print(f"Y: {min(ys):.2f} ~ {max(ys):.2f} mm")

step = odb.steps['Step-8']
f = step.frames[-1]
nt = f.fieldOutputs['NT11']

# Get all node temps by instance
node_inst = {}
for inst_name, inst_ in odb.rootAssembly.instances.items():
    for n in inst_.nodes:
        node_inst[n.label] = (inst_name, n.coordinates)

powder_temps = []
for v in nt.values:
    tup = node_inst.get(v.nodeLabel, ('', None))
    if tup is None:
        continue
    iname, coord = tup
    if 'POWDER' in iname.upper():
        powder_temps.append((v.data, coord[0]*1000, coord[1]*1000, coord[2]*1000, v.nodeLabel))

print(f"\n=== Powder nodes (>100C): {len(powder_temps)} total ===")
powder_temps.sort(key=lambda x: -x[0])
for t, x, y, z, nl in powder_temps[:20]:
    print(f"  Node {nl:>5d}: T={t:.0f}C @ X={x:.2f}mm Y={y:.2f}mm Z={z:.2f}mm")

# Check Y0 for current layer
# KSTEP=9 (Step-9): Layer 1, ACTIVE_STEP=8
# Y0 = SUB_D + 1*LAYER_T = 4.8 + 0.6 = 5.4mm
# DY = Y - Y0 for powder: min=-0.6, max=0  
# Should be within [-0.0006, 0]
print("\n=== Heating check for Step-9 (should be at Z~4.8mm) ===")
step9 = odb.steps['Step-9']
f9 = step9.frames[-1]
nt9 = f9.fieldOutputs['NT11']

powder_hot9 = []
for v in nt9.values:
    tup9 = node_inst.get(v.nodeLabel, ('', None))
    if tup9 is None:
        continue
    iname, coord = tup9
    if 'POWDER' in iname.upper() and v.data > 100:
        powder_hot9.append((v.data, coord, v.nodeLabel))

powder_hot9.sort(key=lambda x: -x[0])
print(f"Hottest powder nodes in Step-9: {len(powder_hot9)} >100C")
for t, coord, nl in powder_hot9[:10]:
    print(f"  Node {nl:>5d}: T={t:.0f}C @ X={coord[0]*1000:.2f}mm Y={coord[1]*1000:.2f}mm Z={coord[2]*1000:.2f}mm")

# Print Z_CURRENT for verification
import math
SCAN_SPEED = 0.005
STEP1_TIME = 10.0
# Step-9 ends at TIME(2) = 10.0 + 8*0.12 = 10.96
time_at_step9_end = 10.0 + 8*0.12
heating_time = time_at_step9_end - STEP1_TIME
z_total = SCAN_SPEED * heating_time
z_current = z_total  # Layer 1
print(f"\n=== Z position calc ===")
print(f"Step-9 end: TIME(2)={time_at_step9_end}s, heating_time={heating_time}s")
print(f"Z_TOTAL={z_total*1000:.2f}mm, Z_CURRENT(Layer1)={z_current*1000:.2f}mm")

# Check 202 steps - but we have Step-43~82 also. Let me check what ODB actually has
print(f"\n=== Full step list ===")
all_steps = list(odb.steps.keys())
print(f"Total steps in ODB: {len(all_steps)}")
print(f"First 10: {all_steps[:10]}")
print(f"Last 10: {all_steps[-10:]}")

odb.close()
