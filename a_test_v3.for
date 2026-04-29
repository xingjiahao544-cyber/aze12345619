C ====================================================================
C     DFLUX - 混合耦合（简化版，去掉所有Y方向截断）
C     只排除基板(Y<SUB_D)和冷却步
C ====================================================================
      SUBROUTINE DFLUX(FLUX, SOL, KSTEP, KINC, TIME, NOEL, NPT,
     1     COORDS, JLTYP, TEMP, PRESS, SNAME)
C
      INCLUDE 'ABA_PARAM.INC'
      DIMENSION FLUX(2), COORDS(3), TIME(2)
      CHARACTER*80 SNAME
C
      REAL*8 LASER_POWER, ABSORPTIVITY, Q_TOTAL
      PARAMETER (LASER_POWER = 1000.0D0, ABSORPTIVITY = 0.4D0)
      PARAMETER (Q_TOTAL = LASER_POWER * ABSORPTIVITY)
C
      REAL*8 F_SURF, F_VOL
      PARAMETER (F_SURF = 0.60D0, F_VOL = 0.40D0)
C
      REAL*8 R0_S, DEPTH_S, PI
      PARAMETER (R0_S = 0.00085D0, DEPTH_S = 0.0002D0)
      PARAMETER (PI = 3.141592653589793D0)
C
      REAL*8 AF, AR, B, C
      PARAMETER (AF = 0.0020D0, AR = 0.0040D0)
      PARAMETER (B = 0.00085D0, C = 0.0006D0)
C
      REAL*8 SUB_D, X0, Z0_START, Y0, SCAN_SPEED, DT_PER_STEP
      PARAMETER (SUB_D = 0.0048D0, X0 = 0.0090D0, Z0_START = 0.0D0)
      PARAMETER (Y0 = 0.0054D0)
      PARAMETER (SCAN_SPEED = 0.005D0, DT_PER_STEP = 0.12D0)
C
      REAL*8 X, Y, Z, Z_CURRENT, DX, DY, DZ, R2
      REAL*8 FLUX_SURF, FLUX_VOL, FF, FR, Q0_S, Q0_V
C
      FLUX(1) = 0.0D0
      IF (JLTYP .NE. 1) RETURN
      IF (KSTEP .LE. 1) RETURN
      IF (KSTEP .EQ. 42 .OR. KSTEP .EQ. 83) RETURN  ! cooling
C
      X = COORDS(1)
      Y = COORDS(2)
      Z = COORDS(3)
C
C     只排除基板
      IF (Y .LT. SUB_D) RETURN
C
      Z_CURRENT = Z0_START + SCAN_SPEED * (KSTEP-2) * DT_PER_STEP
C
      DX = X - X0
      DY = Y - Y0
      DZ = Z - Z_CURRENT
C
C     ===== 表面高斯 =====
      FLUX_SURF = 0.0D0
      IF (DY .GE. -DEPTH_S .AND. DY .LE. 0.0D0) THEN
          R2 = (DX/R0_S)**2 + (DZ/R0_S)**2
          IF (R2 .LE. 9.0D0) THEN  ! 扩大范围
              Q0_S = (F_SURF * Q_TOTAL) / (PI * R0_S * R0_S * DEPTH_S)
              FLUX_SURF = Q0_S * EXP(-R2)
          END IF
      END IF
C
C     ===== 体积双椭球 =====
      FLUX_VOL = 0.0D0
      IF (DY .GE. -2.0D0*C) THEN  ! 允许向下 1.2mm
          IF (DZ .GE. 0.0D0) THEN
              R2 = (DX/B)**2 + (DY/C)**2 + (DZ/AF)**2
              IF (R2 .LE. 9.0D0) THEN
                  FF = 2.0D0 * AF / (AF + AR)
                  Q0_V = (6.0D0 * SQRT(3.0D0) * FF * F_VOL * Q_TOTAL) /
     1                   (PI * SQRT(PI) * AF * B * C)
                  FLUX_VOL = Q0_V * EXP(-3.0D0 * R2)
              END IF
          ELSE
              R2 = (DX/B)**2 + (DY/C)**2 + (DZ/AR)**2
              IF (R2 .LE. 9.0D0) THEN
                  FR = 2.0D0 * AR / (AF + AR)
                  Q0_V = (6.0D0 * SQRT(3.0D0) * FR * F_VOL * Q_TOTAL) /
     1                   (PI * SQRT(PI) * AR * B * C)
                  FLUX_VOL = Q0_V * EXP(-3.0D0 * R2)
              END IF
          END IF
      END IF
C
      FLUX(1) = FLUX_SURF + FLUX_VOL
C
      RETURN
      END
