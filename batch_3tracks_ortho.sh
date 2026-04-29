#!/bin/bash
# batch_3tracks_ortho.sh — 三道三层正交实验批量处理
# 用法：先 cd 到脚本目录，然后 bash batch_3tracks_ortho.sh
#
# 流程：
# 1. 创建 9 组 FOR 文件（替换 P/v 参数）
# 2. 逐个运行 aze_3tracks_ortho.py 生成 INP
# 3. 逐个提交 Abaqus job（顺序提交，避免 FOR 编译冲突）

WORKDIR="/mnt/d/temp/duoceng3"
FOR_TEMPLATE="$WORKDIR/a_3tracks_hybrid_ortho.for"
AZE_SCRIPT="$WORKDIR/aze_3tracks_ortho.py"

# CASES: P x v (3x3=9组)
# P = 800, 1000, 1200 W
# v = 3, 5, 8 mm/s
CASES=(
  "P800_V3:800.0:0.003"
  "P800_V5:800.0:0.005"
  "P800_V8:800.0:0.008"
  "P1000_V3:1000.0:0.003"
  "P1000_V5:1000.0:0.005"
  "P1000_V8:1000.0:0.008"
  "P1200_V3:1200.0:0.003"
  "P1200_V5:1200.0:0.005"
  "P1200_V8:1200.0:0.008"
)

echo "===== 三道三层 316L 正交实验 ====="
echo "热源: 混合耦合(表面高斯60%+体积Goldak40%)"
echo "η = 0.40"
echo ""

# Step 1: 创建 9 个 FOR 文件
echo "=== Step 1: 创建 9 个 FOR 文件 ==="
for CASE_INFO in "${CASES[@]}"; do
  IFS=':' read -r CASE_NAME POWER_VAL SPEED_VAL <<< "$CASE_INFO"
  FOR_FILE="$WORKDIR/a_3tracks_${CASE_NAME}.for"
  
  # 替换 POWER 和 SPEED
  sed -e "s/LASER_POWER = 1000.0D0/LASER_POWER = ${POWER_VAL}D0/" \
      -e "s/SCAN_SPEED = 0.0050D0/SCAN_SPEED = ${SPEED_VAL}D0/" \
      "$FOR_TEMPLATE" > "$FOR_FILE"
  
  echo "  已创建: a_3tracks_${CASE_NAME}.for (P=${POWER_VAL}W, v=$(echo "$SPEED_VAL*1000" | bc)mm/s)"
done
echo ""

# Step 2: 逐个生成 INP（必须逐个运行 CAE）
echo "=== Step 2: 逐个生成 INP ==="
for CASE_INFO in "${CASES[@]}"; do
  IFS=':' read -r CASE_NAME POWER_VAL SPEED_VAL <<< "$CASE_INFO"
  INP_FILE="$WORKDIR/ortho3t_${CASE_NAME}.inp"
  
  if [ -f "$INP_FILE" ]; then
    echo "  INP 已存在: ortho3t_${CASE_NAME}.inp，跳过生成"
  else
    echo "  生成 INP: ortho3t_${CASE_NAME}.inp ..."
    # 需要在 Windows Abaqus CAE 中运行
    # 注意：要确保 FOR 文件在运行 CAE 之前已存在
    cmd.exe /c "abaqus cae noGUI=D:\\temp\\duoceng3\\aze_3tracks_ortho.py -- ${CASE_NAME}"
    echo "  完成"
  fi
done
echo ""

# Step 3: 逐个提交 Abaqus job
echo "=== Step 3: 逐个提交 Abaqus job ==="
echo "注意：将逐个提交，确保 FOR 编译不冲突"
echo ""

for CASE_INFO in "${CASES[@]}"; do
  IFS=':' read -r CASE_NAME POWER_VAL SPEED_VAL <<< "$CASE_INFO"
  JOB_NAME="ortho3t_${CASE_NAME}"
  INP_FILE="$WORKDIR/${JOB_NAME}.inp"
  FOR_FILE="a_3tracks_${CASE_NAME}.for"
  
  if [ ! -f "$INP_FILE" ]; then
    echo "  警告: $INP_FILE 不存在，跳过"
    continue
  fi
  
  echo "  提交 Job: ${JOB_NAME}"
  echo "    FOR: ${FOR_FILE}"
  echo "    P=$(echo "$POWER_VAL/1" | bc)W, v=$(echo "$SPEED_VAL*1000" | bc)mm/s"
  
  # 清理旧 .obj 缓存，确保 FOR 重新编译
  rm -f "$WORKDIR"/*.obj "$WORKDIR"/*.o "$WORKDIR"/*.exe
  
  # 提交（后台运行）
  cd "$WORKDIR"
  cmd.exe /c "abaqus job=${JOB_NAME} user=D:\\temp\\duoceng3\\${FOR_FILE} int ask=OFF" &
  
  # 等待标准求解器进程启动后再提交下一个
  # 简单等待 10 秒让编译完成
  echo "    等待 30 秒以确保编译完成..."
  sleep 30
  
  # 检查是否已经启动
  if tasklist.exe 2>/dev/null | grep -qi "standard.exe\|abaqus"; then
    echo "    求解器已启动，继续等待..."
    sleep 10
  fi
  
  echo "    提交完成"
  echo ""
done

echo "===== 所有 9 组已提交 ====="
echo "使用以下命令检查进度:"
echo "  watch -n 30 'ls -la $WORKDIR/ortho3t_*.sta 2>/dev/null | wc -l'"
echo "  tail -f $WORKDIR/ortho3t_P1000_V5.msg"
