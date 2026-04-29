#!/usr/bin/env python3
"""Fix ALL INP cooling steps to be ultra-conservative + boost deltmx for 3mm/s."""
import os, glob, re

inp_files = sorted(glob.glob('ortho3t_P*.inp'))

cooling_old = b'1e-06, 10., 1e-07, 2.,'
cooling_new = b'1e-08, 10., 1e-10, 2.,'

# 3mm/s groups need higher deltmx on heating steps
slow_groups = ['P800_V3', 'P1000_V3']  # P1200_V3 already = 150
extra_hot = ['P1200_V3']  # already has 150

for inp_path in inp_files:
    with open(inp_path, 'rb') as f:
        content = f.read()
    
    # 1. Fix cooling step parameters
    c = content.count(cooling_old)
    if c > 0:
        content = content.replace(cooling_old, cooling_new)
        print(f"{inp_path}: cooling initInc 1e-06 -> 1e-08 ({c} matches)")
    
    # 2. Fix deltmx for 3mm/s groups
    case_name = os.path.basename(inp_path).replace('ortho3t_', '').replace('.inp', '')
    if case_name in slow_groups:
        # deltmx=50 -> deltmx=100 (but not cooling steps with deltmx=200)
        old_dt = b'deltmx=50.'
        new_dt = b'deltmx=100.'
        cnt = content.count(old_dt)
        if cnt > 0:
            content = content.replace(old_dt, new_dt)
            print(f"  deltmx 50->100: {cnt} matches")
    
    # 3. Verify cooling steps have cooling_new
    if cooling_new not in content:
        print(f"  WARNING: cooling step not fixed!")
    
    with open(inp_path, 'wb') as f:
        f.write(content)

print("\nDone! All INPs updated.")
