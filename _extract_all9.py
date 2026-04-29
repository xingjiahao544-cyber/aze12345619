"""Full ortho results including P800"""
from odbAccess import openOdb

T_LIQ = 1400.0
CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

print(f"{'Case':>10s}  {'Q(W)':>6s}  {'v':>5s}  {'L1max':>7s}  {'L2max':>7s}  {'L3max':>7s}  {'L1n':>5s}  {'L2n':>5s}  {'L3n':>5s}  {'L1W':>5s}  {'L3W':>5s}  {'L3L':>5s}  {'SubMx':>6s}")
print("="*95)

for case in CASES:
    parts = case.split('_')
    power = int(parts[0].replace('P',''))
    speed = int(parts[1].replace('V',''))
    effq = power * 0.4
    
    odb = openOdb(f'ortho_{case}.odb', readOnly=True)
    
    node_info = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_info[n.label] = (inst.name, n.coordinates)
    
    def ana(sn):
        if sn not in odb.steps or not odb.steps[sn].frames:
            return 0,0,[]
        f = odb.steps[sn].frames[-1]
        nt = f.fieldOutputs['NT11']
        pm=0; pn=0; hots=[]
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0].upper() == 'POWDER-1':
                if v.data > pm: pm=v.data
                if v.data>=T_LIQ:
                    pn+=1
                    hots.append((info[1][0]*1000, info[1][2]*1000))
        return pm,pn,hots
    
    l1m,l1n,l1h = ana('Step-41')
    l2m,l2n,_ = ana('Step-82')
    l3m,l3n,l3h = ana('Step-122')
    
    l1w = max(h[0] for h in l1h)-min(h[0] for h in l1h) if l1h else 0
    l3w = max(h[0] for h in l3h)-min(h[0] for h in l3h) if l3h else 0
    l3l = max(h[1] for h in l3h)-min(h[1] for h in l3h) if l3h else 0
    
    sm = 0
    if 'Step-122' in odb.steps and odb.steps['Step-122'].frames:
        nt = odb.steps['Step-122'].frames[-1].fieldOutputs['NT11']
        for v in nt.values:
            info = node_info.get(v.nodeLabel)
            if info and info[0].upper() != 'POWDER-1' and v.data > sm:
                sm = v.data
    
    print(f"{case:>10s}  {effq:6.0f}  {speed:5d}  {l1m:7.0f}  {l2m:7.0f}  {l3m:7.0f}  {l1n:5d}  {l2n:5d}  {l3n:5d}  {l1w:5.1f}  {l3w:5.1f}  {l3l:5.1f}  {sm:6.0f}")
    odb.close()
