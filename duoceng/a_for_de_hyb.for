C ====================================================================
C     DFLUX - Hybrid Coupled Heat Source (Surface Gaussian + Volume Goldak)
C     混合/耦合体热源：表层高斯面热源 + 体积双椭球深层加热
C     总功率分配：f_surf=0.6 给表面高斯，f_vol=0.4 给体积Goldak
C     Parameters: P=800W, eta=0.4 (总吸收率)
C     Surface: Gaussian R0_s=0.85mm (体热流形式，在表面Y层集中分布)
C     Volume: 双椭球 AF=2.0mm, AR=4.0mm, B=0.85mm, C=0.6mm (减弱)
C     For duoceng single-layer 40-step INP
C ====================================================================
      SUBROUTINE DFLUX(FLUX, SOL, KSTEP, KINC, TIME, NOEL, NPT,
     1     COORDS, JLTYP, TEMP, PRESS, SNAME)

      INCLUDE 'ABA_PARAM.INC'
      DIMENSION FLUX(2), COORDS(3), TIME(2)
      CHARACTER*80 SNAME

C     ---- 激光工艺参数 ----
      REAL*8 LASER_POWER, ABSORPTIVITY, Q_TOTAL
      PARAMETER (LASER_POWER = 800.0D0)
      PARAMETER (ABSORPTIVITY = 0.40D0)
      PARAMETER (Q_TOTAL = LASER_POWER * ABSORPTIVITY)

C     ---- 功率分配系数 ----
C     f_surf: 分配给表面高斯组分的比例
C     f_vol:  分配给体积双椭球组分的比例 (f_surf + f_vol = 1.0)
      REAL*8 F_SURF, F_VOL
      PARAMETER (F_SURF = 0.60D0, F_VOL = 0.40D0)

      REAL*8 SCAN_SPEED
      PARAMETER (SCAN_SPEED = 0.005D0)

C     ---- 表面高斯热源参数（体热流形式）----
      REAL*8 R0_S, DEPTH_S
      PARAMETER (R0_S = 0.00085D0, DEPTH_S = 0.0002D0)

C     ---- 体积双椭球参数（减弱组份）----
      REAL*8 AF, AR, B, C
      PARAMETER (AF = 0.0020D0, AR = 0.0040D0)
      PARAMETER (B = 0.00085D0, C = 0.0006D0)

C     ---- 热源起始位置 ----
      REAL*8 X0, Z0_START
      PARAMETER (X0 = 0.003D0, Z0_START = 0.0D0)

C     ---- 基板表面Y坐标 ----
      REAL*8 SUB_Y
      PARAMETER (SUB_Y = 0.003D0)

      REAL*8 PI
      PARAMETER (PI = 3.141592653589793D0)

      REAL*8 X, Y, Z, Z_CURRENT
      REAL*8 DX, DY, DZ, R2, FF, FR, Q_S, Q_V
      REAL*8 FLUX_SURF, FLUX_VOL

      FLUX(1) = 0.0D0
      IF (JLTYP .NE. 1) RETURN

C     ---- 跳过杀死步(Step-1) ----
      IF (KSTEP .LE. 1) RETURN

C     ---- 坐标 ----
      X = COORDS(1)
      Y = COORDS(2)
      Z = COORDS(3)

C     ---- 热源中心Z位置随时间移动 ----
      Z_CURRENT = Z0_START + SCAN_SPEED * TIME(2)

      DX = X - X0
      DY = Y - SUB_Y
      DZ = Z - Z_CURRENT

C     ---- 排除基板节点(Y < SUB_Y) ----
      IF (Y .LT. SUB_Y) THEN
          FLUX(1) = 0.0D0
          RETURN
      END IF

C     ============================================================
C     组分1：表面高斯体热源（集中在粉道表面附近）
C     体热流：q = (f_surf * Q) / (pi * R0^2 * depth) * exp(-r2/R0^2)
C     深度方向限制在 DEPTH_S 内
C     ============================================================
      IF (DY .GE. 0.0D0 .AND. DY .LE. DEPTH_S) THEN
          R2 = (DX/R0_S)**2 + (DZ/R0_S)**2
          IF (R2 .LE. 4.0D0) THEN
              Q_S = (F_SURF * Q_TOTAL) / (PI * R0_S * R0_S * DEPTH_S)
              FLUX_SURF = Q_S * EXP(-R2)
          ELSE
              FLUX_SURF = 0.0D0
          END IF
      ELSE
          FLUX_SURF = 0.0D0
      END IF

C     ============================================================
C     组分2：体积双椭球热源（深层加热，减弱组份）
C     Standard Goldak 双椭球公式
C     ============================================================
      FLUX_VOL = 0.0D0
      IF (DY .GE. 0.0D0) THEN
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
