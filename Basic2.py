"""
 ¡Enseña a tu robot Niryo a moverse! 

¿Cómo funciona?
1. Mueve el brazo del robot con tus manos a la posición que quieras.
2. Presiona ENTER para que el robot "memorice" esa posición.
3. ¡El robot repetirá tus 3 movimientos como por arte de magia!
"""

from pyniryo import NiryoRobot, JointsPosition

# Dirección IP del robot (pregunta a tu profe si no la conoces)
print("¡Hola! Conectando con tu robot...")
robot = NiryoRobot("192.168.1.10")

print("¡Conectado! El robot va a calibrarse, no lo toques todavía...")
robot.calibrate_auto()

print("Abriendo la pinza...")
robot.open_gripper()

#  Modo aprendizaje: el robot se "relaja" y tú puedes moverlo con las manos
robot.set_learning_mode(True)
print()
print("¡Modo aprendizaje activado!")
print("Ahora puedes mover el brazo del robot con tus manos.")
print()

# Vamos a memorizar 3 posiciones, una por una

input("Coloca el robot en la posición 1 y presiona ENTER...")
posicion_1 = robot.get_joints()
print("    ¡Posición 1 memorizada!")

input("Coloca el robot en la posición 2 y presiona ENTER...")
posicion_2 = robot.get_joints()
print("    ¡Posición 2 memorizada!")

input("Coloca el robot en la posición 3 y presiona ENTER...")
posicion_3 = robot.get_joints()
print("    ¡Posición 3 memorizada!")

print()
print("¡Genial! El robot memorizó tus 3 posiciones.")

#  Salimos del modo aprendizaje: el robot vuelve a tener "fuerza"
robot.set_learning_mode(False)

input(" Presiona ENTER para ver al robot repetir tus movimientos...")

# El robot repite las 3 posiciones, una por una

print("Moviéndose a la posición 1...")
robot.move(JointsPosition(*posicion_1))

print("Moviéndose a la posición 2...")
robot.move(JointsPosition(*posicion_2))

print("Moviéndose a la posición 3...")
robot.move(JointsPosition(*posicion_3))

print("Cerrando la pinza...")
robot.close_gripper()

print()
print("¡Misión cumplida! Apagando la conexión con el robot.")
robot.close_connection()
print("¡Hasta la próxima aventura robótica!")
