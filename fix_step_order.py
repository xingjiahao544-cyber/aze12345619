#!/usr/bin/env python3
"""Fix INP: move *Model Change after *Heat Transfer in each step."""
import os, sys

inp = sys.argv[1]
bak = inp + '.bak'
tmp = inp + '.tmp'

os.rename(inp, bak)
print(f"Backup: {bak}")

with open(bak, 'rb') as f:
    lines = f.read().split(b'\r\n')

out = []
i = 0
fixed = 0

while i < len(lines):
    line = lines[i]
    upper = line.strip().upper()
    
    # Detect *Step (except Step-1)
    if upper.startswith(b'*STEP') and upper != b'*STEP, NAME=STEP-1' and not upper.startswith(b'*STEP, NAME=STEP-1,'):
        # Scan for *Model Change, add right after
        j = i + 1
        while j < len(lines) and lines[j].strip() == b'':
            j += 1
        
        mc_lines = []
        found_mc = False
        
        if j < len(lines) and lines[j].strip().upper().startswith(b'*MODEL CHANGE'):
            found_mc = True
            k = j
            while k < len(lines):
                lu = lines[k].strip().upper()
                if lu.startswith(b'*HEAT TRANSFER'):
                    break
                if k > j and lu.startswith(b'*STEP'):
                    break
                if k > j and lu.startswith(b'** STEP:'):
                    break
                if k > j and lu.startswith(b'*END STEP'):
                    break
                mc_lines.append(lines[k])  # always include
                k += 1
            ht_line = lines[k]
            time_line = lines[k+1] if k+1 < len(lines) else b''
            after_time = k + 2
        else:
            ht_line = None
            time_line = None
            after_time = 0
        
        if found_mc:
            out.append(line)      # *Step
            out.append(ht_line)   # *Heat Transfer
            out.append(time_line) # time values
            for mc in mc_lines:
                if mc.strip():
                    out.append(mc)
            i = after_time
            fixed += 1
        else:
            out.append(line)
            i += 1
    else:
        out.append(line)
        i += 1

with open(tmp, 'wb') as f:
    f.write(b'\r\n'.join(out))

os.replace(tmp, inp)
print(f"Fixed {fixed} steps")
print("Done!")
