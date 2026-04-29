"""
build_multi_inp.py
生成 3道×3层 多道搭接 INP
30%搭接率，冷却步10s
"""

import os, math

DIR = r"/mnt/d/temp/duoceng3"
os.makedirs(DIR, exist_ok=True)

# ========== 几何参数 ==========
sub_w, sub_d, sub_l = 0.018, 0.0048, 0.024  # 基板 18×4.8×24mm
pow_w, pow_d, pow_l = 0.0018, 0.0018, 0.024  # 单道 1.8×1.8×24mm
mesh_size_sub = 0.0012    # 基板网格
mesh_size_pow = 0.0003    # 粉道网格
num_tracks = 3
track_spacing = pow_w * 0.70  # 1.26mm
track_x_start = (sub_w - (pow_w + (num_tracks-1)*track_spacing)) / 2.0

# 网格划分
# 基板: X=0~18mm(15×1.2mm), Y=-4.8~0mm(4×1.2mm), Z=0~24mm(20×1.2mm) → 1200 DC3D8
# 粉道: X=0~1.8mm(6×0.3mm), Y=0~1.8mm(6×0.3mm), Z=0~24mm(80×0.3mm) → 2880 DC3D8

nx_sub, ny_sub, nz_sub = int(sub_w/mesh_size_sub), int(sub_d/mesh_size_sub), int(sub_l/mesh_size_sub)
nx_pow, ny_pow, nz_pow = int(pow_w/mesh_size_pow), int(pow_d/mesh_size_pow), int(pow_l/mesh_size_pow)

print(f"基板网格: {nx_sub}×{ny_sub}×{nz_sub} = {nx_sub*ny_sub*nz_sub} 单元")
print(f"粉道网格: {nx_pow}×{ny_pow}×{nz_pow} = {nx_pow*ny_pow*nz_pow} 单元")

# ========== 节点和单元生成 ==========
lines = []
lines.append("*Heading")
lines.append("** 3D 3-Track × 3-Layer Laser Cladding")
lines.append(f"** Track spacing: {track_spacing*1000:.3f}mm, Overlap: 30%")
lines.append("*Preprint, echo=NO, model=NO, history=NO, contact=NO")
lines.append("**")

# --- 基板 Part ---
lines.append("*Part, name=Substrate")
offset = 1
node_total = offset
for k in range(nz_sub+1):
    for j in range(ny_sub+1):
        for i in range(nx_sub+1):
            x = i * mesh_size_sub
            y = j * mesh_size_sub
            z = k * mesh_size_sub
            lines.append(f"{node_total:>8d}, {x:.10f}, {y:.10f}, {z:.10f}")
            node_total += 1
n_nodes_sub = node_total - offset

elem_total = 1
for k in range(nz_sub):
    for j in range(ny_sub):
        for i in range(nx_sub):
            n0 = offset + k*(nx_sub+1)*(ny_sub+1) + j*(nx_sub+1) + i
            n1 = n0 + 1
            n2 = n0 + (nx_sub+1)
            n3 = n2 + 1
            n4 = n0 + (nx_sub+1)*(ny_sub+1)
            n5 = n4 + 1
            n6 = n4 + (nx_sub+1)
            n7 = n6 + 1
            lines.append(f"{elem_total:>8d}, {n0:>8d}, {n1:>8d}, {n3:>8d}, {n2:>8d}, {n4:>8d}, {n5:>8d}, {n7:>8d}, {n6:>8d}")
            elem_total += 1
n_elems_sub = elem_total - 1

lines.append("*Nset, nset=All-Substrate, generate")
lines.append(f"    1, {n_nodes_sub}, 1")
lines.append("*Elset, elset=All-Substrate, generate")
lines.append(f"    1, {n_elems_sub}, 1")
lines.append("*Solid Section, elset=All-Substrate, material=Material-1")
lines.append(",")
lines.append("*End Part")
lines.append("**")

# --- 粉道 Part ---
lines.append("*Part, name=Powder")
# Part 内部节点从 1 开始编号
powder_node_start = 1
offset = 1
nodes_per_layer_pow = (nx_pow+1)*(ny_pow+1)
for k in range(nz_pow+1):
    for j in range(ny_pow+1):
        for i in range(nx_pow+1):
            x = i * mesh_size_pow
            y = j * mesh_size_pow
            z = k * mesh_size_pow
            lines.append(f"{node_total:>8d}, {x:.10f}, {y:.10f}, {z:.10f}")
            node_total += 1
n_nodes_pow = node_total - offset

# Part 内部元素从 1 开始编号
powder_elem_start = 1
for k in range(nz_pow):
    for j in range(ny_pow):
        for i in range(nx_pow):
            n0 = offset + k*(nx_pow+1)*(ny_pow+1) + j*(nx_pow+1) + i
            n1 = n0 + 1
            n2 = n0 + (nx_pow+1)
            n3 = n2 + 1
            n4 = n0 + (nx_pow+1)*(ny_pow+1)
            n5 = n4 + 1
            n6 = n4 + (nx_pow+1)
            n7 = n6 + 1
            lines.append(f"{elem_total:>8d}, {n0:>8d}, {n1:>8d}, {n3:>8d}, {n2:>8d}, {n4:>8d}, {n5:>8d}, {n7:>8d}, {n6:>8d}")
            elem_total += 1
n_elems_pow = elem_total - powder_elem_start

lines.append("*Nset, nset=All-Elements, generate")
lines.append(f"    {powder_elem_start}, {powder_elem_start+n_elems_pow-1}, 1")
lines.append("*Elset, elset=All-Elements, generate")
lines.append(f"    {powder_elem_start}, {powder_elem_start+n_elems_pow-1}, 1")
lines.append("*Solid Section, elset=All-Elements, material=Material-1")
lines.append(",")
lines.append("*End Part")
lines.append("**")

# ========== 材料 ==========
lines.append("*Material, name=Material-1")
lines.append("*Conductivity")
lines.append(" 13.1,  10.\n  14., 100.\n  23., 300.\n  36., 500.\n  38., 800.\n  35.,1200.\n  70.,1350.\n 100.,1450.\n 130.,1800.\n 170.,3000.")
lines.append("*Density")
lines.append("7740.,  10.\n7710., 100.\n7680., 300.\n7580., 500.\n7470., 800.\n7350.,1200.\n7000.,1500.\n6900.,1600.\n6900.,3000.")
lines.append("*Latent Heat")
lines.append("270000., 1384.85, 1446.85")
lines.append("*Specific Heat")
lines.append("450.,  10.\n500., 100.\n650., 300.\n750., 500.\n850., 800.\n780.,1200.\n920.,1500.\n800.,1600.\n800.,3000.")
lines.append("**")
lines.append("*Physical Constants, absolute zero=-273.15, stefan boltzmann=5.67037e-08")
lines.append("**")

# ========== 装配体 ==========
lines.append("*Assembly, name=Assembly")
# 基板实例
lines.append("*Instance, name=Substrate-1, part=Substrate")
lines.append("*End Instance")
lines.append("**")

# 3个粉道实例
track_x_positions = [track_x_start + t * track_spacing for t in range(num_tracks)]
for t in range(num_tracks):
    inst_name = f"Powder-{t+1}"
    tx = track_x_positions[t]
    lines.append(f"*Instance, name={inst_name}, part=Powder")
    lines.append(f"      {tx:.10f},       {sub_d:.10f},            0.")
    lines.append("*End Instance")
lines.append("**")

# ========== 接触表面定义 ==========
# 基板顶面
for t in range(num_tracks):
    tx = track_x_positions[t]
    inst_name = f"Powder-{t+1}"
    tx_center = tx + pow_w/2.0
    
    # 每个粉道的底部表面（需要在Part内部定义）
    # 底层元素: j=0 in part mesh
    line_elems = []
    for k in range(nz_pow):
        base = powder_elem_start + k*nx_pow*ny_pow  # first element of layer k
        line_elems.extend([base + i for i in range(nx_pow)])
    
    # 在 Part 内部定义表面
    lines.append(f"*Elset, elset=_BotFaces, generate")
    lines.append(f"    1, {n_elems_pow}, {nx_pow}")
    lines.append("*Surface, type=ELEMENT, name=Bottom")
    lines.append("_BotFaces, S3")
    
lines.append("*End Part")
lines.append("**")
sub_top_elems = []
for k in range(nz_sub):
    for i in range(nx_sub):
        sub_top_elems.append(k*nx_sub*ny_sub + (ny_sub-1)*nx_sub + i + 1)

sub_eset_lines = []
for i in range(0, len(sub_top_elems), 16):
    chunk = sub_top_elems[i:i+16]
    sub_eset_lines.append("  " + ", ".join(str(e) for e in chunk) + ",")

lines.append("*Elset, elset=_Substrate-Top, internal, instance=Substrate-1")
for ln in sub_eset_lines:
    lines.append(ln)
if lines[-1].endswith(","):
    lines[-1] = lines[-1][:-1]

lines.append("*Surface, name=Substrate-Top")
lines.append("_Substrate-Top, S2")
lines.append("**")

# 外表面（散热用）
lines.append("*Elset, elset=_External-Surf, internal, instance=Substrate-1, generate")
lines.append(f"    1, {n_elems_sub}, 1")
lines.append("*Surface, type=ELEMENT, name=All-External, internal")
lines.append("_External-Surf, S1")
lines.append("_External-Surf, S2")
lines.append("_External-Surf, S3")
lines.append("_External-Surf, S4")
lines.append("_External-Surf, S5")
lines.append("_External-Surf, S6")

# ========== 粉道集合（按层和Z分段）===========
# 每道每层: 元素按Z分40组
total_elem_per_track = n_elems_pow  # 2880
elems_per_layer = total_elem_per_track // 3  # 960
elems_per_zgroup = elems_per_layer // 40  # 24

# 元素编号: 连续排列，Z变化最慢
# Z=0: nx_pow*ny_pow 个元素
# Z=1: 下一个 nx_pow*ny_pow

# 集合名: Track{track}-Layer{layer:03d}-Z{z:03d}
for t in range(num_tracks):
    inst_name = f"Powder-{t+1}"
    # Kill集：所有粉道元素
    lines.append(f"*Elset, elset=Track{t+1}-Kill, instance={inst_name}, generate")
    lines.append(f"    {powder_elem_start}, {powder_elem_start+n_elems_pow-1}, 1")
    
    set_counter = 1
    for ly in range(3):
        layer_start = powder_elem_start + ly * elems_per_layer
        for zi in range(40):
            z_start = layer_start + zi * elems_per_zgroup
            z_end = z_start + elems_per_zgroup - 1
            set_name = f"Track{t+1}-Set-{set_counter:03d}"
            lines.append(f"*Elset, elset={set_name}, instance={inst_name}, generate")
            lines.append(f"    {z_start}, {z_end}, 1")
            set_counter += 1

lines.append("*End Assembly")
lines.append("**")

# ========== Contact Pair + Gap Conductance ==========
for t in range(num_tracks):
    lines.append(f"*Surface Interaction, name=Contact-Thermal-{t+1}")
    lines.append("*Gap Conductance")
    lines.append("1e7, 0.0")
    lines.append("1e7, 1.0")
    lines.append(f"*Contact Pair, interaction=Contact-Thermal-{t+1}")
    lines.append(f"Substrate-Top, Powder-{t+1}-Bottom")
    lines.append("**")

# ========== Step-1: 初始杀死+预热 ==========
lines.append("** STEP: Step-1")
lines.append("*Step, name=Step-1, nlgeom=NO, inc=1000000")
lines.append("*Heat Transfer, end=PERIOD, deltmx=500.")
lines.append("10.0, 0.1, 1e-10, 1.0,")
for t in range(num_tracks):
    lines.append(f"*Model Change, remove")
    lines.append(f"Powder-{t+1}.Track{t+1}-Kill")
lines.append("*Sfilm")
lines.append("All-External, F, 20., 20.")
lines.append("*Sradiate")
lines.append("All-External, R, 0., 0.85")
lines.append("*End Step")

# ========== 加热步 + 冷却步 ==========
step_num = 2
for t in range(num_tracks):
    for ly in range(3):
        for zi in range(40):
            set_idx = ly * 40 + zi + 1
            set_name = f"Track{t+1}-Set-{set_idx:03d}"
            
            lines.append(f"** STEP: Step-{step_num}")
            lines.append(f"*Step, name=Step-{step_num}, nlgeom=NO, inc=1000000")
            lines.append(f"*Heat Transfer, end=PERIOD, deltmx=50.")
            lines.append("0.012, 0.12, 1.2e-05, 0.12,")
            lines.append(f"*Model Change, add")
            lines.append(f"Powder-{t+1}.{set_name}")
            lines.append("*Dflux")
            lines.append("Powder-{}.All-Elements, BFNU, 1.".format(t+1))
            lines.append("*Sfilm")
            lines.append("All-External, F, 20., 20.")
            lines.append("*Sradiate")
            lines.append("All-External, R, 0., 0.85")
            lines.append("*End Step")
            step_num += 1
        
        # 冷却步（除最后一个加热步）
        if ly < 2 or t < num_tracks - 1:
            lines.append(f"** STEP: Step-{step_num} (Cool)")
            lines.append(f"*Step, name=Step-{step_num}, nlgeom=NO, inc=5000000")
            lines.append(f"*Heat Transfer, end=PERIOD, deltmx=200.")
            lines.append("0.0012, 10., 1.2e-05, 1.,")
            lines.append("*Sfilm")
            lines.append("All-External, F, 20., 20.")
            lines.append("*Sradiate")
            lines.append("All-External, R, 0., 0.85")
            lines.append("*End Step")
            step_num += 1

# ========== 写入文件 ==========
inp_path = os.path.join(DIR, "multi_track.inp")
with open(inp_path, 'w') as f:
    f.write('\n'.join(lines))

print(f"\nINP written: {inp_path}")
print(f"Total steps: {step_num-1}")
print(f"Substrate: {n_elems_sub} elements")
print(f"Powder per track: {n_elems_pow} elements")
print(f"Total elements: {n_elems_sub + num_tracks*n_elems_pow}")
