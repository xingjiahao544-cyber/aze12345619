# -*- coding: utf-8 -*-
"""
aze_3tracks_ortho.py — 三层三道 316L 正交实验 INP 生成
3 tracks x 40 Z-layers/layer x 3 Y-layers + cooling steps = 363 steps
可接受 P(功率) 和 v(扫描速度) 参数

用法：
  abaqus cae noGUI=aze_3tracks_ortho.py -- P1200_V5

将会生成 D:\temp\duoceng3\ortho3t_P1200_V5.inp
"""
from abaqus import *
from abaqusConstants import *
from caeModules import *
import regionToolset
import os, sys, math

sys.setrecursionlimit(10000)

def safe_print(msg):
    print(msg); sys.stdout.flush()

# ========== 读取参数 ==========
POWER = 1000       # 默认
SPEED = 0.005      # 5mm/s 默认
case_label = 'P1000_V5'

if len(sys.argv) >= 2 and sys.argv[-1].startswith('P') and '_' in sys.argv[-1]:
    case_label = sys.argv[-1]
    # Abaqus CAE 吞掉 --，参数在 sys.argv[-1]
    parts = case_label.split('_')
    if len(parts) == 2:
        power_str = parts[0].replace('P','')
        speed_str = parts[1].replace('V','')
        POWER = float(power_str)
        SPEED = float(speed_str) / 1000.0  # mm/s -> m/s

ABSORPTIVITY = 0.40
Q_TOTAL = POWER * ABSORPTIVITY
DT_PER_STEP = 0.0006 / SPEED  # 每步移动0.6mm

safe_print(f"===== 三道三层正交实验 =====")
safe_print(f"Case: {case_label}")
safe_print(f"P={POWER}W, v={SPEED*1000:.0f}mm/s, eta={ABSORPTIVITY}, Q={Q_TOTAL:.0f}W")
safe_print(f"dt_per_step = {DT_PER_STEP:.6f}s")

workdir = r'D:\temp\duoceng3'
os.makedirs(workdir, exist_ok=True)
os.chdir(workdir)

# ===================== 几何参数 =====================
sub_w, sub_d, sub_l = 0.018, 0.0048, 0.024
track_w, track_d, track_l = 0.0018, 0.0018, 0.024
num_tracks = 3
overlap_ratio = 0.30
track_pitch = track_w * (1.0 - overlap_ratio)
total_powder_w = track_w + (num_tracks - 1) * track_pitch
pow_x0 = (sub_w - total_powder_w) / 2.0
track_x_offsets = [pow_x0 + i * track_pitch for i in range(num_tracks)]

ABSOLUTE_ZERO = -273.15
STEFAN_BOLTZMANN = 5.670367e-8

# ===================== 创建模型 =====================
safe_print("Step 1: 创建模型...")
myModel = mdb.Model(name='Model-1')
myModel.setValues(absoluteZero=ABSOLUTE_ZERO, stefanBoltzmann=STEFAN_BOLTZMANN)

# ===================== 基板 Part =====================
safe_print("Step 2: 创建基板部件...")
sub_part = myModel.Part(name='Substrate', dimensionality=THREE_D, type=DEFORMABLE_BODY)
sketch_sub = myModel.ConstrainedSketch(name='__sub__', sheetSize=0.5)
sketch_sub.rectangle(point1=(0.0, 0.0), point2=(sub_w, sub_d))
sub_part.BaseSolidExtrude(sketch=sketch_sub, depth=sub_l)

# ===================== 三道粉道 Part =====================
safe_print("Step 3: 创建三道粉道部件...")
powder_parts = []
for t in range(num_tracks):
    name = f'Powder-{t+1}'
    part = myModel.Part(name=name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    sketch = myModel.ConstrainedSketch(name=f'__pow{t}__', sheetSize=0.5)
    sketch.rectangle(point1=(0.0, 0.0), point2=(track_w, track_d))
    part.BaseSolidExtrude(sketch=sketch, depth=track_l)
    powder_parts.append(part)
    safe_print(f"  创建 {name}")

# ===================== 材料 =====================
safe_print("Step 4: 创建材料...")
mat = myModel.Material(name='Material-1')
mat.Conductivity(temperatureDependency=ON, table=(
    (13.1,10),(14,100),(23,300),(36,500),(38,800),(35,1200),(70,1350),(100,1450),(130,1800),(170,3000)))
mat.SpecificHeat(temperatureDependency=ON, table=(
    (450,10),(500,100),(650,300),(750,500),(850,800),(780,1200),(920,1500),(800,1600),(800,3000)))
mat.Density(temperatureDependency=ON, table=(
    (7740,10),(7710,100),(7680,300),(7580,500),(7470,800),(7350,1200),(7000,1500),(6900,1600),(6900,3000)))
mat.LatentHeat(table=((270000, 1384.85, 1446.85),))

# ===================== 截面分配 =====================
safe_print("Step 5: 截面分配...")
sec = myModel.HomogeneousSolidSection(name='SolidSection', material='Material-1')
for part in [sub_part] + powder_parts:
    name = part.name
    region = part.Set(name=f'All-{name}', cells=part.cells)
    part.SectionAssignment(region=region, sectionName='SolidSection')

# ===================== 装配体 =====================
safe_print("Step 6: 装配体...")
a = myModel.rootAssembly
inst_sub = a.Instance(name='Substrate-1', part=sub_part, dependent=ON)
instances = [inst_sub]

for t in range(num_tracks):
    name = f'Powder-{t+1}'
    inst = a.Instance(name=f'{name}-1', part=powder_parts[t], dependent=ON)
    a.translate(instanceList=(f'{name}-1',), vector=(track_x_offsets[t], sub_d, 0.0))
    instances.append(inst)

# ===================== 网格 =====================
safe_print("Step 7: 网格划分...")
elem_type = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
sub_part.seedPart(size=0.0012, deviationFactor=0.1)
sub_part.setMeshControls(regions=sub_part.cells, elemShape=HEX, technique=SWEEP)
sub_part.setElementType(regions=(sub_part.cells,), elemTypes=(elem_type,))
sub_part.generateMesh()

for p in powder_parts:
    p.seedPart(size=0.0003, deviationFactor=0.1)
    p.setMeshControls(regions=p.cells, elemShape=HEX, technique=SWEEP)
    p.setElementType(regions=(p.cells,), elemTypes=(elem_type,))
    p.generateMesh()

# ===================== 筛选粉道单元并分组 =====================
safe_print("Step 8: 筛选三道粉道单元...")

num_y_layers = 3
num_z_layers_per_track = 40

all_powder_sets = []
global_set_counter = 1

# ===================== 预计算各道的Y/Z分层数据 =====================
# 按道生成 (elem_y_per_track, elem_z_per_track)
elem_y_per_track = {}
elem_z_per_track = {}
for t in range(num_tracks):
    pname = f'Powder-{t+1}'
    part = powder_parts[t]
    elems = list(part.elements)
    
    # 按Y分层
    elem_y = []
    for e in elems:
        nodes_list = list(e.getNodes())
        y_sum = 0.0
        for n in nodes_list:
            y_sum += n.coordinates[1]
        y_avg = y_sum / len(nodes_list)
        elem_y.append((e.label, y_avg))
    elem_y.sort(key=lambda x: x[1])
    total = len(elem_y)
    y_size = total // num_y_layers
    y_rem = total % num_y_layers
    
    # 每道每Y层的Z分层
    y_layers_data = []
    idx = 0
    for yi in range(num_y_layers):
        y_sz = y_size + (1 if yi < y_rem else 0)
        y_labels = [item[0] for item in elem_y[idx:idx+y_sz]]
        idx += y_sz
        
        elem_z = []
        for lab in y_labels:
            nodes_list = list(powder_parts[t].elements[lab-1].getNodes())
            z_sum = 0.0
            for n in nodes_list:
                z_sum += n.coordinates[2]
            z_avg = z_sum / len(nodes_list)
            elem_z.append((lab, z_avg))
        elem_z.sort(key=lambda x: x[1])
        
        z_size = len(elem_z) // num_z_layers_per_track
        z_rem = len(elem_z) % num_z_layers_per_track
        z_idx = 0
        z_layers = []
        for zi in range(num_z_layers_per_track):
            z_sz = z_size + (1 if zi < z_rem else 0)
            z_labels = tuple(item[0] for item in elem_z[z_idx:z_idx+z_sz])
            z_layers.append(z_labels)
            z_idx += z_sz
        y_layers_data.append(z_layers)
    
    elem_y_per_track[t] = y_layers_data

# ===================== 按激活顺序生成 Set-Layer =====================
# 激活顺序：先按层(L1→L2→L3)，再按道(T1→T2→T3)，再按Z(Z1→Z40)
# 这确保 Set-Layer-NNN 的顺序与激活步一一对应
for yi in range(num_y_layers):           # 外部：按层
    for t in range(num_tracks):           # 中部：按道
        pname = f'Powder-{t+1}'
        z_layers = elem_y_per_track[t][yi]  # 该道该层的Z分层
        for zi in range(num_z_layers_per_track):
            set_name = f'Set-Layer-{global_set_counter:03d}'
            all_powder_sets.append((set_name, (pname, z_layers[zi])))
            global_set_counter += 1

safe_print(f"共生成 {len(all_powder_sets)} 个激活集合")

# 创建 Part-level 的集合
for t in range(num_tracks):
    pname = f'Powder-{t+1}'
    part = powder_parts[t]
    labels = tuple(e.label for e in part.elements)
    part.SetFromElementLabels(name='Set-Kill', elementLabels=labels)
    part.SetFromElementLabels(name='All-Powder', elementLabels=labels)

for set_name, (pname, labels) in all_powder_sets:
    part = powder_parts[int(pname[-1])-1]
    part.SetFromElementLabels(name=set_name, elementLabels=labels)

# ===================== 创建分析步 =====================
safe_print("Step 9: 创建分析步...")

# 扫描模式：每道40步，T1前向，T2反向，T3前向
step_list = [('Step-1', False, None, None)]
step_counter = 2

for layer in range(1, num_y_layers+1):
    track_order = [1, 2, 3]
    for track in track_order:
        direction = 1 if (track % 2 == 1) else -1
        for _ in range(num_z_layers_per_track):
            step_list.append((f'Step-{step_counter}', False, track, direction))
            step_counter += 1
    if layer < num_y_layers:
        step_list.append((f'Step-{step_counter}', True, None, None))
        step_counter += 1

safe_print(f"共 {len(step_list)} 步 (含 Step-1)")
# Step-1 杀死 + 120*3 加热 + 2 冷却 = 363

# 创建 HeatTransferStep
prev = 'Initial'
for step_name, is_cooling, _, _ in step_list:
    if step_name == 'Step-1':
        tp = 1e-8
        init_inc = max_inc = tp
        min_inc = tp * 1e-3
    elif is_cooling:
        tp = 10.0
        init_inc = 0.1
        min_inc = 1.2e-5
        max_inc = 2.0
    else:
        tp = DT_PER_STEP
        init_inc = tp / 10.0
        max_inc = tp
        min_inc = tp / 10000.0
    
    if is_cooling:
        myModel.HeatTransferStep(name=step_name, previous=prev, timePeriod=tp,
            maxNumInc=5000000, initialInc=init_inc, minInc=min_inc, maxInc=max_inc, deltmx=200.0)
    else:
        myModel.HeatTransferStep(name=step_name, previous=prev, timePeriod=tp,
            maxNumInc=1000000, initialInc=init_inc, minInc=min_inc, maxInc=max_inc, deltmx=50.0)
    prev = step_name

# ===================== 插入关键词 =====================
safe_print("Step 10: 插入关键词...")
kb = myModel.keywordBlock
kb.synchVersions(storeNodesAndElements=False)
blocks = kb.sieBlocks

step_indices = {}
for idx, line in enumerate(blocks):
    s = line.strip().upper()
    if s.startswith('*STEP'):
        parts = line.split(',')
        if len(parts) > 1:
            np = parts[1].strip()
            if np.startswith('name='):
                sn = np[5:]
            else:
                sn = np
            step_indices[sn] = idx

# ---- Contact Pair（在 Step-1 之前插入）----
idx1 = step_indices['Step-1']
contact_block = (
    "** CONTACT PAIR: Powder bottom <-> Substrate top\n"
    "*Contact Pair, interaction=IntProp-1\n"
    "Substrate-Top, Powder-1-Bottom\n"
    "*Contact Pair, interaction=IntProp-1\n"
    "Substrate-Top, Powder-2-Bottom\n"
    "*Contact Pair, interaction=IntProp-1\n"
    "Substrate-Top, Powder-3-Bottom\n"
    "*Surface Interaction, name=IntProp-1\n"
    "*Gap Conductance\n"
    "1e7, 0.0\n"
    "1e7, 1.0\n"
)
kb.insert(idx1 - 1, contact_block)

# ---- Model Change ----
kb.synchVersions(storeNodesAndElements=False)
blocks = kb.sieBlocks
step_indices = {}
for idx, line in enumerate(blocks):
    s = line.strip().upper()
    if s.startswith('*STEP'):
        parts = line.split(',')
        if len(parts) > 1:
            np = parts[1].strip()
            if np.startswith('name='):
                sn = np[5:]
            else:
                sn = np
            step_indices[sn] = idx

# Step-1: 杀死所有粉道
idx1 = step_indices['Step-1']
kill_cmd = "*Model Change, TYPE=ELEMENT, remove\n"
for t in range(num_tracks):
    kill_cmd += f"Powder-{t+1}-1.Set-Kill\n"
kb.insert(idx1 + 1, kill_cmd)

# 后续激活步
act_idx = 0
insertions = []
for step_name, is_cooling, track, direction in step_list:
    if step_name == 'Step-1' or is_cooling:
        continue
    if act_idx < len(all_powder_sets):
        set_name, (pname, _) = all_powder_sets[act_idx]
        idx = step_indices[step_name]
        inst_name = f"{pname}-1"
        insertions.append((idx + 1, f"*Model Change, TYPE=ELEMENT, add\n{inst_name}.{set_name}\n"))
        act_idx += 1

insertions.sort(key=lambda x: x[0], reverse=True)
for pos, cmd in insertions:
    kb.insert(pos, cmd)

safe_print(f"插入了 {len(insertions)} 条 Model Change 命令")

# ===================== 相互作用与载荷 =====================
safe_print("Step 11: 相互作用与载荷...")

# All-Elements (Element set for DFLUX)
elem_labels_all = []
for inst in a.instances.values():
    elem_labels_all.append((inst.name, tuple(e.label for e in inst.elements)))
a.SetFromElementLabels(name='All-Elements', elementLabels=elem_labels_all)

# All-Nodes (Node set for Initial Temperature)
node_labels_all = []
for inst in a.instances.values():
    node_labels_all.append((inst.name, tuple(n.label for n in inst.nodes)))
a.SetFromNodeLabels(name='All-Nodes', nodeLabels=node_labels_all)

# Body Heat Flux
myModel.BodyHeatFlux(name='Body-Heat-Flux', createStepName='Step-2',
    region=a.sets['All-Elements'], distributionType=USER_DEFINED, magnitude=1.0)

# Initial Temp (using Node set)
myModel.Temperature(name='Initial-Temp', createStepName='Initial',
    region=a.sets['All-Nodes'], distributionType=UNIFORM, magnitudes=(20.0,))

# 所有外表面 — Film + Radiation
all_faces = []
for inst in a.instances.values():
    mask = inst.faces.getSequenceFromMask(('[#ffffffff]',))
    all_faces.append(mask)
combined = all_faces[0]
for f in all_faces[1:]:
    combined += f
region_film = regionToolset.Region(side1Faces=combined)

myModel.FilmCondition(name='Film-All', createStepName='Step-2',
    surface=region_film, definition=EMBEDDED_COEFF, filmCoeff=20.0, sinkTemperature=20.0)
myModel.RadiationToAmbient(name='Radiation-All', createStepName='Step-2',
    surface=region_film, radiationType=AMBIENT, distributionType=UNIFORM, emissivity=0.85, ambientTemperature=0.0)

# 表面：基板顶面 ↔ 三粉道底面
top_face = inst_sub.faces.findAt(((sub_w/2.0, sub_d, sub_l/2.0),))
a.Surface(name='Substrate-Top', side1Faces=top_face)

for t in range(num_tracks):
    pname = f'Powder-{t+1}'
    inst_pow = a.instances[f'{pname}-1']
    cx = track_x_offsets[t] + track_w/2.0
    bot_face = inst_pow.faces.findAt(((cx, sub_d, track_l/2.0),))
    a.Surface(name=f'{pname}-Bottom', side1Faces=bot_face)

# ===================== 作业创建 =====================
safe_print("Step 12: 创建作业并写入 INP...")
job_name = f'ortho3t_{case_label}'
if job_name in mdb.jobs.keys():
    del mdb.jobs[job_name]

user_sub = rf'D:\temp\duoceng3\a_3tracks_hybrid_ortho.for'
myJob = mdb.Job(name=job_name, model='Model-1',
    numCpus=8, numDomains=8, numGPUs=1,
    userSubroutine=user_sub)
myJob.writeInput(consistencyChecking=OFF)
safe_print(f"INP 已写入: {os.path.join(workdir, job_name + '.inp')}")
safe_print("脚本完成！")
