"""Debug: check step existence check behavior"""
from odbAccess import openOdb
odb = openOdb('ortho3t_P800_V5.odb', readOnly=True)

sn = 'Step-121'
print(f"Type of odb.steps: {type(odb.steps)}")
print(f"'Step-121' in odb.steps: {sn in odb.steps}")
print(f"Step-121 exists: {odb.steps.has_key(sn) if hasattr(odb.steps, 'has_key') else 'no has_key'}")

# Try direct access
try:
    s = odb.steps[sn]
    print(f"odb.steps['Step-121'] OK, frames={len(s.frames)}")
except:
    print("odb.steps['Step-121'] FAILED")

# Check what happens with sname
def test(sname):
    if sname not in odb.steps:
        print(f"  '{sname}' NOT in odb.steps")
        return 0
    print(f"  '{sname}' IN odb.steps -> frames={len(odb.steps[sname].frames)}")
    return 1

test('Step-121')
test('Step-242')
test('Step-363')

odb.close()
