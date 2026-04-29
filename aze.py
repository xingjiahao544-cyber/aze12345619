# -*- coding: utf-8 -*-
from abaqus import *
from abaqusConstants import *
from caeModules import *
import regionToolset
import os
import sys
import __main__

sys.setrecursionlimit(10000)

def safe_print(msg):
    print(msg)
    sys.stdout.flush()

workdir = r'D:\temp\duoceng3'
os.makedirs(workdir, exist_ok=True)
os.chdir(workdir)

# 0. 几何参数
sub_w, sub_d, sub_l = 0.018, 0.0048, 0.024
pow_w, pow_d, pow_l = 0.0018, 0.0018, 0.024
pow_x0 = (sub_w - pow_w) / 2.0

ABSOLUTE_ZERO = -273.15
STEFAN_BOLTZMANN = 5.670367e-8

scan_speed = 0.005
single_layer_time = pow_l / scan_speed
total_scan_time = 3 * single_layer_time
cooling_time = 120.0
layers_with_cooling = [True, True, False]  # 第三层后无冷却

num_y_layers = 3
num_z_layers_per_y = 40
total_activation_steps = num_y_layers * num_z_layers_per_y
dt_per_step = total_scan_time / total_activation_steps

safe_print("总扫描时间：{} s，总激活步数：{}，每激活步时间：{} s".format(
    total_scan_time, total_activation_steps, dt_per_step))

# 1. 创建模型
safe_print("Step 1: 创建模型...")
model_name = 'Model-1'
myModel = mdb.Model(name=model_name)
myModel.setValues(absoluteZero=ABSOLUTE_ZERO, stefanBoltzmann=STEFAN_BOLTZMANN)
safe_print("Step 1: OK")

# 2. 创建基板部件
safe_print("Step 2: 创建基板部件...")
substrate_part = myModel.Part(name='Substrate', dimensionality=THREE_D,
                              type=DEFORMABLE_BODY)
sketch_sub = myModel.ConstrainedSketch(name='__sub_profile__', sheetSize=0.5)
sketch_sub.rectangle(point1=(0.0, 0.0), point2=(sub_w, sub_d))
substrate_part.BaseSolidExtrude(sketch=sketch_sub, depth=sub_l)
safe_print("Step 2: OK")

# 3. 创建粉道部件
safe_print("Step 3: 创建粉道部件...")
powder_part = myModel.Part(name='Powder', dimensionality=THREE_D,
                           type=DEFORMABLE_BODY)
sketch_pow = myModel.ConstrainedSketch(name='__pow_profile__', sheetSize=0.5)
sketch_pow.rectangle(point1=(0.0, 0.0), point2=(pow_w, pow_d))
powder_part.BaseSolidExtrude(sketch=sketch_pow, depth=pow_l)
safe_print("Step 3: OK")

# 4. 创建材料
safe_print("Step 4: 创建材料...")
materialName = 'Material-1'
if materialName in myModel.materials.keys():
    del myModel.materials[materialName]
myMaterial = myModel.Material(name=materialName)
conductivityTable = (
    (13.1, 10.0), (14.0, 100.0), (23.0, 300.0), (36.0, 500.0),
    (38.0, 800.0), (35.0, 1200.0), (70.0, 1350.0), (100.0, 1450.0),
    (130.0, 1800.0), (170.0, 3000.0),
)
myMaterial.Conductivity(temperatureDependency=ON, table=conductivityTable)
specificHeatTable = (
    (450.0, 10.0), (500.0, 100.0), (650.0, 300.0), (750.0, 500.0),
    (850.0, 800.0), (780.0, 1200.0), (920.0, 1500.0),
    (800.0, 1600.0), (800.0, 3000.0),
)
myMaterial.SpecificHeat(temperatureDependency=ON, table=specificHeatTable)
densityTable = (
    (7740.0, 10.0), (7710.0, 100.0), (7680.0, 300.0), (7580.0, 500.0),
    (7470.0, 800.0), (7350.0, 1200.0), (7000.0, 1500.0),
    (6900.0, 1600.0), (6900.0, 3000.0),
)
myMaterial.Density(temperatureDependency=ON, table=densityTable)
myMaterial.LatentHeat(table=((270000.0, 1384.85, 1446.85),))
safe_print("Step 4: OK")

# 5. 创建截面
safe_print("Step 5: 创建截面...")
sectionName = 'SolidSection'
if sectionName not in myModel.sections.keys():
    myModel.HomogeneousSolidSection(name=sectionName, material=materialName)
region_sub = substrate_part.Set(name='All-Substrate', cells=substrate_part.cells)
substrate_part.SectionAssignment(region=region_sub, sectionName=sectionName)
region_pow = powder_part.Set(name='All-Powder', cells=powder_part.cells)
powder_part.SectionAssignment(region=region_pow, sectionName=sectionName)
safe_print("Step 5: OK")

# 6. 装配体（从属实例）
safe_print("Step 6: 装配体（从属实例模式）...")
a = myModel.rootAssembly
inst_sub = a.Instance(name='Substrate-1', part=substrate_part, dependent=ON)
inst_pow = a.Instance(name='Powder-1', part=powder_part, dependent=ON)
a.translate(instanceList=('Powder-1',), vector=(pow_x0, sub_d, 0.0))
safe_print("Step 6: OK")

# 7. 网格划分
safe_print("Step 7: 网格划分...")
elem_type = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
substrate_part.seedPart(size=0.0012, deviationFactor=0.1)
substrate_part.setMeshControls(regions=substrate_part.cells, elemShape=HEX, technique=SWEEP)
substrate_part.setElementType(regions=(substrate_part.cells,), elemTypes=(elem_type,))
substrate_part.generateMesh()
powder_part.seedPart(size=0.0003, deviationFactor=0.1)
powder_part.setMeshControls(regions=powder_part.cells, elemShape=HEX, technique=SWEEP)
powder_part.setElementType(regions=(powder_part.cells,), elemTypes=(elem_type,))
powder_part.generateMesh()
safe_print("Step 7: OK")

# 8. 筛选粉道单元并分组
safe_print("Step 8: 筛选粉道单元...")
powder_elements = list(powder_part.elements)
if len(powder_elements) == 0:
    raise Exception("粉道部件没有单元，请检查网格划分！")

elem_y_centers = []
for elem in powder_elements:
    nodes = elem.getNodes()
    y_sum = 0.0
    n_count = 0
    for node in nodes:
        y_sum += node.coordinates[1]
        n_count += 1
    y_center = y_sum / n_count
    elem_y_centers.append((elem.label, y_center))
elem_y_centers.sort(key=lambda x: x[1])

total = len(elem_y_centers)
y_layers_labels = []
start = 0
for i in range(num_y_layers):
    size = total // num_y_layers + (1 if i < total % num_y_layers else 0)
    layer_labels = [item[0] for item in elem_y_centers[start:start+size]]
    y_layers_labels.append(layer_labels)
    start += size

all_layer_sets = []
counter = 1
for layer_labels in y_layers_labels:
    elem_z_list = []
    for label in layer_labels:
        elem = powder_part.elements[label-1]
        nodes = elem.getNodes()
        z_sum = 0.0
        n_count = 0
        for node in nodes:
            z_sum += node.coordinates[2]
            n_count += 1
        z_center = z_sum / n_count
        elem_z_list.append((label, z_center))
    elem_z_list.sort(key=lambda x: x[1])
    sorted_labels = [item[0] for item in elem_z_list]

    total_z = len(sorted_labels)
    size_z = total_z // num_z_layers_per_y
    rem_z = total_z % num_z_layers_per_y
    idx = 0
    for i in range(num_z_layers_per_y):
        step_size = size_z + (1 if i < rem_z else 0)
        subset_labels = sorted_labels[idx:idx+step_size]
        all_layer_sets.append(('Set-Layer-{:03d}'.format(counter), subset_labels))
        counter += 1
        idx += step_size

safe_print("共生成 {} 个激活集合".format(len(all_layer_sets)))

powder_labels = [e.label for e in powder_part.elements]
powder_part.SetFromElementLabels(name='Set-Kill', elementLabels=powder_labels)
for set_name, labels in all_layer_sets:
    powder_part.SetFromElementLabels(name=set_name, elementLabels=tuple(labels))
safe_print("Step 8: OK")

# 10. 创建分析步序列
safe_print("Step 9: 创建分析步...")
step_list = [('Step-1', False, None)]  # 初始杀死步
step_counter = 2
for layer in range(1, num_y_layers+1):
    for _ in range(num_z_layers_per_y):
        step_list.append(('Step-{}'.format(step_counter), False, layer))
        step_counter += 1
    if layer < num_y_layers and layers_with_cooling[layer-1]:
        step_list.append(('Step-{}'.format(step_counter), True, layer))
        step_counter += 1

total_steps = len(step_list) - 1
prev = 'Initial'
for step_name, is_cooling, _ in step_list:
    if step_name == 'Step-1':
        tp = 1e-8
    elif is_cooling:
        tp = cooling_time
    else:
        tp = dt_per_step

    if step_name == 'Step-1':
        init_inc = max_inc = tp
        min_inc = tp * 1e-3
    elif is_cooling:
        # 冷却步：极小初始增量 + 极小最小增量，让求解器能逐步通过最陡梯度段
        init_inc = tp / 100000.0    # 120/100000 = 0.0012s
        min_inc  = tp / 10000000.0  # 120/1e7 = 1.2e-5s
        max_inc  = tp / 10.0        # 120/10 = 12s（收敛后可增大）
    else:
        init_inc = tp / 10.0
        max_inc  = tp
        min_inc  = tp / 10000.0

    if is_cooling:
        myModel.HeatTransferStep(name=step_name, previous=prev, timePeriod=tp,
                                 maxNumInc=5000000, initialInc=init_inc,
                                 minInc=min_inc, maxInc=max_inc, deltmx=200.0)
    else:
        myModel.HeatTransferStep(name=step_name, previous=prev, timePeriod=tp,
                                 maxNumInc=1000000, initialInc=init_inc,
                                 minInc=min_inc, maxInc=max_inc, deltmx=50.0)
    prev = step_name
safe_print("Step 9: OK")

# 11. 插入生死单元关键词（关键修正：添加实例名前缀）
safe_print("Step 10: 插入关键词...")
kb = myModel.keywordBlock
kb.synchVersions(storeNodesAndElements=False)
blocks = kb.sieBlocks
step_indices = {}
for idx, line in enumerate(blocks):
    if line.strip().upper().startswith('*STEP'):
        parts = line.split(',')
        if len(parts) > 1:
            name_part = parts[1].strip()
            if name_part.startswith('name='):
                step_name = name_part[5:]
            else:
                step_name = name_part
            step_indices[step_name] = idx

act_idx = 1
act_map = {}
for step_name, is_cooling, _ in step_list:
    if step_name == 'Step-1':
        continue
    if not is_cooling:
        act_map[step_name] = 'Set-Layer-{:03d}'.format(act_idx)
        act_idx += 1
    else:
        act_map[step_name] = None

insertions = []
idx1 = step_indices['Step-1']
# 重要：对于 dependent 实例，必须加上实例名 "Powder-1." 前缀
insertions.append((idx1+1, '*Model Change, remove\nPowder-1.Set-Kill\n'))
for step_name, set_name in act_map.items():
    idx = step_indices[step_name]
    if set_name:
        insertions.append((idx+1, '*Model Change, add\nPowder-1.{}\n'.format(set_name)))
# ---- 先插入 Contact Pair + Gap Conductance（在 Step-1 之前）----
# 必须插入在第一个 *Step 之前（kb.insert 插入在 pos 之后，所以用 idx1-1）
contact_block = (
    "** CONTACT PAIR: Powder bottom <-> Substrate top\n"
    "*Contact Pair, interaction=IntProp-1, small sliding\n"
    "Powder-Bottom, Substrate-Top\n"
    "*Surface Interaction, name=IntProp-1\n"
    "*Gap Conductance\n"
    "1e7, 0.0\n"
    "1e7, 1.0\n"
)
# 找到第一个 *Step 行之前的位置，插入 Contact Pair
# idx1-1 确保在 Step-1 注释头之前
kb.insert(idx1 - 1, contact_block)
# 重新同步 blocks，因为插入改变了索引
kb.synchVersions(storeNodesAndElements=False)
blocks = kb.sieBlocks
# 重建 step_indices（索引已变）
step_indices = {}
for idx, line in enumerate(blocks):
    if line.strip().upper().startswith('*STEP'):
        parts = line.split(',')
        if len(parts) > 1:
            name_part = parts[1].strip()
            if name_part.startswith('name='):
                step_name = name_part[5:]
            else:
                step_name = name_part
            step_indices[step_name] = idx

# ---- 再插入 Model Change（生死单元）----
act_idx = 1
act_map = {}
for step_name, is_cooling, _ in step_list:
    if step_name == 'Step-1':
        continue
    if not is_cooling:
        act_map[step_name] = 'Set-Layer-{:03d}'.format(act_idx)
        act_idx += 1
    else:
        act_map[step_name] = None

insertions = []
idx1 = step_indices['Step-1']
insertions.append((idx1+1, '*Model Change, remove\nPowder-1.Set-Kill\n'))
for step_name, set_name in act_map.items():
    idx = step_indices[step_name]
    if set_name:
        insertions.append((idx+1, '*Model Change, add\nPowder-1.{}\n'.format(set_name)))
insertions.sort(key=lambda x: x[0], reverse=True)
for pos, cmd in insertions:
    kb.insert(pos, cmd)

safe_print("Step 10: OK")

# 12. 相互作用与载荷
safe_print("Step 11: 准备相互作用与载荷...")
a = mdb.models['Model-1'].rootAssembly

# ---- 1. 创建所有体集合 ----
all_cells = inst_sub.cells + inst_pow.cells
if 'All-Cells' in a.sets.keys():
    del a.sets['All-Cells']
a.Set(name='All-Cells', cells=all_cells)

# ---- 2. 创建所有单元集合 ----
elem_labels_sub = tuple(e.label for e in inst_sub.elements)
elem_labels_pow = tuple(e.label for e in inst_pow.elements)
all_elem_labels = (('Substrate-1', elem_labels_sub), ('Powder-1', elem_labels_pow))
if 'All-Elements' in a.sets.keys():
    del a.sets['All-Elements']
a.SetFromElementLabels(name='All-Elements', elementLabels=all_elem_labels)

# ---- 3. 施加体热通量（配合 DFLUX 子程序）----
myModel.BodyHeatFlux(name='Body-Heat-Flux', createStepName='Step-2',
                     region=a.sets['All-Elements'],
                     distributionType=USER_DEFINED, magnitude=1.0)
safe_print("  体热通量创建成功")

# ---- 4. 初始温度 ----
myModel.Temperature(name='Initial-Temp', createStepName='Initial',
                    region=a.sets['All-Cells'],
                    distributionType=UNIFORM, magnitudes=(20.0,))
safe_print("  初始温度设置成功")

# ---- 5. 对流换热与辐射 ----
# 获取所有外表面
all_faces_sub = inst_sub.faces
all_faces_pow = inst_pow.faces
# 使用 getSequenceFromMask 快速选取所有外表面
# 对于简单长方体，mask 可以用 ('[#ffffffff]',) 但建议使用 findAt 或直接使用 faces
# 这里使用简便方法：直接传递所有面
region_film = regionToolset.Region(side1Faces=all_faces_sub.getSequenceFromMask(('[#ffffffff]',)) +
                                   all_faces_pow.getSequenceFromMask(('[#ffffffff]',)))
myModel.FilmCondition(name='Film-All', createStepName='Step-2',
                      surface=region_film, definition=EMBEDDED_COEFF,
                      filmCoeff=20.0, sinkTemperature=20.0)

myModel.RadiationToAmbient(name='Radiation-All', createStepName='Step-2',
                           surface=region_film, radiationType=AMBIENT,
                           distributionType=UNIFORM, emissivity=0.85,
                           ambientTemperature=0.0)
safe_print("  对流与辐射边界设置成功")

# ---- 6. 创建 基板-粉道 表面（供 Contact Pair 使用，关键字在 Step 10 已插入） ----
safe_print("  创建表面（基板顶面 ↔ 粉道底面）...")
# 基板顶面 — 几何中心在 (sub_w/2, sub_d, sub_l/2)
top_face_sub = inst_sub.faces.findAt(((sub_w/2.0, sub_d, sub_l/2.0),))
# 粉道底面 — 几何中心在 (pow_x0+pow_w/2, sub_d, pow_l/2)（已平移至装配体）
bot_face_pow = inst_pow.faces.findAt(((pow_x0 + pow_w/2.0, sub_d, pow_l/2.0),))
# 创建表面（CAE 自动写入 INP Assembly 段）
a.Surface(name='Substrate-Top', side1Faces=top_face_sub)
a.Surface(name='Powder-Bottom', side1Faces=bot_face_pow)
safe_print("  表面创建成功，Contact Pair 将在 Step 10 插入的关键字中定义")

safe_print("Step 11: OK")

# 13. 作业创建与 INP 写入
safe_print("Step 12: 创建作业并写入 INP 文件...")
job_name = 'LaserCladding-316L'
if job_name in mdb.jobs.keys():
    del mdb.jobs[job_name]

myJob = mdb.Job(name=job_name, model='Model-1',
                numCpus=8, numDomains=8, numGPUs=1,
                userSubroutine=r'D:\temp\duoceng3\a.for')

myJob.writeInput(consistencyChecking=OFF)
safe_print("INP 文件已写入：{}".format(os.path.join(workdir, job_name + '.inp')))
safe_print("脚本执行完毕，无错误。")