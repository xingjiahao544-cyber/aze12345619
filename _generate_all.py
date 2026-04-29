#!/usr/bin/env python3
"""
Generate all files for duoceng3 orthogonal experiment (eta=0.40)
Creates:
  1. 9 FOR files with correct DT_PER_STEP
  2. 9 short INP files (8 heating steps + 1 cooling, for Layer 1 only)
  3. Submission scripts
"""
import math, os

CURRENT_DIR = "/mnt/d/temp/duoceng3"
WIN_DIR = "D:/temp/duoceng3"

# === Orthogonal parameters ===
powers = [800, 1000, 1200]
speeds = [3, 5, 8]
eta = 0.40

# Load template FOR
with open(f"{CURRENT_DIR}/a_for_hybrid.for", "r") as f:
    for_template = f.read()

# ==================== 1. Generate 9 FOR files ====================
print("=== Generating FOR files ===")

for power in powers:
    for speed in speeds:
        case = f"P{power}_V{speed}"
        dt_per_step = 0.0006 / (speed / 1000.0)  # 0.6mm per layer / speed
        
        # Copy template and replace PARAMETER lines
        new_for = for_template.replace(
            "      PARAMETER (LASER_POWER = 1000.0D0, ABSORPTIVITY = 0.4D0)",
            f"      PARAMETER (LASER_POWER = {power}.0D0, ABSORPTIVITY = 0.4D0)"
        ).replace(
            "      PARAMETER (SCAN_SPEED = 0.005D0)",
            f"      PARAMETER (SCAN_SPEED = {speed/1000.0:.4f}D0)"
        ).replace(
            "      PARAMETER (DT_PER_STEP = 0.12D0)",
            f"      PARAMETER (DT_PER_STEP = {dt_per_step:.6f}D0)"
        )
        
        # Also update the comment header if present
        new_for = new_for.replace(
            "C     基于 duoceng3 的 123 步结构",
            f"C     基于 duoceng3 的 123 步结构 | P={power}W, v={speed}mm/s, η={eta}"
        )
        
        filename = f"a_for_hybrid_{case}.for"
        with open(f"{CURRENT_DIR}/{filename}", "w") as f:
            f.write(new_for)
        print(f"  Created: {filename} (DT_PER_STEP={dt_per_step:.6f}s)")

# ==================== 2. Parse INP structure ====================
print("\n=== Parsing INP structure ===")

with open(f"{CURRENT_DIR}/LaserCladding-316L.inp", "rb") as f:
    inp_raw = f.read()

# For short INP: only need header + Step-1 + Step-2~9 + Step-42 (cooling)
# Step 2-41 are heating steps for Layer 1 (40 steps)
# Step 42 is cooling
# Short: 8 heating steps (Step-2~9) + Step-42 (cooling)

# Find step boundaries
step_starts = {}
pos = 0
while True:
    step_marker = inp_raw.find(b"** STEP: Step-", pos)
    if step_marker == -1:
        break
    # Extract step number
    line_end = inp_raw.find(b"\n", step_marker)
    step_line = inp_raw[step_marker:line_end].decode('ascii', errors='replace')
    step_num = int(step_line.split("Step-")[1].split()[0].strip())
    step_starts[step_num] = step_marker
    pos = step_marker + 1

print(f"Found {len(step_starts)} steps: {sorted(step_starts.keys())}")
print(f"Step-1 start: {step_starts[1]}")

# Header is everything before Step-1
header_end = step_starts[1]
header = inp_raw[:header_end]

# Cooling step (Step-42)
cooling_start = step_starts[42]
cooling_end = step_starts[83]  # Step-83 is next cooling (Layer 2 cooling)

print(f"Header: {header_end} bytes")
print(f"Step-42 (cooling): {cooling_start} to {cooling_end} ({cooling_end - cooling_start} bytes)")

# ==================== 3. Generate 9 short INPs ====================
print("\n=== Generating short INP files ===")

# Short INP: Header + Step-1 + Step-2~9 (8 heating steps) + Step-42 (cooling)
# We need to keep the step names consistent

# Build short INP from:
# 1. Header (model definition)
# 2. Step-1 (kill step)
# 3. Step-2 through Step-9 (8 heating steps)
# 4. Step-42 (Layer 1 cooling, but rename to Step-10)

step1_data = inp_raw[step_starts[1]:step_starts[2]]
step2_data = inp_raw[step_starts[2]:step_starts[3]]
step3_data = inp_raw[step_starts[3]:step_starts[4]]
step4_data = inp_raw[step_starts[4]:step_starts[5]]
step5_data = inp_raw[step_starts[5]:step_starts[6]]
step6_data = inp_raw[step_starts[6]:step_starts[7]]
step7_data = inp_raw[step_starts[7]:step_starts[8]]
step8_data = inp_raw[step_starts[8]:step_starts[9]]
step9_data = inp_raw[step_starts[9]:step_starts[10]]

step42_data = inp_raw[step_starts[42]:step_starts[83]]

# Check step format to ensure correct renumbering
print(f"Step-2 raw[:50]: {step2_data[:50]}")
print(f"Step-42 raw[:50]: {step42_data[:50]}")

# Build short INP for each speed (time increments differ by speed)
# Actually the time increments in the INP are fixed, only the FOR file changes dt
# So short INP is the same for all cases

short_inp = header + step1_data + step2_data + step3_data + step4_data + \
            step5_data + step6_data + step7_data + step8_data + step9_data + \
            step42_data

print(f"Short INP total: {len(short_inp)} bytes")

# Renumber steps in short INP: Step-2~9 become Step-2~9 (unchanged in short version)
# Step-42 stays as Step-42 (just as the cooling step)
# Actually for the short model, we'll just use Step-8 (last heating step) for extraction
# Keep step numbers as-is for simplicity

with open(f"{CURRENT_DIR}/short_template.inp", "wb") as f:
    f.write(short_inp)
print("  Saved: short_template.inp (same for all cases)")

# Actually each case needs different dt_per_step in the time increment lines
# The INP time increments need to be adjusted
# Let's modify the time increment lines per case

for power in powers:
    for speed in speeds:
        case = f"P{power}_V{speed}"
        dt_per_step = 0.0006 / (speed / 1000.0)
        
        # Build with correct time increments
        inp_out = bytearray(header)
        
        # Step-1 (kill step, keep original)
        inp_out.extend(step1_data)
        
        # Step-2~9 (heating steps, modify time increments)
        for si, step_data in enumerate([step2_data, step3_data, step4_data, 
                                         step5_data, step6_data, step7_data,
                                         step8_data, step9_data]):
            step_num = si + 2
            # Modify: initInc, totalTime/period, minInc, maxInc
            # Original: 0.012, 0.12, 1.2e-05, 0.12
            initInc = dt_per_step / 10.0  # 1/10 of step time
            period = dt_per_step
            minInc = dt_per_step / 10000.0
            maxInc = dt_per_step
            
            # Replace the time increment line
            old_line = b"0.012, 0.12, 1.2e-05, 0.12, "
            new_line = f"{initInc:.6f}, {period:.6f}, {minInc:.10e}, {maxInc:.6f}, ".encode()
            
            step_modified = step_data.replace(old_line, new_line, 1)
            inp_out.extend(step_modified)
        
        # Step-42 (cooling, keep original)
        inp_out.extend(step42_data)
        
        out_filename = f"short_{case}.inp"
        with open(f"{CURRENT_DIR}/{out_filename}", "wb") as f:
            f.write(bytes(inp_out))
        print(f"  Created: {out_filename} ({len(inp_out)} bytes, dt={dt_per_step:.6f}s)")

# ==================== 4. Generate submission script ====================
print("\n=== Generating submission script ===")

submit_script = """#!/bin/bash
# Submit all 9 short INP cases for duoceng3 orthogonal experiment
# eta=0.40, hybrid heat source
cd /mnt/d/temp/duoceng3

CASES=("P800_V3" "P800_V5" "P800_V8" "P1000_V3" "P1000_V5" "P1000_V8" "P1200_V3" "P1200_V5" "P1200_V8")

for case in "${CASES[@]}"; do
  echo "Submitting: $case"
  cmd.exe /c "abaqus job=short_${case} user=D:/temp/duoceng3/a_for_hybrid_${case}.for int ask=OFF" &
  # Wait 10s between submissions to avoid license contention
  sleep 10
done

echo "All 9 cases submitted"
echo "Run: process(action='poll') to check status"
"""

with open(f"{CURRENT_DIR}/_submit_all.sh", "w") as f:
    f.write(submit_script)
os.chmod(f"{CURRENT_DIR}/_submit_all.sh", 0o755)
print("  Created: _submit_all.sh")

# ==================== 5. Generate extraction script ====================
print("\n=== Generating extraction script ===")

extract_script = '''"""
Extract short INP results for duoceng3 orthogonal experiment
Uses Step-8 (last heating step) for comparison
"""
from odbAccess import openOdb
import sys

CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

T_LIQ = 1400.0

print("="*90)
print("Hybrid Heat Source 3x3 Orthogonal Experiment (eta=0.40, short INP)")
print("="*90)
print(f"{'Case':>12s}  {'P(W)':>6s}  {'v(mm/s)':>8s}  {'Q(W)':>6s}  {'Tmax(C)':>8s}  {'Nhot':>5s}  {'W(mm)':>6s}  {'D(mm)':>6s}  {'L(mm)':>6s}  {'IW(mm)':>6s}")
print("-"*92)

for case in CASES:
    parts = case.split('_')
    power = int(parts[0].replace('P',''))
    speed = int(parts[1].replace('V',''))
    q = power * 0.4
    
    odb = openOdb(f'short_{case}.odb', readOnly=True)
    
    # Build node coords
    node_coords = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_coords[(inst.name, n.label)] = (
                n.coordinates[0], n.coordinates[1], n.coordinates[2])
    
    node_inst = {}
    for inst in odb.rootAssembly.instances.values():
        for el in inst.elements:
            for nl in el.connectivity:
                node_inst[nl] = inst.name
    
    # Step-8 = last heating step  
    step = odb.steps['Step-8']
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    ninc = len(step.frames)
    
    tmax = max(v.data for v in nt.values)
    
    # Melt pool
    hot = []
    sub_hot = []
    for v in nt.values:
        iname = node_inst.get(v.nodeLabel, list(node_coords.keys())[0][0])
        key = (iname, v.nodeLabel)
        if key in node_coords:
            c = node_coords[key]
            if v.data >= T_LIQ:
                hot.append((v.data, c[0]*1000, c[1]*1000, c[2]*1000))
                # Substrate Y < SUB_D = 4.8mm
                if c[1] < 0.0048:
                    sub_hot.append(v.data)
    
    sub_tmax = max(sub_hot) if sub_hot else 0
    
    if hot:
        xs = [h[1] for h in hot]; ys = [h[2] for h in hot]; zs = [h[3] for h in hot]
        w = max(xs)-min(xs); d = max(ys)-min(ys); l = max(zs)-min(zs)
        
        # Interface width at Y = SUB_D (4.8mm)
        interface_x = [h[1] for h in hot if abs(h[2] - 4.8) < 0.15]
        iw = max(interface_x)-min(interface_x) if interface_x else 0
        
        print(f"{case:>12s}  {power:6d}  {speed:8d}  {q:6.0f}  {tmax:8.1f}  {len(hot):5d}  {w:6.3f}  {d:6.3f}  {l:6.3f}  {iw:6.3f}")
    else:
        print(f"{case:>12s}  {power:6d}  {speed:8d}  {q:6.0f}  {tmax:8.1f}      0      -      -      -      -")
    
    # Save individual result
    with open(f'D:\\\\temp\\\\duoceng3\\\\_{case}_result.txt', 'w') as rf:
        rf.write(f"{case}: Q={q:.0f}W v={speed}mm/s | Tmax={tmax:.0f}C | SubTmax={sub_tmax:.0f}C | "
                 f"Pool:N={len(hot)} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm IW={iw:.3f}mm | Step=Step-8\\n")
        rf.write(f"Q={q:.0f}W v={speed}mm/s\\n")
        rf.write(f"PeakT={tmax:.0f}C\\n")
        rf.write(f"MaxPowderT={tmax:.0f}C MaxSubT={sub_tmax:.0f}C\\n")
        if hot:
            rf.write(f"MeltPool:N={len(hot)} W={w:.3f}mm D={d:.3f}mm L={l:.3f}mm IW={iw:.3f}mm\\n")
        rf.write(f"LastStep=Step-8\\n")
    
    odb.close()

print("-"*92)
'''

with open(f"{CURRENT_DIR}/_extract_short_v2.py", "w") as f:
    f.write(extract_script)
print("  Created: _extract_short_v2.py")

print("\n=== DONE ===")
print("Generated:")
print("  - 9 FOR files (a_for_hybrid_P*_V*.for)")
print("  - 9 short INP files (short_P*_V*.inp)")
print("  - _submit_all.sh (submission script)")
print("  - _extract_short_v2.py (extraction script)")
