#!/usr/bin/env python3
"""分析所有短 INP 结果"""
import os, sys, glob
import numpy as np

WORKDIR = "/mnt/d/temp/duoceng3"
CASES = ["P800_V3", "P800_V5", "P800_V8",
         "P1000_V3", "P1000_V5", "P1000_V8",
         "P1200_V3", "P1200_V5", "P1200_V8"]

results = {}

for case in CASES:
    odb_path = os.path.join(WORKDIR, f"short_{case}.odb")
    for_path = os.path.join(WORKDIR, f"a_for_{case}.for")
    
    if not os.path.exists(odb_path):
        print(f"  {case}: ODB not found, skipping")
        continue
    
    # 提取参数
    with open(for_path, "r") as f:
        content = f.read()
    import re
    m = re.search(r"LASER_POWER\s*=\s*([\d.]+)D0", content)
    power = float(m.group(1)) if m else 0
    m = re.search(r"ABSORPTIVITY\s*=\s*([\d.]+)D0", content)
    eta = float(m.group(1)) if m else 0
    m = re.search(r"SCAN_SPEED\s*=\s*([\d.]+)D0", content)
    speed = float(m.group(1)) if m else 0
    m = re.search(r"DT_PER_STEP\s*=\s*([\d.]+)D0", content)
    dt = float(m.group(1)) if m else 0
    
    # 通过 Abaqus Python 提取温度
    cmd = f'cmd.exe /c "abaqus cae nogui=_extract_peak.py -- {case}"'
    os.system(cmd)
    
    print(f"  {case}: P={power:.0f}W, v={speed*1000:.1f}mm/s, DT={dt:.3f}s -> see {case}_result.txt")

print("\n=== 汇总 ===")
for case in CASES:
    result_file = os.path.join(WORKDIR, f"{case}_result.txt")
    if os.path.exists(result_file):
        with open(result_file, "r") as f:
            print(f"  {case}: {f.read().strip()}")
