# Abaqus Python script to extract peak temperature from a short ODB
# Usage: abaqus cae nogui=_extract_peak.py -- <case_name>
import sys, os

# Parse case name from arguments
case_name = "P1000_V3"
for a in sys.argv:
    if a.startswith("P") and "_V" in a and len(a) <= 12:
        case_name = a
        break

# Parse P and V from case name
parts = case_name.split("_")
power = int(parts[0].replace("P", ""))
speed_mms = int(parts[1].replace("V", ""))
speed_ms = speed_mms / 1000.0
eta = 0.4
Q = power * eta

workdir = r"D:\temp\duoceng3"
odb_path = os.path.join(workdir, f"short_{case_name}.odb")

print(f"=== Analyzing {case_name}: P={power}W, v={speed_mms}mm/s, Q={Q}W ===")

from odbAccess import openOdb
from abaqusConstants import *
import numpy as np

odb = openOdb(path=odb_path, readOnly=True)

# Get last frame of the LAST HEATING step (not cooling step)
all_steps = list(odb.steps.keys())
step_names_filtered = [s for s in all_steps if s != "Step-42" and s != "Step-1"]
last_heating_step_name = step_names_filtered[-1] if step_names_filtered else all_steps[-2]
step = odb.steps[last_heating_step_name]
last_frame = step.frames[-1] if step.frames else None
last_step_name = last_heating_step_name

temp_field = last_frame.fieldOutputs["NT11"]
vals = temp_field.values

# Collect coords + temperatures
node_temps = []
for v in vals:
    node_label = v.nodeLabel
    try:
        coord = v.instance.getNodeFromLabel(node_label).coordinates
        node_temps.append((coord[0], coord[1], coord[2], v.data))
    except:
        pass

nt = np.array(node_temps)
tmax = float(np.max(nt[:, 3]))
peak_idx = np.argmax(nt[:, 3])
px, py, pz, pt = nt[peak_idx]

# Ranges
pow_x0, pow_x1 = 0.0081, 0.0099
sub_y = 0.0048
melt_T = 1400.0

in_powder = (nt[:, 0] >= pow_x0) & (nt[:, 0] <= pow_x1) & (nt[:, 1] >= sub_y)
p_tmax = float(np.max(nt[in_powder, 3])) if np.any(in_powder) else 0

in_sub = nt[:, 1] < sub_y
s_tmax = float(np.max(nt[in_sub, 3])) if np.any(in_sub) else 0

# Melt pool stats
melted = nt[nt[:, 3] > melt_T]
n_melted = len(melted)

if n_melted > 0:
    w = float(np.max(melted[:, 0]) - np.min(melted[:, 0])) * 1000
    d = float(np.max(melted[:, 1]) - np.min(melted[:, 1])) * 1000
    l = float(np.max(melted[:, 2]) - np.min(melted[:, 2])) * 1000
    interface = melted[np.abs(melted[:, 1] - sub_y) < 0.0003]
    iw = float(np.max(interface[:, 0]) - np.min(interface[:, 0])) * 1000 if len(interface) > 0 else 0
else:
    w = d = l = iw = 0

odb.close()

# Build result string
if n_melted > 0:
    summary = (f"{case_name}: Q={Q}W v={speed_mms}mm/s | "
               f"Tmax={tmax:.0f}C @({px*1000:.2f},{py*1000:.2f},{pz*1000:.2f})mm | "
               f"SubTmax={s_tmax:.0f}C | "
               f"Pool:N={n_melted} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm IW={iw:.3f}mm | "
               f"Step={last_step_name}")
else:
    summary = (f"{case_name}: Q={Q}W v={speed_mms}mm/s | "
               f"Tmax={tmax:.0f}C | SubTmax={s_tmax:.0f}C | NO MELT POOL | "
               f"Step={last_step_name}")

print(summary)

# Write result file
result_path = os.path.join(workdir, f"_{case_name}_result.txt")
with open(result_path, "w") as f:
    f.write(summary + "\n")
    f.write(f"Q={Q}W v={speed_mms}mm/s\n")
    f.write(f"PeakT={tmax:.0f}C at ({px*1000:.4f},{py*1000:.4f},{pz*1000:.4f})mm\n")
    f.write(f"MaxPowderT={p_tmax:.0f}C MaxSubT={s_tmax:.0f}C\n")
    f.write(f"MeltPool:N={n_melted} W={w:.4f}mm D={d:.4f}mm L={l:.4f}mm IW={iw:.4f}mm\n")
    f.write(f"LastStep={last_step_name}\n")
