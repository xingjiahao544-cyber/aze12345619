#!/usr/bin/env python3
"""Fix cooling step in INP: reduce initInc from 0.1 to 1e-06 for better convergence."""
import sys, os

inp = sys.argv[1]
bak = inp + '.bak.cool'

if os.path.exists(bak):
    with open(bak, 'rb') as f:
        content = f.read()
else:
    with open(inp, 'rb') as f:
        content = f.read()
    with open(bak, 'wb') as f:
        f.write(content)
    print(f"Backup: {bak}")

# Find cooling steps: *Heat Transfer with deltmx=200.
# Replace the time line after it (0.1, 10., 1.2e-05, 2.,)
# with (1e-06, 10., 1e-07, 2.,)
old = b'0.1, 10., 1.2e-05, 2.,'
new = b'1e-06, 10., 1e-07, 2.,'

count = content.count(old)
if count == 0:
    print(f"No cooling step pattern found! Tried: {old}")
    # Show what we have
    for line in content.split(b'\r\n'):
        if b'deltmx=200' in line:
            print(f"  Found deltmx=200 at: {line}")
else:
    content = content.replace(old, new)
    with open(inp, 'wb') as f:
        f.write(content)
    print(f"Fixed {count} cooling step initInc: 0.1 -> 1e-06")
