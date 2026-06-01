"""Ejemplo básico de uso del robot Niryo para guardar y ejecutar posiciones de articulaciones.
"""
from pyniryo import NiryoRobot, JointsPosition, PoseObject
# Inicializa la conexión con el robot Niryo especificando su dirección IP.
robot = NiryoRobot("192.168.1.10")
# Calibras el robot para que sepa su posición inicial y pueda moverse correctamente.
robot.calibrate_auto()

# Abre la pinza/gripper para que el robot pueda recoger o soltar objetos.
robot.open_gripper()

# Activa el modo aprendizaje para que el robot registre las posiciones actuales
# de sus articulaciones sin ejecutar trayectorias predefinidas.
robot.set_learning_mode(True)

# Pausa la ejecución hasta que el usuario presione ENTER.
# Esto permite posicionar el robot manualmente antes de guardar los ángulos.
input("Mueve el robot y pulsa ENTER para guardar posición...")

# Lista donde se almacenarán las posiciones de las articulaciones.
posiciones = []

# Guarda tres posiciones diferentes de las articulaciones.
# Cambia el valor 3 por otro número si quieres almacenar más o menos posiciones.
for i in range(3):
    input(f"Coloca posición {i+1} y pulsa ENTER...")
    posiciones.append(robot.get_joints())

# Muestra en pantalla las posiciones guardadas para comprobación.
print(posiciones)

# Desactiva el modo aprendizaje para que el robot vuelva a controlar sus movimientos normalmente.
robot.set_learning_mode(False)

# Mueve el robot a la primera posición guardada.
# Si quieres ejecutar todas las posiciones guardadas, puedes recorrer la lista posiciones.
robot.move(JointsPosition(*posiciones[0]))

# Cierra la pinza/gripper después del movimiento.
robot.close_gripper()

# Cierra la conexión con el robot y libera recursos.
robot.close_connection()