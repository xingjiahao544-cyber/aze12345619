"""Check short_P1000_V5 - the one that worked"""
from odbAccess import openOdb
odb = openOdb('short_P1000_V5.odb', readOnly=True)

node_info = {}
for inst in odb.rootAssembly.instances.values():
    for n in inst.nodes:
        node_info[n.label] = (inst.name, n.coordinates)

for sname in ['Step-2', 'Step-4', 'Step-6', 'Step-8']:
    if sname not in odb.steps:
        continue
    step = odb.steps[sname]
    f = step.frames[-1]
    nt = f.fieldOutputs['NT11']
    
    tmax = 0
    powder_max = 0
    for v in nt.values:
        if v.data > tmax: tmax = v.data
        info = node_info.get(v.nodeLabel)
        if info:
            nm, c = info
            if nm == 'POWDER-1' and v.data > powder_max:
                powder_max = v.data
    print(f"{sname}: Tmax={tmax:.0f}C  PowderMax={powder_max:.0f}C")

# Check which element set was used for Dflux
# Read the inp filename from job info? Can't. But we know it was short_P1000_V5.inp
# Let's see the Dflux reference
import subprocess
result = subprocess.run(['grep', 'BFNU', 'short_P1000_V5.inp'], capture_output=True, text=True)
print(f"\nDflux ref in short_P1000_V5.inp: {result.stdout.strip()}")
result2 = subprocess.run(['grep', '-A2', 'Elset, elset=Powder-1.Set-Kill\|Elset, elset=All-Elements', 'short_P1000_V5.inp'], capture_output=True, text=True)
print(f"Elset definitions: {result2.stdout[:500]}")

odb.close()
