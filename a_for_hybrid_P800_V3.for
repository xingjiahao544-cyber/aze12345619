C ====================================================================
C     DFLUX - Hybrid Coupled Heat Source for duoceng3 三层 316L
C     基于 duoceng 已验证的 800W/0.4/5mm/s 混合耦合热源
C     表面高斯(60%) + 体积Goldak(40%)
C     Z位置用 TIME(2) 计算（已验证正确的写法）
C ====================================================================
      SUBROUTINE DFLUX(FLUX, SOL, KSTEP, KINC, TIME, NOEL, NPT,
     1     COORDS, JLTYP, TEMP, PRESS, SNAME)

      INCLUDE 'ABA_PARAM.INC'
      DIMENSION FLUX(2), COORDS(3), TIME(2)
      CHARACTER*80 SNAME

C     ---- 激光工艺参数（基值 800W，后续其他功率由此修改）----
      REAL*8 LASER_POWER, ABSORPTIVITY, Q_TOTAL
      PARAMETER (LASER_POWER = 800.0D0)
      PARAMETER (ABSORPTIVITY = 0.40D0)
      PARAMETER (Q_TOTAL = LASER_POWER * ABSORPTIVITY)   ! 320W

C     ---- 功率分配系数 ----
      REAL*8 F_SURF, F_VOL
      PARAMETER (F_SURF = 0.60D0, F_VOL = 0.40D0)

      REAL*8 SCAN_SPEED
      PARAMETER (SCAN_SPEED = 0.0030D0)

C     ---- 表面高斯热源参数 ----
      REAL*8 R0_S, DEPTH_S
      PARAMETER (R0_S = 0.00085D0, DEPTH_S = 0.0002D0)

C     ---- 体积双椭球参数 ----
      REAL*8 AF, AR, B, C
      PARAMETER (AF = 0.0020D0, AR = 0.0040D0)
      PARAMETER (B = 0.00085D0, C = 0.0006D0)

C     ---- 几何参数 ----
C     SUB_D=基板顶面, 粉道在 Y=0.0048~0.0066 (3层×0.6mm)
C     X0=粉道中心 (粉道在 X=0.0081~0.0099, 中心=0.0090)
C     POW_L=单层长度, LAYER_T=单层厚度
      REAL*8 SUB_D, X0, POW_L, LAYER_T
      PARAMETER (SUB_D = 0.0048D0)
      PARAMETER (X0 = 0.0090D0)
      PARAMETER (POW_L = 0.024D0)
      PARAMETER (LAYER_T = 0.0006D0)

C     ---- Step-1 总时间（用于 TIME(2) 偏移）----
C     Step-1: 10.0s, Step-2~41: 每步 0.12s（5mm/s, 0.6mm/步）
      REAL*8 STEP1_TIME
      PARAMETER (STEP1_TIME = 0.1D0)

      REAL*8 PI
      PARAMETER (PI = 3.141592653589793D0)

      REAL*8 X, Y, Z, Z_CURRENT, Y0
      REAL*8 DX, DY, DZ, R2, FF, FR, Q_S, Q_V
      REAL*8 FLUX_SURF, FLUX_VOL
      REAL*8 HEAT_TIME, Z_TOTAL
      INTEGER CURRENT_LAYER, STEP_IN_LAYER
      LOGICAL IS_COOLING

      FLUX(1) = 0.0D0
      IF (JLTYP .NE. 1) RETURN

C     ---- 跳过 Step-1（杀死步）----
      IF (KSTEP .LE. 1) RETURN

C     ---- 判断冷却步 ----
      IS_COOLING = .FALSE.
      IF (KSTEP .EQ. 42 .OR. KSTEP .EQ. 83) IS_COOLING = .TRUE.
      IF (IS_COOLING) RETURN

C     ---- 判断当前层 ----
C     Layer 1: KSTEP=2~41, Layer 2: KSTEP=43~82, Layer 3: KSTEP=84~123
      IF (KSTEP .GE. 2 .AND. KSTEP .LE. 41) THEN
          CURRENT_LAYER = 1
          STEP_IN_LAYER = KSTEP - 1
      ELSE IF (KSTEP .GE. 43 .AND. KSTEP .LE. 82) THEN
          CURRENT_LAYER = 2
          STEP_IN_LAYER = KSTEP - 42
      ELSE IF (KSTEP .GE. 84 .AND. KSTEP .LE. 123) THEN
          CURRENT_LAYER = 3
          STEP_IN_LAYER = KSTEP - 83
      ELSE
          RETURN
      END IF

C     ---- 当前层热源中心Y坐标（层顶面）----
      Y0 = SUB_D + CURRENT_LAYER * LAYER_T

C     ---- 坐标 ----
      X = COORDS(1)
      Y = COORDS(2)
      Z = COORDS(3)

C     ---- 热源Z位置：使用 TIME(2)（已验证正确的写法）----
C     TIME(2) 从 Step-1 开始累积。减去 STEP1_TIME 得到加热开始后的时间
C     Z 位置：用步编号计算（不受冷却步时间影响）
      Z_CURRENT = (STEP_IN_LAYER - 1) * 0.0006D0
C     ---- 相对热源中心的坐标 ----
      DX = X - X0
      DY = Y - Y0
      DZ = Z - Z_CURRENT

C     ---- 排除基板节点 ----
      IF (Y .LT. SUB_D) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF

C     ---- Y方向截断：热源在层顶面，只向下加热一个粉道厚度 ----
C     DY>0 说明在热源上方（粉道顶部空气），排除
C     DY<-LAYER_T 说明低于当前层底部，排除
      IF (DY .GT. 1e-10 .OR. DY .LT. -(LAYER_T * 1.1D0)) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF

C     ============================================================
C     组分1：表面高斯体热源（集中在粉道表面附近）
C     体热流：q = (f_surf * Q) / (pi * R0^2 * depth) * exp(-r2/R0^2)
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
C     组分2：体积双椭球热源（深层加热，减弱组份）
C     Standard Goldak 双椭球公式
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

C     ---- 叠加两个组分 ----
      FLUX(1) = FLUX_SURF + FLUX_VOL

      RETURN
      END
