"""
Ensena a tu robot Niryo a recoger un cubo y llevarlo a otro sitio.

Como funciona?
1. Mueve el brazo del robot con tus manos y guarda 3 posiciones:
   - Posicion 1: inicio (donde espera el robot)
   - Posicion 2: donde esta el cubo (posicion A)
   - Posicion 3: donde hay que dejar el cubo (posicion B)
2. El robot lee su sensor (como si fueran sus ojos).
3. Segun lo que detecte el sensor, el robot decide:
   - Si detecta el cubo: lo agarra en la posicion A, lo lleva
     a la posicion B y abre la pinza para soltarlo alli.
   - Si no detecta nada: se queda esperando en la posicion de inicio.
"""

from pyniryo import NiryoRobot, PinID, JointsPosition

# Direccion IP del robot (pregunta a tu profe si no la conoces)
print("Hola! Conectando con tu robot...")
robot = NiryoRobot("192.168.1.10")

print("Conectado! El robot va a calibrarse, no lo toques todavia...")
robot.calibrate_auto()

print("Abriendo la pinza...")
robot.open_gripper()

# Modo aprendizaje: el robot se relaja y tu puedes moverlo con las manos
robot.set_learning_mode(True)
print()
print("Modo aprendizaje activado!")
print("Ahora puedes mover el brazo del robot con tus manos.")
print()

# Vamos a memorizar 3 posiciones, una por una

input("Coloca el robot en la posicion 1 (inicio) y presiona ENTER...")
posicion_inicio = robot.get_joints()
print("   Posicion de inicio memorizada!")

input("Coloca el robot en la posicion 2 (donde esta el cubo, posicion A) y presiona ENTER...")
posicion_cubo = robot.get_joints()
print("   Posicion del cubo memorizada!")

input("Coloca el robot en la posicion 3 (donde dejara el cubo, posicion B) y presiona ENTER...")
posicion_destino = robot.get_joints()
print("   Posicion de destino memorizada!")

print()
print("Genial! El robot memorizo las 3 posiciones.")

# Salimos del modo aprendizaje: el robot vuelve a tener fuerza
robot.set_learning_mode(False)

input("Presiona ENTER para que el robot use su sensor y decida que hacer...")

# El robot lee su sensor en el pin DI5
# El sensor devuelve 1 si detecta el cubo, y 0 si no detecta nada
estado = robot.digital_read(PinID.DI5)
print("El sensor dice:", estado)

# Primero el robot va a la posicion de inicio
print("Moviendose a la posicion de inicio...")
robot.move(JointsPosition(*posicion_inicio))

# Ahora el robot toma una decision segun el sensor
if estado == 1:
    print("El sensor detecto el cubo! Voy a buscarlo a la posicion A.")
    robot.move(JointsPosition(*posicion_cubo))

    print("Cerrando la pinza para agarrar el cubo...")
    robot.close_gripper()

    print("Llevando el cubo a la posicion B...")
    robot.move(JointsPosition(*posicion_destino))

    print("Abriendo la pinza para soltar el cubo en la posicion B.")
    robot.open_gripper()

    print("Volviendo a la posicion de inicio...")
    robot.move(JointsPosition(*posicion_inicio))
else:
    print("El sensor no detecto ningun cubo.")
    print("Me quedo esperando en la posicion de inicio con la pinza abierta.")

print()
print("Mision cumplida! Apagando la conexion con el robot.")
robot.close_connection()
print("Hasta la proxima aventura robotica!")

