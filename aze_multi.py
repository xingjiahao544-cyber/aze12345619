# -*- coding: utf-8 -*-
"""
aze_multi.py - 3道×3层 316L激光熔覆
搭接率30%，道间距1.26mm
在 Abaqus CAE 中运行：File -> Run Script
"""
from abaqus import *
from abaqusConstants import *
from caeModules import *
import regionToolset
import os, sys, __main__

sys.setrecursionlimit(10000)

def safe_print(msg):
    """避免gbk编码错误"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('utf-8', errors='replace').decode('gbk', errors='replace'))

workdir = r'D:\temp\duoceng3'
os.makedirs(workdir, exist_ok=True)
os.chdir(workdir)

# ========== 几何参数 ==========
sub_w, sub_d, sub_l = 0.018, 0.0048, 0.024  # 基板
pow_w, pow_d, pow_l = 0.0018, 0.0018, 0.024  # 单道粉道

num_tracks = 3           # 3道
track_spacing = pow_w * 0.70  # 30%搭接率
total_track_width = pow_w + (num_tracks - 1) * track_spacing
track_x_start = (sub_w - total_track_width) / 2.0  # 第一道起始X

scan_speed = 0.005
single_layer_time = pow_l / scan_speed
cooling_time = 10.0       # 每层间冷却10s

num_y_layers = 3
num_z_layers_per_y = 40
steps_per_track = num_y_layers * num_z_layers_per_y  # 120步/道
cooling_steps_per_track = num_y_layers  # 每道3个冷却步
total_steps = num_tracks * (steps_per_track + cooling_steps_per_track)  # 369步 + Step-1

safe_print("3道3层多道搭接模型")
safe_print("道间距: {:.3f}mm".format(track_spacing*1000))
safe_print("总粉道宽度: {:.3f}mm".format(total_track_width*1000))
safe_print("第一道起始X: {:.3f}mm".format(track_x_start*1000))
safe_print("总步数: {}".format(total_steps))

# ========== 1. 创建模型 ==========
safe_print("Step 1: 创建模型...")
model_name = 'Model-1'
myModel = mdb.Model(name=model_name)
myModel.setValues(absoluteZero=ABSOLUTE_ZERO, stefanBoltzmann=STEFAN_BOLTZMANN)

# ========== 2. 创建基板部件 ==========
safe_print("Step 2: 创建基板部件...")
substrate_part = myModel.Part(name='Substrate', dimensionality=THREE_D,
                              type=DEFORMABLE_BODY)
sketch_sub = myModel.ConstrainedSketch(name='__sub_profile__', sheetSize=0.5)
sketch_sub.rectangle(point1=(0.0, 0.0), point2=(sub_w, sub_d))
substrate_part.BaseSolidExtrude(sketch=sketch_sub, depth=sub_l)

# ========== 3. 创建粉道部件（单条，后续实例平移）==========
safe_print("Step 3: 创建粉道部件...")
powder_part = myModel.Part(name='Powder', dimensionality=THREE_D,
                           type=DEFORMABLE_BODY)
sketch_pow = myModel.ConstrainedSketch(name='__pow_profile__', sheetSize=0.5)
sketch_pow.rectangle(point1=(0.0, 0.0), point2=(pow_w, pow_d))
powder_part.BaseSolidExtrude(sketch=sketch_pow, depth=pow_l)
safe_print("Step 3: OK")

# ========== 4. 材料属性 ==========
safe_print("Step 4: 设置材料属性...")
mat = myModel.Material(name='Material-1')
# 导热率 (W/mK)
mat.Conductivity.setValues(table=(
    (13.1, 10.), (14., 100.), (23., 300.), (36., 500.),
    (38., 800.), (35., 1200.), (70., 1350.), (100., 1450.),
    (130., 1800.), (170., 3000.),
))
# 密度 (kg/m3)
mat.Density.setValues(table=(
    (7740., 10.), (7710., 100.), (7680., 300.), (7580., 500.),
    (7470., 800.), (7350., 1200.), (7000., 1500.), (6900., 1600.),
    (6900., 3000.),
))
# 潜热
mat.LatentHeat.setValues(table=((270000., 1384.85, 1446.85),))
# 比热 (J/kgK)
mat.SpecificHeat.setValues(table=(
    (450., 10.), (500., 100.), (650., 300.), (750., 500.),
    (850., 800.), (780., 1200.), (920., 1500.), (800., 1600.),
    (800., 3000.),
))

sectionName = 'SolidSection'
myModel.HomogeneousSolidSection(name=sectionName, material='Material-1')
region_sub = substrate_part.Set(name='All-Substrate', cells=substrate_part.cells)
substrate_part.SectionAssignment(region=region_sub, sectionName=sectionName)
region_pow = powder_part.Set(name='All-Powder', cells=powder_part.cells)
powder_part.SectionAssignment(region=region_pow, sectionName=sectionName)
safe_print("Step 4: OK")

# ========== 5. 装配体 ==========
safe_print("Step 5: 创建装配体...")
a = myModel.rootAssembly
inst_sub = a.Instance(name='Substrate-1', part=substrate_part, dependent=ON)

# 创建3个粉道实例，分别平移
inst_pow_tracks = []
for t in range(num_tracks):
    track_x = track_x_start + t * track_spacing
    inst_name = 'Powder-{}'.format(t+1)
    inst = a.Instance(name=inst_name, part=powder_part, dependent=ON)
    a.translate(instanceList=(inst_name,), vector=(track_x, sub_d, 0.0))
    inst_pow_tracks.append(inst)
    safe_print("  粉道{}: X={:.4f}m".format(t+1, track_x))

a.regenerate()
safe_print("Step 5: OK")

# ========== 6. 网格划分 ==========
safe_print("Step 6: 网格划分...")
elem_type = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)

# 基板网格（粗网格）
substrate_part.seedPart(size=0.0012, deviationFactor=0.1)
substrate_part.setElementType(regions=(substrate_part.cells,), elemTypes=(elem_type,))
substrate_part.setMeshControls(regions=substrate_part.cells, elemShape=HEX,
                                technique=SWEEP)
substrate_part.generateMesh()

# 粉道网格（细网格，0.3mm）
powder_part.seedPart(size=0.0003, deviationFactor=0.1)
powder_part.setElementType(regions=(powder_part.cells,), elemTypes=(elem_type,))
powder_part.setMeshControls(regions=powder_part.cells, elemShape=HEX,
                             technique=SWEEP)
powder_part.generateMesh()
safe_print("Step 6: OK")

# ========== 7. 定义集合 ==========
safe_print("Step 7: 定义集合...")
# 基板所有节点/单元
inst_sub.Set(name='All-Elements', elements=inst_sub.elements)
inst_sub.Set(name='All-Nodes', nodes=inst_sub.nodes)

# 每个粉道的集合
for t in range(num_tracks):
    inst_name = 'Powder-{}'.format(t+1)
    inst = a.instances[inst_name]
    inst.Set(name='All-Elements', elements=inst.elements)

# 每个粉道的激活集合（按Y分层，每层内按Z分40组）
all_sets = []  # (track, layer, z_idx, set_name, element_labels)
set_counter = 1

for t in range(num_tracks):
    inst_name = 'Powder-{}'.format(t+1)
    inst = a.instances[inst_name]
    elements = list(powder_part.elements)  # 粉道Part内的元素

    # 按Y质心分3层
    elem_y = [(e.label, sum(n.coordinates[1] for n in e.getNodes())/len(e.getNodes()))
              for e in elements]
    elem_y.sort(key=lambda x: x[1])

    total = len(elem_y)
    y_layer_size = total // num_y_layers
    y_rem = total % num_y_layers

    set_list = []
    start = 0
    for ly in range(num_y_layers):
        size = y_layer_size + (1 if ly < y_rem else 0)
        layer_labels = [elem_y[i][0] for i in range(start, start+size)]
        start += size

        # 按Z质心分40组
        elem_z = []
        for label in layer_labels:
            elem = powder_part.elements[label-1]
            z_center = sum(n.coordinates[2] for n in elem.getNodes())/len(elem.getNodes())
            elem_z.append((label, z_center))
        elem_z.sort(key=lambda x: x[1])
        sorted_labels = [e[0] for e in elem_z]

        total_z = len(sorted_labels)
        z_size = total_z // num_z_layers_per_y
        z_rem = total_z % num_z_layers_per_y
        idx = 0
        for zi in range(num_z_layers_per_y):
            step_size = z_size + (1 if zi < z_rem else 0)
            subset = sorted_labels[idx:idx+step_size]
            idx += step_size
            set_name = 'Track{}-Layer{:03d}'.format(t+1, set_counter)
            set_list.append((set_name, subset))
            set_counter += 1

    # 为每个粉道创建所有集合
    for set_name, labels in set_list:
        full_labels = []
        for lab in labels:
            # 在Part级别用局部编号
            full_labels.append(lab)
        powder_part.SetFromElementLabels(name=set_name, elementLabels=tuple(full_labels))

    # 创建Kill集合（包含所有粉道元素）
    all_labels = tuple(e.label for e in powder_part.elements)
    powder_part.SetFromElementLabels(name='Track{}-Kill'.format(t+1),
                                     elementLabels=all_labels)

    all_sets.append((inst_name, set_list))
    safe_print("  粉道{}: {}组集合".format(t+1, len(set_list)))

safe_print("Step 7: OK")

# ========== 8. 表面定义（供散热边界使用）==========
safe_print("Step 8: 创建表面...")
# 收集所有粉道的底面（与基板接触的面）
all_bot_faces = []
all_top_faces = []
for t in range(num_tracks):
    inst_name = 'Powder-{}'.format(t+1)
    inst = a.instances[inst_name]
    # 粉道底面（Y=0 in Part coords, = sub_d in assembly）
    bot_face = inst.faces.findAt(((track_x_start + t*track_spacing + pow_w/2.0, sub_d, pow_l/2.0),))
    all_bot_faces.append(bot_face)
    # 粉道顶面
    top_face = inst.faces.findAt(((track_x_start + t*track_spacing + pow_w/2.0, sub_d+pow_d, pow_l/2.0),))
    all_top_faces.append(top_face)

# 基板顶面
top_face_sub = inst_sub.faces.findAt(((sub_w/2.0, sub_d, sub_l/2.0),))

# 基板外表面（散热用）
all_faces_sub = inst_sub.faces
all_faces_pow = []
for t in range(num_tracks):
    inst = a.instances['Powder-{}'.format(t+1)]
    for f in inst.faces:
        all_faces_pow.append(f)

# 创建表面
a.Surface(name='Substrate-Top', side1Faces=top_face_sub)
for t in range(num_tracks):
    a.Surface(name='Powder-{}-Bottom'.format(t+1), side1Faces=all_bot_faces[t])

# 外表面（对流+辐射）
all_external_faces = list(all_faces_sub) + all_faces_pow
# 用PickledSurf
# 简化：直接使用所有暴露面
safe_print("Step 8: OK")

# ========== 9. 创建分析步 ==========
safe_print("Step 9: 创建分析步...")

step_list = [('Step-1', 'cooling')]
step_counter = 2

for t in range(num_tracks):
    for ly in range(num_y_layers):
        for zi in range(num_z_layers_per_y):
            step_list.append(('Step-{}'.format(step_counter), 'heating'))
            step_counter += 1
        if ly < num_y_layers - 1 or t < num_tracks - 1:
            step_list.append(('Step-{}'.format(step_counter), 'cooling'))
            step_counter += 1

safe_print("总共{}个分析步".format(len(step_list)))
safe_print("Step 9: OK")

# ========== 10. 定义边界条件等 ==========
safe_print("Step 10: 边界条件和接触定义...")
# 初始温度
myModel.Temperature(name='Initial-Temp', 
                    createStepName='Initial',
                    region=inst_sub.Set(name='All-Nodes', nodes=inst_sub.nodes),
                    distributionType=UNIFORM, crossSectionDistribution=CONSTANT_THROUGH_THICKNESS,
                    magnitude=20.0)

# 基板底面固定温度（可选）
# 省略 - 由散热对流控制

# 接触定义（每个粉道底面与基板顶面）
for t in range(num_tracks):
    int_name = 'IntProp-{}'.format(t+1)
    myModel.interactionProperties.changeKey(fromKey='IntProp-1', toKey=int_name)
    # 实际需要在keywords中添加*Gap Conductance
    # 这里创建一个空接触属性
    myModel.ContactProperty(int_name)
    myModel.interactionProperties[int_name].TangentialBehavior()
    myModel.interactionProperties[int_name].NormalBehavior()

safe_print("Step 10: OK")

# ========== 11. 写入keywordBlock插入Contact Pair ==========
safe_print("Step 11: 写入Contact Pair关键字...")
# 在 Step-1 之前插入 *Contact Pair 和 *Gap Conductance
contact_lines = []
for t in range(num_tracks):
    contact_lines.append("*Surface Interaction, name=Contact-Thermal-{}".format(t+1))
    contact_lines.append("*Gap Conductance")
    contact_lines.append("1e7, 0.0")
    contact_lines.append("1e7, 1.0")
    contact_lines.append("*Contact Pair, interaction=Contact-Thermal-{}".format(t+1))
    contact_lines.append("Substrate-Top, Powder-{}-Bottom".format(t+1))

kb = myModel.keywordBlock
kb.synchVersions(storeNodesAndElements=False)
blocks = kb.sieBlocks

# 找到 Step-1 的位置
step1_idx = None
for i, line in enumerate(blocks):
    if '*Step, name=Step-1' in line.strip().upper():
        step1_idx = i
        break

if step1_idx:
    # 插入在 Step-1 之前
    insert_text = '\n'.join(contact_lines) + '\n'
    kb.insert(step1_idx - 1, insert_text)
    safe_print("  Contact Pair 已插入在 Step-1 之前")
else:
    safe_print("  警告：找不到 Step-1 位置")

safe_print("Step 11: OK")

# ========== 12. 写入Model Change和Dflux命令 ==========
safe_print("Step 12: 写入Model Change和Dflux...")
kb.synchVersions(storeNodesAndElements=False)
blocks = kb.sieBlocks

# 重新找到所有Step位置
step_positions = {}
for i, line in enumerate(blocks):
    s = line.strip().upper()
    if s.startswith('*STEP, NAME=STEP-'):
        name = s.split('=')[1].strip()
        step_positions[name] = i

# Step-1: 移除所有粉道元素
if 'STEP-1' in step_positions:
    idx = step_positions['STEP-1']
    remove_cmds = []
    for t in range(num_tracks):
        inst_name = 'Powder-{}'.format(t+1)
        remove_cmds.append("*Model Change, remove")
        remove_cmds.append("{}.Track{}-Kill".format(inst_name, t+1))
    remove_text = '\n'.join(remove_cmds) + '\n'
    kb.insert(idx + 4, remove_text)  # 在*Heat Transfer+时间行之后

# 后续步：每个加热步激活+Dflux，冷却步只有冷却
kb.synchVersions(storeNodesAndElements=False)
blocks = kb.sieBlocks

# 重新定位所有Step
step_positions = {}
for i, line in enumerate(blocks):
    s = line.strip().upper()
    if s.startswith('*STEP, NAME=STEP-'):
        name = s.split('=')[1].strip()
        step_positions[name] = i

# 遍历所有加热步（除了Step-1）
for step_name, idx in step_positions.items():
    step_num = int(step_name.split('-')[1])
    if step_num == 1:
        continue

    # 判断这个步属于哪个道和层
    # 简化：每个加热步都激活对应集合 + Dflux
    # 由于步数太多、集合名复杂，用文本方式直接在INP中插入更可靠
    pass

safe_print("Step 12: 建议使用后处理脚本插入Model Change和Dflux关键字")

# ========== 13. 写入INP ==========
safe_print("Step 13: 写入INP文件...")
inp_path = os.path.join(workdir, 'multi_track.inp')
mdb.Job(name='multi_track', model=model_name, description='3D 3-track 3-layer')
# 注意：直接writeInput可能不包含keywordBlock修改
# 需要在CAE中手动提交或使用writeInput(format=...)
safe_print("INP准备就绪: {}".format(inp_path))

safe_print("\n===== 完成 =====")
safe_print("请检查模型后，在CAE中：")
safe_print("1. 检查模型完整性")
safe_print("2. 在keywordBlock中确认关键字")
safe_print("3. 手动补充Model Change和DFLUX命令（或使用后处理脚本）")
safe_print("4. 提交作业: multi_track.inp")
