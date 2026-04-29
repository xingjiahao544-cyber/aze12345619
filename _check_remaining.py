"""Check remaining ortho ODBs"""
from odbAccess import openOdb

for case in ['P800_V3', 'P800_V5', 'P800_V8', 'P1000_V3', 'P1000_V5', 'P1000_V8', 'P1200_V3', 'P1200_V5', 'P1200_V8']:
    try:
        odb = openOdb(f'ortho_{case}.odb', readOnly=True)
        steps = list(odb.steps.keys())
        last = steps[-1]
        nframes = len(odb.steps[last].frames) if odb.steps[last].frames else 0
        print(f"{case}: steps={len(steps)} last={last} frames={nframes}")
        odb.close()
    except Exception as e:
        print(f"{case}: {e}")
