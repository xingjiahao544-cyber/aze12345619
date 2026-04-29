import os, shutil

BASE_FOR = "a_for_hybrid_v6.for"
OUT_DIR = "/mnt/d/temp/duoceng3"

# 读取模板
with open(os.path.join(OUT_DIR, BASE_FOR), "r") as f:
    template = f.read()

# 8组正交参数（P800_V5 已作为基线在跑）
# 功率 800: 已经包含在模板里（PARAMETER LASER_POWER=800）
# 需要修改功率、速度、DT_PER_STEP
# 注意：新 FOR 用 TIME(2) 计算 Z 位置，不依赖 DT_PER_STEP
# 所以只需要改 LASER_POWER 和 SCAN_SPEED

# 注意：短 INP 的 step-2~8 的时间行已经按速度调整好了
# P=800W, v=5mm/s 是基线，用 hyb_v6.for 直接跑

case_params = {
    # P800_V5 已跑，不需要生成
    "P800_V3":  (800, 0.003, 0.200),
    "P800_V8":  (800, 0.008, 0.075),
    "P800_V5":  (800, 0.005, 0.120),  # 基线
    "P1000_V3": (1000, 0.003, 0.200),
    "P1000_V5": (1000, 0.005, 0.120),
    "P1000_V8": (1000, 0.008, 0.075),
    "P1200_V3": (1200, 0.003, 0.200),
    "P1200_V5": (1200, 0.005, 0.120),
    "P1200_V8": (1200, 0.008, 0.075),
}

for case, (power, speed, dt) in case_params.items():
    new_for = template
    new_for = new_for.replace("LASER_POWER = 800.0D0", f"LASER_POWER = {power:.1f}D0")
    new_for = new_for.replace("SCAN_SPEED = 0.005D0", f"SCAN_SPEED = {speed:.4f}D0")
    
    out_path = os.path.join(OUT_DIR, f"a_for_hybrid_{case}.for")
    with open(out_path, "w") as f:
        f.write(new_for)
    print(f"Generated: a_for_hybrid_{case}.for  (P={power}W, v={speed*1000}mm/s)")

print("\nDone! hyb_v6 job is running, results coming soon.")
