#!/usr/bin/env python3
"""分析短 INP 结果：提取最后一个加热步的峰值温度和熔池信息"""
import os, sys
from odbAccess import openOdb
from abaqusConstants import *
import numpy as np

WORKDIR = r"/mnt/d/temp/duoceng3"
case_name = sys.argv[1] if len(sys.argv) > 1 else "P1000_V3"
odb_path = os.path.join(WORKDIR, f"short_{case_name}.odb")
for_path = os.path.join(WORKDIR, f"a_for_{case_name}.for")

print(f"=== Case: {case_name} ===")

# 提取 FOR 中的参数
with open(for_path, "r") as f:
    content = f.read()
import re

m = re.search(r"LASER_POWER\s*=\s*([\d.]+)D0", content)
power = float(m.group(1)) if m else 0
m = re.search(r"ABSORPTIVITY\s*=\s*([\d.]+)D0", content)
eta = float(m.group(1)) if m else 0
m = re.search(r"SCAN_SPEED\s*=\s*([\d.]+)D0", content)
speed = float(m.group(1)) if m else 0
m = re.search(r"DT_PER_STEP\s*=\s*([\d.]+)D0", content)
dt = float(m.group(1)) if m else 0
print(f"  P={power:.0f}W, η={eta}, Q={power*eta:.0f}W, v={speed*1000:.1f}mm/s, DT={dt:.4f}s")

# 打开 ODB
odb = openOdb(path=odb_path, readOnly=True)
instances = odb.rootAssembly.instances

# 找粉道实例
powder_name = None
for name in instances.keys():
    if "POWDER" in name.upper():
        powder_name = name
        break

if powder_name:
    print(f"  Powder instance: {powder_name}")
else:
    print(f"  No powder instance found, available: {list(instances.keys())}")
    powder_name = list(instances.keys())[0]

powder = instances[powder_name]

# 找最后一个帧（加热步的最后一步是 step-8, 帧 index -1）
last_frame = None
steps = odb.steps
for step_name in reversed(steps.keys()):
    step = steps[step_name]
    if len(step.frames) > 0:
        last_frame = step.frames[-1]
        break

if not last_frame:
    # fallback to step-8
    step = steps.get("Step-8", steps.values()[-1])
    last_frame = step.frames[-1] if step.frames else step.frames[0]

print(f"  Analyzing: {list(steps.keys())[-1]}, frame index {list(steps.values())[-1].frames.index(last_frame)}")

# 读取温度
temp_field = last_frame.fieldOutputs["NT11"]
temp_values = temp_field.bulkDataBlocks[0].data if temp_field.bulkDataBlocks else None

if temp_values is None:
    temp_values = np.array([v.data for v in temp_field.values])

temps = temp_values if isinstance(temp_values, np.ndarray) else np.array([v.magnitude for v in temp_field.values])
tmax = float(np.max(temps))
tmin = float(np.min(temps))

# 提取节点坐标和温度
coords_data = []
for v in temp_field.values:
    coords_data.append((v.instance.nodeLabel, list(v.nodeLabel), v.data))
# 简化方法
nodes = temp_field.values
node_temps = []
for n in nodes:
    node_label = n.nodeLabel
    try:
        coord = n.instance.getNodeFromLabel(node_label).coordinates
        node_temps.append((coord[0], coord[1], coord[2], n.data))
    except:
        pass

if node_temps:
    node_temps = np.array(node_temps)
    # 粉道范围
    pow_x0, pow_w = 0.0081, 0.0018
    pow_y0 = 0.0048  # 基板顶面
    sub_d = 0.0048
    
    # 粉道节点温度
    in_powder = (node_temps[:, 0] >= pow_x0) & (node_temps[:, 0] <= pow_x0 + pow_w) & (node_temps[:, 1] >= pow_y0)
    powder_temps = node_temps[in_powder, 3]
    p_tmax = float(np.max(powder_temps)) if len(powder_temps) > 0 else 0
    
    # 基板节点温度
    in_sub = node_temps[:, 1] < pow_y0
    sub_temps = node_temps[in_sub, 3]
    s_tmax = float(np.max(sub_temps)) if len(sub_temps) > 0 else 0
    
    # 峰值位置
    peak_idx = np.argmax(node_temps[:, 3])
    peak_x, peak_y, peak_z, peak_t = node_temps[peak_idx]
    
    # 熔池统计 (T > 1400°C)
    melted = node_temps[node_temps[:, 3] > 1400.0]
    n_pool = len(melted)
    if n_pool > 0:
        x_vals = melted[:, 0]
        y_vals = melted[:, 1]
        z_vals = melted[:, 2]
        pool_width = float(np.max(x_vals) - np.min(x_vals)) * 1000  # mm
        pool_depth = float(np.max(y_vals) - np.min(y_vals)) * 1000  # mm
        pool_length = float(np.max(z_vals) - np.min(z_vals)) * 1000  # mm
        
        # 界面熔宽（Y=sub_d 附近的熔化节点）
        interface = melted[np.abs(melted[:, 1] - pow_y0) < 0.0003]
        interface_width = float(np.max(interface[:, 0]) - np.min(interface[:, 0])) * 1000 if len(interface) > 0 else 0
    else:
        pool_width = pool_depth = pool_length = interface_width = 0
    
    print(f"\n  === 温度结果 ===")
    print(f"  全局峰值温度: {tmax:.1f}°C (位置: ({peak_x*1000:.3f}, {peak_y*1000:.3f}, {peak_z*1000:.3f}) mm)")
    print(f"  粉道最高温度: {p_tmax:.1f}°C")
    print(f"  基板最高温度: {s_tmax:.1f}°C")
    print(f"  全局最低温度: {tmin:.1f}°C")
    
    if n_pool > 0:
        print(f"\n  熔池信息 (T > 1400°C):")
        print(f"  熔池节点数: {n_pool}")
        print(f"  熔宽: {pool_width:.3f} mm (粉道 {pool_width/1.8*100:.0f}%)")
        print(f"  界面熔宽: {interface_width:.3f} mm")
        print(f"  熔深: {pool_depth:.3f} mm")
        print(f"  熔长: {pool_length:.3f} mm")
        # 熔池温度范围
        pool_tmin = float(np.min(melted[:, 3]))
        pool_tmax = float(np.max(melted[:, 3]))
        print(f"  熔池温度范围: {pool_tmin:.0f}~{pool_tmax:.0f}°C")
    else:
        print(f"  ❌ 无熔池 (所有节点 < 1400°C)")
    
    # 如果基板过热
    if s_tmax > 1450:
        print(f"  ⚠️ 基板过热! 最高 {s_tmax:.1f}°C > 1450°C 液相线")
    else:
        print(f"  ✅ 基板安全 ({s_tmax:.1f}°C)")
    
    print(f"\n  增量步数: 见 .sta 文件")

odb.close()
