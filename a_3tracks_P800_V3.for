C ====================================================================
C     DFLUX - Hybrid Coupled Heat Source for duoceng3 三层三道 316L
C     表面高斯(60%) + 体积Goldak(40%)
C     3 tracks x 40 Z-layers/layer x 3 Y-layers + 2 cooling = 363 steps
C     Step mapping (363-step structure):
C       Layer1: Step-2~41(T1), Step-42~81(T2), Step-82~121(T3) → cooling=122
C       Layer2: Step-123~162(T1), Step-163~202(T2), Step-203~242(T3) → cooling=243
C       Layer3: Step-244~283(T1), Step-284~323(T2), Step-324~363(T3)
C     Track 1: Z forward (0~24mm), X0_1
C     Track 2: Z reverse (24~0mm), X0_2 = X0_1 + track_pitch
C     Track 3: Z forward (0~24mm), X0_3 = X0_1 + 2*track_pitch
C     Overlap 30%: track_pitch = 0.0018 * 0.7 = 0.00126
C ====================================================================
      SUBROUTINE DFLUX(FLUX, SOL, KSTEP, KINC, TIME, NOEL, NPT,
     1     COORDS, JLTYP, TEMP, PRESS, SNAME)

      INCLUDE 'ABA_PARAM.INC'
      DIMENSION FLUX(2), COORDS(3), TIME(2)
      CHARACTER*80 SNAME

C     ---- 激光工艺参数 ----
      REAL*8 LASER_POWER, ABSORPTIVITY, Q_TOTAL, SCAN_SPEED
      PARAMETER (LASER_POWER = 800.0D0)
      PARAMETER (ABSORPTIVITY = 0.40D0)
      PARAMETER (Q_TOTAL = LASER_POWER * ABSORPTIVITY)
      PARAMETER (SCAN_SPEED = 0.003D0)

C     ---- 正交实验参数：由生成脚本修改下面的值 ----
C     P800_V3:   LASER_POWER=800.0,  SCAN_SPEED=0.003
C     P800_V5:   LASER_POWER=800.0,  SCAN_SPEED=0.005
C     P800_V8:   LASER_POWER=800.0,  SCAN_SPEED=0.008
C     P1000_V3:  LASER_POWER=1000.0, SCAN_SPEED=0.003
C     P1000_V5:  LASER_POWER=1000.0, SCAN_SPEED=0.005
C     P1000_V8:  LASER_POWER=1000.0, SCAN_SPEED=0.008
C     P1200_V3:  LASER_POWER=1200.0, SCAN_SPEED=0.003
C     P1200_V5:  LASER_POWER=1200.0, SCAN_SPEED=0.005
C     P1200_V8:  LASER_POWER=1200.0, SCAN_SPEED=0.008

C     ---- 功率分配系数 ----
      REAL*8 F_SURF, F_VOL
      PARAMETER (F_SURF = 0.60D0, F_VOL = 0.40D0)

C     ---- 热源参数 ----
      REAL*8 R0_S, DEPTH_S, AF, AR, B, C
      PARAMETER (R0_S = 0.00085D0, DEPTH_S = 0.0002D0)
      PARAMETER (AF = 0.0020D0, AR = 0.0040D0)
      PARAMETER (B = 0.00085D0, C = 0.0006D0)

C     ---- 几何参数 ----
C     基板: X=0~0.018, Y=0~0.0048, Z=0~0.024
C     三道中心: X0_1=0.00573, X0_2=0.00699, X0_3=0.00825
      REAL*8 SUB_D, LAYER_T, TRACK_W, TRACK_P, POW_L
      REAL*8 X0_1, X0_2, X0_3
      PARAMETER (SUB_D = 0.0048D0)
      PARAMETER (LAYER_T = 0.0006D0)
      PARAMETER (TRACK_W = 0.0018D0)
      PARAMETER (TRACK_P = 0.00126D0)
      PARAMETER (POW_L = 0.024D0)
      PARAMETER (X0_1 = 0.00573D0)
      PARAMETER (X0_2 = X0_1 + TRACK_P)
      PARAMETER (X0_3 = X0_2 + TRACK_P)

      REAL*8 PI
      PARAMETER (PI = 3.141592653589793D0)

C     ---- 步映射参数 ----
C     363步结构:
C       Layer1: Step-2~121 (120步), cooling=122
C       Layer2: Step-123~242 (120步), cooling=243
C       Layer3: Step-244~363 (120步)
C       STEPS_PER_LAYER = 120, STEPS_PER_TRACK = 40
      INTEGER STEPS_PER_TRACK, TRACKS_PER_LAYER, STEPS_PER_LAYER
      PARAMETER (STEPS_PER_TRACK = 40)
      PARAMETER (TRACKS_PER_LAYER = 3)
      PARAMETER (STEPS_PER_LAYER = STEPS_PER_TRACK * TRACKS_PER_LAYER)

C     ---- 变量 ----
      REAL*8 X, Y, Z, Y0
      REAL*8 DX, DY, DZ, R2, FF, FR, Q_S, Q_V
      REAL*8 FLUX_SURF, FLUX_VOL, Z_TRACK, Z_STEP
      REAL*8 X_CENTERS(3)
      INTEGER CURRENT_LAYER, CURRENT_TRACK, STEP_IN_TRACK
      INTEGER GLOBAL_STEP_IN_LAYER

      FLUX(1) = 0.0D0
      IF (JLTYP .NE. 1) RETURN

C     ---- 跳过 Step-1（杀死步）----
      IF (KSTEP .LE. 1) RETURN

C     ---- 判断冷却步（跳过）----
      IF (KSTEP .EQ. 122 .OR. KSTEP .EQ. 243) RETURN

C     ---- 判断当前层和道（基于 KSTEP，363步结构）----
C     Layer 1: KSTEP 2~41 (T1), 42~81 (T2), 82~121 (T3)
C     Layer 2: KSTEP 123~162 (T1), 163~202 (T2), 203~242 (T3)
C     Layer 3: KSTEP 244~283 (T1), 284~323 (T2), 324~363 (T3)

      IF (KSTEP .GE. 2 .AND. KSTEP .LE. 121) THEN
          CURRENT_LAYER = 1
          GLOBAL_STEP_IN_LAYER = KSTEP - 1        ! 1~120
      ELSE IF (KSTEP .GE. 123 .AND. KSTEP .LE. 242) THEN
          CURRENT_LAYER = 2
          GLOBAL_STEP_IN_LAYER = KSTEP - 122       ! 1~120
      ELSE IF (KSTEP .GE. 244 .AND. KSTEP .LE. 363) THEN
          CURRENT_LAYER = 3
          GLOBAL_STEP_IN_LAYER = KSTEP - 243       ! 1~120
      ELSE
          RETURN
      END IF

C     ---- 判断当前道 ----
C     GLOBAL_STEP_IN_LAYER 1~40=T1, 41~80=T2, 81~120=T3
      IF (GLOBAL_STEP_IN_LAYER .GE. 1 .AND.
     1     GLOBAL_STEP_IN_LAYER .LE. STEPS_PER_TRACK) THEN
          CURRENT_TRACK = 1
          STEP_IN_TRACK = GLOBAL_STEP_IN_LAYER
      ELSE IF (GLOBAL_STEP_IN_LAYER .GT. STEPS_PER_TRACK .AND.
     1         GLOBAL_STEP_IN_LAYER .LE. 2 * STEPS_PER_TRACK) THEN
          CURRENT_TRACK = 2
          STEP_IN_TRACK = GLOBAL_STEP_IN_LAYER - STEPS_PER_TRACK
      ELSE IF (GLOBAL_STEP_IN_LAYER .GT. 2 * STEPS_PER_TRACK .AND.
     1         GLOBAL_STEP_IN_LAYER .LE. STEPS_PER_LAYER) THEN
          CURRENT_TRACK = 3
          STEP_IN_TRACK = GLOBAL_STEP_IN_LAYER - 2 * STEPS_PER_TRACK
      ELSE
          RETURN
      END IF

C     ---- 当前层顶面 Y ----
      Y0 = SUB_D + CURRENT_LAYER * LAYER_T

C     ---- 坐标 ----
      X = COORDS(1)
      Y = COORDS(2)
      Z = COORDS(3)

C     ---- 当前道 X 中心 ----
      X_CENTERS(1) = X0_1
      X_CENTERS(2) = X0_2
      X_CENTERS(3) = X0_3

C     ---- 当前道 Z 位置（基于 STEP_IN_TRACK，与粉道网格对齐）----
C     Z_STEP = (STEP_IN_TRACK - 1) * 0.0006D0
C     Track 1: Z forward, 0~24mm
C     Track 2: Z reverse, 24~0mm
C     Track 3: Z forward, 0~24mm
      Z_STEP = (STEP_IN_TRACK - 1) * 0.0006D0
      IF (CURRENT_TRACK .EQ. 2) THEN
C         Reverse scan: 24mm -> 0mm
          Z_TRACK = POW_L - Z_STEP
      ELSE
C         Forward scan: 0mm -> 24mm
          Z_TRACK = Z_STEP
      END IF

C     ---- 相对热源中心的坐标 ----
      DX = X - X_CENTERS(CURRENT_TRACK)
      DY = Y - Y0
      DZ = Z - Z_TRACK

C     ---- 排除基板节点 ----
      IF (Y .LT. SUB_D) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF

C     ---- Y方向截断（10% 浮点容差）----
      IF (DY .GT. 1e-10 .OR. DY .LT. -(LAYER_T * 1.1D0)) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF

C     ---- 检查是否在当前道的X范围内 ----
      IF (ABS(DX) .GT. TRACK_W * 1.2D0) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF

C     ============================================================
C     组分1：表面高斯体热源
C     ============================================================
      FLUX_SURF = 0.0D0
      IF (ABS(DY) .LE. DEPTH_S) THEN
          R2 = (DX/R0_S)**2 + (DZ/R0_S)**2
          IF (R2 .LE. 4.0D0) THEN
              Q_S = (F_SURF * Q_TOTAL) / (PI * R0_S * R0_S * DEPTH_S)
              FLUX_SURF = Q_S * EXP(-R2)
          END IF
      END IF

C     ============================================================
C     组分2：体积双椭球热源
C     ============================================================
      FLUX_VOL = 0.0D0
      IF (ABS(DY) .LE. 2.0D0 * C) THEN
          IF (DZ .GE. 0.0D0) THEN
              R2 = (DX/B)**2 + (DY/C)**2 + (DZ/AF)**2
              IF (R2 .LE. 4.0D0) THEN
                  FF = 2.0D0 * AF / (AF + AR)
                  Q_V = (6.0D0 * SQRT(3.0D0) * FF * F_VOL * Q_TOTAL) /
     1                  (PI * SQRT(PI) * AF * B * C)
                  FLUX_VOL = Q_V * EXP(-3.0D0 * R2)
              END IF
          ELSE
              R2 = (DX/B)**2 + (DY/C)**2 + (DZ/AR)**2
              IF (R2 .LE. 4.0D0) THEN
                  FR = 2.0D0 * AR / (AF + AR)
                  Q_V = (6.0D0 * SQRT(3.0D0) * FR * F_VOL * Q_TOTAL) /
     1                  (PI * SQRT(PI) * AR * B * C)
                  FLUX_VOL = Q_V * EXP(-3.0D0 * R2)
              END IF
          END IF
      END IF

C     ---- 叠加 ----
      FLUX(1) = FLUX_SURF + FLUX_VOL

      RETURN
      END
