"""Ejemplo básico de uso del robot Niryo para leer posiciones y sensores."""
from pyniryo import NiryoRobot, PinID,JointsPosition 
# Inicializa la conexión con el robot Niryo especificando su dirección IP.
robot = NiryoRobot("192.168.1.10")

# Calibras el robot para que sepa su posición inicial y pueda moverse correctamente.
robot.calibrate_auto()

# Abre la pinza/gripper para que el robot pueda recoger o soltar objetos.
robot.open_gripper()

# Activa el modo aprendizaje para que el robot registre las posiciones actuales
robot.set_learning_mode(True)

posiciones = []

for i in range(3):
    input(f"Coloca posición {i+1} y pulsa ENTER...")
    posiciones.append(robot.get_joints())

# Desactiva el modo aprendizaje para que el robot vuelva a controlar sus movimientos normalmente.
robot.set_learning_mode(False)

# Leer sensor en pin DI1 (por ejemplo) para nuestro ejemplo el pin activo era el 5
estado = robot.digital_read(PinID.DI5)
print("Sensor:", estado)

#Ejecuta un movimiento cualquiera antes de leer el estado del sensor, por ejemplo, la posición 0 guardada.
robot.move(JointsPosition(*posiciones[0]))

# Ejecuta un movimiento basado en el estado del sensor. Si el sensor está activo (1), mueve a la posición 0 y cierra la pinza. Si no, mueve a la posición 1.
if (estado==1):
    robot.move(JointsPosition(*posiciones[1]))
    robot.close_gripper()
# Si el sensor no está activo, mueve a la posición 2 sin cerrar la pinza.
else:
    robot.move(JointsPosition(*posiciones[2]))

# Cierra la conexión con el robot y libera recursos.
robot.close_connection()

