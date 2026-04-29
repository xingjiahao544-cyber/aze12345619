"""
extract_3tracks_ortho.py — 三道三层正交实验后处理提取
从 ortho3t_P*.odb 提取每层结束时各道的温度/熔池数据

步映射（363步结构）：
  Layer1: Step-2~41(T1), 42~81(T2), 82~121(T3) → cooling=122
  Layer2: Step-123~162(T1), 163~202(T2), 203~242(T3) → cooling=243
  Layer3: Step-244~283(T1), 284~323(T2), 324~363(T3)

提取点：
  Layer 1 结束 = Step-121 (T3 最后一步, 第40步)
  Layer 2 结束 = Step-242 (T3 最后一步, 第40步)
  Layer 3 结束 = Step-363 (T3 最后一步, 第40步)
"""

from odbAccess import openOdb

T_LIQ = 1400.0
CASES = ['P800_V3', 'P800_V5', 'P800_V8',
         'P1000_V3', 'P1000_V5', 'P1000_V8',
         'P1200_V3', 'P1200_V5', 'P1200_V8']

# 三层中每层的最后一步
LAYER_LAST_STEPS = {
    'Layer1': 'Step-121',
    'Layer2': 'Step-242',
    'Layer3': 'Step-363',
}

# 三道各自的最后一步（每层中每道的结束）
# Layer1: T1 end=Step-41, T2 end=Step-81, T3 end=Step-121
# Layer2: T1 end=Step-162, T2 end=Step-202, T3 end=Step-242
# Layer3: T1 end=Step-283, T2 end=Step-302, T3 end=Step-363

STEP_END_T1_L1 = 'Step-41'
STEP_END_T2_L1 = 'Step-81'
STEP_END_T3_L1 = 'Step-121'
STEP_END_T1_L2 = 'Step-162'
STEP_END_T2_L2 = 'Step-202'
STEP_END_T3_L2 = 'Step-242'
STEP_END_T1_L3 = 'Step-283'
STEP_END_T2_L3 = 'Step-323'
STEP_END_T3_L3 = 'Step-363'

POWDER_NAMES = ['Powder-1', 'Powder-2', 'Powder-3']

def analyze_odb(case):
    """从 ODB 分析指定 case 的温度和熔池"""
    odb_path = f'ortho3t_{case}.odb'
    print(f"\n{'='*60}")
    print(f"分析: {case}")
    print(f"{'='*60}")
    
    odb = openOdb(odb_path, readOnly=True)
    
    # 构建节点坐标缓存（用 (instance_name, node_label) 作为key，因为不同实例有相同node label）
    node_info = {}
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            node_info[(inst.name.upper(), n.label)] = (inst.name, n.coordinates)
    
    def ana_step(sname, powder_filter=None):
        """分析某步最后帧的温度"""
        if sname not in odb.steps or not odb.steps[sname].frames:
            return {p: {'peak': 0, 'molten': 0, 'hots': []} for p in POWDER_NAMES}
        
        f = odb.steps[sname].frames[-1]
        nt = f.fieldOutputs['NT11']
        
        results = {}
        for pn in POWDER_NAMES:
            results[pn] = {'peak': 0.0, 'molten': 0, 'hots': []}
        
        for v in nt.values:
            info = node_info.get((v.instance.name.upper(), v.nodeLabel))
            if not info:
                continue
            inst_name = info[0].upper()
            for pn in POWDER_NAMES:
                if pn.upper() in inst_name:
                    if v.data > results[pn]['peak']:
                        results[pn]['peak'] = v.data
                    if v.data >= T_LIQ:
                        results[pn]['molten'] += 1
                        results[pn]['hots'].append((info[1][0]*1000, info[1][1]*1000, info[1][2]*1000))
                    break
        return results
    
    def ana_substrate(sname):
        """分析基板最高温"""
        if sname not in odb.steps or not odb.steps[sname].frames:
            return 0
        f = odb.steps[sname].frames[-1]
        nt = f.fieldOutputs['NT11']
        sm = 0
        for v in nt.values:
            info = node_info.get((v.instance.name.upper(), v.nodeLabel))
            if info and info[0].upper() == 'SUBSTRATE-1' and v.data > sm:
                sm = v.data
        return sm
    
    def calc_pool_dim(hots):
        """从热点列表计算熔池尺寸"""
        if len(hots) < 2:
            return 0, 0, 0
        xs = [h[0] for h in hots]
        ys = [h[1] for h in hots]
        zs = [h[2] for h in hots]
        return max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)
    
    # ---- 三层结果 ----
    r1 = ana_step(STEP_END_T3_L1)
    r2 = ana_step(STEP_END_T3_L2)
    r3 = ana_step(STEP_END_T3_L3)
    
    # 每层峰值（所有道中最高）
    l1_peak = max(r1[p]['peak'] for p in POWDER_NAMES)
    l2_peak = max(r2[p]['peak'] for p in POWDER_NAMES)
    l3_peak = max(r3[p]['peak'] for p in POWDER_NAMES)
    
    # 每层熔池节点总数
    l1_molten = sum(r1[p]['molten'] for p in POWDER_NAMES)
    l2_molten = sum(r2[p]['molten'] for p in POWDER_NAMES)
    l3_molten = sum(r3[p]['molten'] for p in POWDER_NAMES)
    
    # Layer 3 熔池尺寸
    l3_all_hots = r3['Powder-1']['hots'] + r3['Powder-2']['hots'] + r3['Powder-3']['hots']
    l3_w, l3_d, l3_l = calc_pool_dim(l3_all_hots)
    
    # 基板最高温
    sub_peak = ana_substrate(STEP_END_T3_L3)
    
    # ---- 输出 ----
    print(f"Layer 1 (Step-{STEP_END_T3_L1}):")
    for p in POWDER_NAMES:
        print(f"  {p}: Peak={r1[p]['peak']:.0f}°C, Melt={r1[p]['molten']} nodes")
    print(f"  Total: Peak={l1_peak:.0f}°C, Melt={l1_molten} nodes")
    
    print(f"\nLayer 2 (Step-{STEP_END_T3_L2}):")
    for p in POWDER_NAMES:
        print(f"  {p}: Peak={r2[p]['peak']:.0f}°C, Melt={r2[p]['molten']} nodes")
    print(f"  Total: Peak={l2_peak:.0f}°C, Melt={l2_molten} nodes")
    
    print(f"\nLayer 3 (Step-{STEP_END_T3_L3}):")
    for p in POWDER_NAMES:
        print(f"  {p}: Peak={r3[p]['peak']:.0f}°C, Melt={r3[p]['molten']} nodes")
    print(f"  Total: Peak={l3_peak:.0f}°C, Melt={l3_molten} nodes")
    print(f"  Pool: W={l3_w:.2f}mm D={l3_d:.2f}mm L={l3_l:.2f}mm")
    print(f"  Substrate Peak: {sub_peak:.0f}°C")
    
    odb.close()
    return {
        'case': case,
        'L1_peak': l1_peak, 'L1_molten': l1_molten,
        'L2_peak': l2_peak, 'L2_molten': l2_molten,
        'L3_peak': l3_peak, 'L3_molten': l3_molten,
        'L3_W': l3_w, 'L3_D': l3_d, 'L3_L': l3_l,
        'Sub_peak': sub_peak,
        'r1': r1, 'r2': r2, 'r3': r3,
    }

# ========== 主程序 ==========
print("三道三层 316L 正交实验 — 后处理分析")
print("热源: 混合耦合(η=0.40)")
print(f"液相线: {T_LIQ}°C")
print("="*60)

all_results = []
for case in CASES:
    try:
        result = analyze_odb(case)
        all_results.append(result)
    except Exception as e:
        print(f"\n⚠️  {case}: 分析失败 - {e}")
        all_results.append({'case': case, 'L3_peak': 0, 'L3_molten': 0})

# === 汇总表 ===
print("\n" + "="*80)
print("汇总表")
print("="*80)
header = f"{'Case':>10s}  {'Q(W)':>6s}  {'v(mm/s)':>8s}  {'L1peak':>7s}  {'L2peak':>7s}  {'L3peak':>7s}"
header += f"  {'L1n':>5s}  {'L2n':>5s}  {'L3n':>5s}  {'L3W':>5s}  {'L3D':>5s}  {'L3L':>5s}  {'SubPk':>6s}"
print(header)
print("-"*80)

for r in all_results:
    case = r['case']
    parts = case.split('_')
    power = int(parts[0].replace('P',''))
    speed = int(parts[1].replace('V',''))
    effq = power * 0.4
    
    line = f"{case:>10s}  {effq:6.0f}  {speed:8d}"
    line += f"  {r['L1_peak']:7.0f}  {r['L2_peak']:7.0f}  {r['L3_peak']:7.0f}"
    line += f"  {r['L1_molten']:5d}  {r['L2_molten']:5d}  {r['L3_molten']:5d}"
    line += f"  {r['L3_W']:5.2f}  {r['L3_D']:5.2f}  {r['L3_L']:5.2f}"
    line += f"  {r['Sub_peak']:6.0f}"
    print(line)

print("-"*80)

# 找最佳
valid = [r for r in all_results if r['L3_peak'] >= T_LIQ and r['L3_peak'] > 0]
if valid:
    best = max(valid, key=lambda r: r['L3_molten'])
    print(f"\n** Recommended: {best['case']} - L3={best['L3_peak']:.0f}C, Melt={best['L3_molten']} nodes")

print("\n完成！")
