C ====================================================================
C     DFLUX 用户子程序 - 三层熔覆模拟（混合耦合热源）
C     表面高斯(60%) + 体积Goldak(40%) 
C     基于 duoceng3 的 123 步结构
C     Y方向修复：热源在粉道顶面，双向加热
C ====================================================================
      SUBROUTINE DFLUX(FLUX, SOL, KSTEP, KINC, TIME, NOEL, NPT,
     1     COORDS, JLTYP, TEMP, PRESS, SNAME)
C
      INCLUDE 'ABA_PARAM.INC'
      DIMENSION FLUX(2), COORDS(3), TIME(2)
      CHARACTER*80 SNAME
C
C     ========== 工艺参数 ==========
      REAL*8 LASER_POWER, ABSORPTIVITY, Q_TOTAL
      PARAMETER (LASER_POWER = 1000.0D0, ABSORPTIVITY = 0.4D0)
      PARAMETER (Q_TOTAL = LASER_POWER * ABSORPTIVITY)   ! 400 W
      PARAMETER (SCAN_SPEED = 0.005D0)
C
C     功率分配系数
      REAL*8 F_SURF, F_VOL
      PARAMETER (F_SURF = 0.60D0, F_VOL = 0.40D0)
C
C     表面高斯组分：R0_S=深度衰减半径, DEPTH_S=表层厚度
      REAL*8 R0_S, DEPTH_S, PI, Q0_S
      PARAMETER (R0_S = 0.00085D0, DEPTH_S = 0.0002D0)
      PARAMETER (PI = 3.141592653589793D0)
C
C     体积Goldak组分：AF/AR前后半轴, B宽度, C深度
      REAL*8 AF, AR, B, C
      PARAMETER (AF = 0.0020D0, AR = 0.0040D0)
      PARAMETER (B = 0.00085D0, C = 0.0006D0)
C
C     ========== 几何参数 ==========
      REAL*8 SUB_D, POW_X0, LAYER_LENGTH
      PARAMETER (SUB_D = 0.0048D0, POW_X0 = 0.0081D0)
      PARAMETER (LAYER_LENGTH = 0.024D0)
C
      REAL*8 X0, Z0_START
      PARAMETER (X0 = POW_X0 + 0.0009D0)   ! 粉道中心
      PARAMETER (Z0_START = 0.0D0)
C
      INTEGER TOTAL_ACTIVE_STEPS, STEPS_PER_LAYER
      PARAMETER (TOTAL_ACTIVE_STEPS = 120, STEPS_PER_LAYER = 40)
C
      REAL*8 Y_LAYER1, Y_LAYER2, Y_LAYER3
      PARAMETER (Y_LAYER1 = SUB_D + 0.0006D0)   ! 0.0054 (Layer 1 顶面)
      PARAMETER (Y_LAYER2 = SUB_D + 0.0012D0)   ! 0.0060 (Layer 2 顶面)
      PARAMETER (Y_LAYER3 = SUB_D + 0.0018D0)   ! 0.0066 (Layer 3 顶面)
C
C     ========== 局部变量 ==========
      REAL*8 X, Y, Z, Z_CURRENT, Y0, DX, DY, DZ, R2
      REAL*8 Z_TOTAL, SCAN_TIME_ELAPSED
      INTEGER CURRENT_LAYER, ACTIVE_STEP
      LOGICAL IS_COOLING_STEP
      PARAMETER (DT_PER_STEP = 0.12D0)
C
      REAL*8 FLUX_SURF, FLUX_VOL, FF, FR, Q0_V
C
      FLUX(1) = 0.0D0
      IF (JLTYP .NE. 1) RETURN
C
C     ---- 步序号映射 ----
      IF (KSTEP .EQ. 1) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF
C
      IS_COOLING_STEP = .FALSE.
C
      IF (KSTEP .GE. 2 .AND. KSTEP .LE. 41) THEN
          ACTIVE_STEP = KSTEP - 1
      ELSE IF (KSTEP .EQ. 42) THEN
          IS_COOLING_STEP = .TRUE.
      ELSE IF (KSTEP .GE. 43 .AND. KSTEP .LE. 82) THEN
          ACTIVE_STEP = KSTEP - 2
      ELSE IF (KSTEP .EQ. 83) THEN
          IS_COOLING_STEP = .TRUE.
      ELSE IF (KSTEP .GE. 84 .AND. KSTEP .LE. 123) THEN
          ACTIVE_STEP = KSTEP - 3
      ELSE
          RETURN
      END IF
C
      IF (IS_COOLING_STEP) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF
C
C     ---- 当前层 Y0 ----
      CURRENT_LAYER = (ACTIVE_STEP - 1) / STEPS_PER_LAYER + 1
      IF (CURRENT_LAYER .EQ. 1) THEN
          Y0 = Y_LAYER1
      ELSE IF (CURRENT_LAYER .EQ. 2) THEN
          Y0 = Y_LAYER2
      ELSE IF (CURRENT_LAYER .EQ. 3) THEN
          Y0 = Y_LAYER3
      ELSE
          RETURN
      END IF
C
      X = COORDS(1)
      Y = COORDS(2)
      Z = COORDS(3)
C
      SCAN_TIME_ELAPSED = (ACTIVE_STEP - 1) * DT_PER_STEP
      Z_TOTAL = Z0_START + SCAN_SPEED * SCAN_TIME_ELAPSED
      Z_CURRENT = Z_TOTAL - (CURRENT_LAYER - 1) * LAYER_LENGTH
C
      DX = X - X0
      DY = Y - Y0
      DZ = Z - Z_CURRENT
C
C     Y方向截断：基板排除 + 只在当前层粉道范围内加热
      IF (Y .LT. SUB_D) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF
C     热源在粉道顶面(Y0)，向下加热0.6mm(粉道厚度)
      IF (DY .GT. 0.0D0 .OR. DY .LT. -0.0006D0) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF
C
C     ============================================================
C     组分1：表面高斯体热源（体热通量形式，集中在表层）
C     ============================================================
      FLUX_SURF = 0.0D0
      IF (ABS(DY) .LE. DEPTH_S) THEN
          R2 = (DX/R0_S)**2 + (DZ/R0_S)**2
          IF (R2 .LE. 4.0D0) THEN
              Q0_S = (F_SURF * Q_TOTAL) / (PI * R0_S * R0_S * DEPTH_S)
              FLUX_SURF = Q0_S * EXP(-R2)
          END IF
      END IF
C
C     ============================================================
C     组分2：体积双椭球热源（深层加热，减弱组份）
C     允许 DY<0 加热粉道下半部分（热源中心在粉道顶部）
C     ============================================================
      FLUX_VOL = 0.0D0
      IF (ABS(DY) .LE. 2.0D0 * C) THEN
          IF (DZ .GE. 0.0D0) THEN
              R2 = (DX/B)**2 + (DY/C)**2 + (DZ/AF)**2
              IF (R2 .LE. 4.0D0) THEN
                  FF = 2.0D0 * AF / (AF + AR)
                  Q0_V = (6.0D0 * SQRT(3.0D0) * FF * F_VOL * Q_TOTAL) /
     1                   (PI * SQRT(PI) * AF * B * C)
                  FLUX_VOL = Q0_V * EXP(-3.0D0 * R2)
              END IF
          ELSE
              R2 = (DX/B)**2 + (DY/C)**2 + (DZ/AR)**2
              IF (R2 .LE. 4.0D0) THEN
                  FR = 2.0D0 * AR / (AF + AR)
                  Q0_V = (6.0D0 * SQRT(3.0D0) * FR * F_VOL * Q_TOTAL) /
     1                   (PI * SQRT(PI) * AR * B * C)
                  FLUX_VOL = Q0_V * EXP(-3.0D0 * R2)
              END IF
          END IF
      END IF
C
C     ---- 叠加 ----
      FLUX(1) = FLUX_SURF + FLUX_VOL
C
      RETURN
      END
