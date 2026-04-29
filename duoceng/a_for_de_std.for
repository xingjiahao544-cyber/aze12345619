C ====================================================================
C     DFLUX - Standard Goldak Double Ellipsoid Heat Source
C     标准双椭球热源（作为基准对照）
C     Parameters: P=800W, eta=0.4, v=5mm/s
C     Shape: AF=2.0mm, AR=4.0mm, B=0.85mm, C=0.6mm
C     For duoceng single-layer 40-step INP
C ====================================================================
      SUBROUTINE DFLUX(FLUX, SOL, KSTEP, KINC, TIME, NOEL, NPT,
     1     COORDS, JLTYP, TEMP, PRESS, SNAME)

      INCLUDE 'ABA_PARAM.INC'
      DIMENSION FLUX(2), COORDS(3), TIME(2)
      CHARACTER*80 SNAME

C     ---- 激光工艺参数 ----
      REAL*8 LASER_POWER, ABSORPTIVITY, Q
      PARAMETER (LASER_POWER = 800.0D0)
      PARAMETER (ABSORPTIVITY = 0.40D0)
      PARAMETER (Q = LASER_POWER * ABSORPTIVITY)

      REAL*8 SCAN_SPEED
      PARAMETER (SCAN_SPEED = 0.005D0)

C     ---- 双椭球形状参数（米）----
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
      REAL*8 DX, DY, DZ, R2, FF, FR, Q_V

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

C     ---- 双椭球热源（Goldak标准模型）----
C     前方（DZ >= 0）使用AF
C     后方（DZ < 0）使用AR
      IF (DZ .GE. 0.0D0) THEN
          R2 = (DX/B)**2 + (DY/C)**2 + (DZ/AF)**2
          IF (R2 .LE. 4.0D0) THEN
              FF = 2.0D0 * AF / (AF + AR)
              Q_V = (6.0D0 * SQRT(3.0D0) * FF * Q) /
     1              (PI * SQRT(PI) * AF * B * C) * EXP(-3.0D0 * R2)
              FLUX(1) = Q_V
          END IF
      ELSE
          R2 = (DX/B)**2 + (DY/C)**2 + (DZ/AR)**2
          IF (R2 .LE. 4.0D0) THEN
              FR = 2.0D0 * AR / (AF + AR)
              Q_V = (6.0D0 * SQRT(3.0D0) * FR * Q) /
     1              (PI * SQRT(PI) * AR * B * C) * EXP(-3.0D0 * R2)
              FLUX(1) = Q_V
          END IF
      END IF

      RETURN
      END
