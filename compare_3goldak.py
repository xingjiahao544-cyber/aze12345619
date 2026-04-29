"""
提取三种Goldak热源变体的温度场数据，对比分析
"""
from odbAccess import openOdb
import sys

CASES = ['compare_de_std', 'compare_de_ext', 'compare_de_hyb']
NAMES = ['标准Goldak', '扩展锥形Goldak', '混合耦合Goldak']
T_LIQ = 1400.0  # 316L液相线

def get_step_temps(odb):
    """提取每步最后一个增量步的峰值温度和基板温度"""
    results = []
    for sn in odb.steps.values():
        step = odb.steps[sn.name]
        frames = step.frames
        if not frames: continue
        f = frames[-1]
        if hasattr(f, 'fieldOutputs') and 'NT11' in f.fieldOutputs:
            nt = f.fieldOutputs['NT11']
            vals = [v.data for v in nt.values]
            tmax = max(vals)
            tmin = min(vals)
            # 从step名提取步号
            try:
                snum = int(sn.name.replace('Step-', ''))
            except:
                snum = 0
            results.append((snum, tmax, tmin, len(frames)))
    return sorted(results, key=lambda x: x[0])

def get_meltpool_data(odb, liq_temp=1400.0):
    """从最后加热步提取熔池数据"""
    step_names = list(odb.steps.keys())
    # 跳过 Step-1 (杀死步)
    heating_names = [s for s in step_names if s != 'Step-1']
    
    # 取最后一步
    last_step = odb.steps[heating_names[-1]]
    f = last_step.frames[-1]
    nt = f.fieldOutputs['NT11']
    
    # 构建节点坐标缓存
    node_coords = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_coords[(inst.name, n.label)] = n.coordinates
    
    # 获取所有节点标签和温度
    hot_nodes = []
    all_instances = odb.rootAssembly.instances.values()
    inst_map = {}
    for inst in all_instances:
        for el in inst.elements:
            for nlabel in el.connectivity:
                inst_map[nlabel] = inst.name
    
    for v in nt.values:
        inst_name = inst_map.get(v.nodeLabel, list(odb.rootAssembly.instances.keys())[0])
        if (inst_name, v.nodeLabel) in node_coords:
            coord = node_coords[(inst_name, v.nodeLabel)]
            if v.data >= liq_temp:
                hot_nodes.append((v.data, coord[0], coord[1], coord[2]))
    
    if not hot_nodes:
        return {'tmax': 0, 'n_melt': 0, 'width': 0, 'depth': 0, 'length': 0}
    
    xs = [h[1] for h in hot_nodes]
    ys = [h[2] for h in hot_nodes]
    zs = [h[3] for h in hot_nodes]
    tmax = max(h[0] for h in hot_nodes)
    
    return {
        'tmax': tmax,
        'n_melt': len(hot_nodes),
        'width': (max(xs) - min(xs)) * 1000,
        'depth': (max(ys) - min(ys)) * 1000,
        'length': (max(zs) - min(zs)) * 1000,
        'tmax_loc': (hot_nodes[0][1]*1000, hot_nodes[0][2]*1000, hot_nodes[0][3]*1000)
    }

# 分析每个案例
print("=" * 80)
print("热源对比分析结果 (P=700W, η=0.5, v=5mm/s, 单层40步)")
print("=" * 80)

for i, case in enumerate(CASES):
    print(f"\n--- {NAMES[i]} ---")
    try:
        odb = openOdb(f'{case}.odb', readOnly=True)
        
        # 1. 温度演化
        step_data = get_step_temps(odb)
        print(f"  总共 {len(step_data)} 步")
        # 显示关键步
        key_steps = [s for s in step_data if s[0] in [5, 10, 15, 20, 25, 30, 35, 40, 41]]
        for snum, tmax, tmin, ninc in key_steps:
            print(f"  Step-{snum:3d}: Tmax={tmax:7.1f}°C  Tmin={tmin:6.1f}°C  inc={ninc:3d}")
        
        # 2. 最后一步平均温度和稳定段判断
        last_5 = step_data[-5:] if len(step_data) >= 5 else step_data
        last5_avg = sum(s[1] for s in last_5) / len(last_5)
        last5_std = (sum((s[1]-last5_avg)**2 for s in last_5) / len(last_5))**0.5
        print(f"  最后5步平均温度: {last5_avg:.1f}°C ± {last5_std:.1f}°C")
        
        # 3. 熔池数据
        mp = get_meltpool_data(odb)
        print(f"  峰值温度: {mp['tmax']:.1f}°C")
        print(f"  熔池节点数: {mp['n_melt']}")
        if mp['n_melt'] > 0:
            print(f"  熔宽: {mp['width']:.3f}mm")
            print(f"  熔深: {mp['depth']:.3f}mm")
            print(f"  熔长: {mp['length']:.3f}mm")
        
        # 4. 总增量步数（评估收敛性）
        total_inc = sum(s[3] for s in step_data)
        avg_inc = total_inc / len(step_data) if step_data else 0
        print(f"  总增量步: {total_inc}, 平均每步: {avg_inc:.1f}")
        
        odb.close()
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 80)
