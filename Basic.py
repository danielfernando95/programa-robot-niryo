# ============================================================
# MI PRIMER PROGRAMA PARA EL ROBOT NED2
# ============================================================
# Este programa hace que el robot:
#   1. Vaya a su casita (HOME)
#   2. Mueva sus brazos a diferentes posiciones
#   3. Regrese a su casita
# ============================================================

# --------------------------
# PASO 1: Traer herramientas, conectar robot, calibrar robot
# --------------------------
# Necesitamos JointsPosition para decirle al robot
# a dónde mover cada articulación.
from pyniryo import JointsPosition
# El robot tiene una dirección especial, como tu casa tiene
# un número en la calle. Esta es la dirección del robot:
DIRECCION_DEL_ROBOT = "169.254.200.200"
# Le decimos al robot que nos escuche
robot = NiryoRobot(DIRECCION_DEL_ROBOT)
#Calibramos el robot para que el sepa están sus brazos
robot.calibrate_auto()
# --------------------------
# PASO 2: Crear la posición HOME
# --------------------------
# HOME es la casita del robot.
# Todas las articulaciones están en cero (0).

home = JointsPosition(0.0002,0.4994,-1.2506,0,0,0)

# --------------------------
# PASO 3: Ir a HOME
# --------------------------
# El robot va a su casita.

robot.move(home)

# --------------------------
# PASO 4: Crear el primer movimiento
# --------------------------
# Movemos la BASE (J1) un poquito a la derecha.

posicion_1 = JointsPosition(0.3, 0, 0, 0, 0, 0)
robot.move(posicion_1)

# --------------------------
# PASO 5: Crear el segundo movimiento
# --------------------------
# Movemos el BRAZO (J2) para que baje un poco.

posicion_2 = JointsPosition(0.3, 0.2, 0, 0, 0, 0)
robot.move(posicion_2)

# --------------------------
# PASO 6: Crear el tercer movimiento
# --------------------------
# Doblamos el CODO (J3) un poquito.

posicion_3 = JointsPosition(0.3, 0.2, -0.3, 0, 0, 0)
robot.move(posicion_3)

# --------------------------
# PASO 7: Crear el cuarto movimiento
# --------------------------
# Movemos la MUÑECA (J5) hacia arriba.

posicion_4 = JointsPosition(0.3, 0.2, -0.3, 0, 0.2, 0)
robot.move(posicion_4)

# --------------------------
# PASO 8: Regresar a HOME
# --------------------------
# Siempre regresamos a la casita al terminar.

robot.move(home)

# ============================================================
# ¡FIN DEL PROGRAMA!
# ============================================================

