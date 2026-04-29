#!/usr/bin/env python3
"""
Batch generator for duoceng3 orthogonal experiment (hybrid heat source, eta=0.40)
Generates:
  1. 9 FOR files (a_for_hybrid_P{power}_V{speed}.for) with correct DT_PER_STEP
  2. 9 short INP files (short_{case}.inp) - only Layer 1, first 8 heating steps + 1 cooling
  3. Job submission script
"""
import os, math

# === Orthogonal experiment parameters ===
powers = [800, 1000, 1200]       # W
speeds = [3, 5, 8]               # mm/s
eta = 0.40

# Shape parameters (fixed)
F_SURF = 0.60
F_VOL = 0.40
R0_S = 0.00085
DEPTH_S = 0.0002
AF = 0.0020
AR = 0.0040
B = 0.00085
C = 0.0006

# For template references (from a_for_hybrid.for)
SUB_D = 0.0048   # substrate top Y
POW_X0 = 0.0081  # powder start X
LAYER_LENGTH = 0.024
Y_LAYER1 = SUB_D + 0.0003  # 0.0051

CURRENT_DIR = "/mnt/d/temp/duoceng3"
WIN_DIR = "D:/temp/duoceng3"

# === Template: a_for_hybrid.for ===
with open(f"{CURRENT_DIR}/a_for_hybrid.for", "r") as f:
    template = f.read()

# === Read base INP ===
with open(f"{CURRENT_DIR}/LaserCladding-316L.inp", "rb") as f:
    inp_raw = f.read()

# Split into header (model definition) + steps part
# Find first *Step line
header_end = inp_raw.find(b"\n** STEP: Step-1")
header = inp_raw[:header_end]

# Read the Step-1 block to understand the structure
step1_start = inp_raw.find(b"** STEP: Step-1", header_end)
step1_end = inp_raw.find(b"** STEP: Step-2", step1_start)

print(f"Header end at byte {header_end}")
print(f"Step-1 bytes: {step1_start}-{step1_end}")

# Read first 10 steps of the INP to understand repeating patterns
step2_start = inp_raw.find(b"** STEP: Step-2", step1_end)
step3_start = inp_raw.find(b"** STEP: Step-3", step2_start)
print(f"Step-1 size: {step1_end - step1_start}")
print(f"Step-2 start: {step2_start}, Step-3 start: {step3_start}")
print(f"Step-2 size: {step3_start - step2_start}")

# Let's look at the structure of a single heating step
step2_data = inp_raw[step2_start:step3_start]
print("\nStep-2 raw:")
print(repr(step2_data[:300]))
print("...")
print(repr(step2_data[-200:]))
