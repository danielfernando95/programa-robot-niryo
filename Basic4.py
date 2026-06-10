"""
Ensena a tu robot Niryo a trabajar con una cinta transportadora.

Como funciona?
1. Guardas 3 posiciones moviendo el brazo con tus manos:
   - Posicion 1: inicio (donde espera el robot)
   - Posicion 2: donde recoge el cubo de la cinta (posicion A)
   - Posicion 3: donde deja el cubo (posicion B)
2. La cinta empieza a moverse y trae los cubos hacia el sensor.
3. Cuando el sensor detecta un cubo:
   - La cinta se para.
   - El robot recoge el cubo, lo lleva a la posicion B y lo suelta.
   - La cinta vuelve a arrancar para traer el siguiente cubo.
4. Despues de cada cubo, el programa te pregunta si quieres continuar.
"""

from pyniryo import JointsPosition, NiryoRobot, ConveyorDirection, PinID

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

# Vamos a memorizar 3 posiciones usando un bucle for.
# El bucle repite lo mismo 3 veces para no escribirlo 3 veces.
nombres = ["inicio", "recoger el cubo (posicion A)", "dejar el cubo (posicion B)"]
posiciones = []

for i in range(3):
    input("Coloca el robot en la posicion de " + nombres[i] + " y presiona ENTER...")
    posiciones.append(robot.get_joints())
    print("   Posicion de " + nombres[i] + " memorizada!")

posicion_inicio = posiciones[0]
posicion_cubo = posiciones[1]
posicion_destino = posiciones[2]

print()
print("Genial! El robot memorizo las 3 posiciones.")

# Salimos del modo aprendizaje: el robot vuelve a tener fuerza
robot.set_learning_mode(False)

# El robot se coloca en la posicion de inicio para empezar
print("Moviendose a la posicion de inicio...")
robot.move(JointsPosition(*posicion_inicio))

# Preparamos la cinta transportadora
print("Preparando la cinta transportadora...")
conveyor_id = robot.set_conveyor()

input("Pon los cubos sobre la cinta y presiona ENTER para empezar...")

# Arrancamos la cinta hacia adelante a velocidad 50
robot.run_conveyor(conveyor_id, speed=50, direction=ConveyorDirection.FORWARD)
print("La cinta esta en marcha! Esperando a que llegue un cubo...")

# Esta variable es como un interruptor: mientras sea True, el robot sigue trabajando
seguir_trabajando = True

# Guardamos lo que decia el sensor la vez anterior.
# Asi sabemos cuando un cubo ACABA de llegar (el sensor pasa de 0 a 1),
# y no recogemos el mismo cubo dos veces.
estado_anterior = 0

# Bucle principal: se repite una y otra vez mientras el interruptor este encendido
while seguir_trabajando:

    # El robot mira su sensor: 1 = hay un cubo delante, 0 = no hay nada
    estado = robot.digital_read(PinID.DI5)

    # Solo actuamos si ANTES no habia nada (0) y AHORA si hay algo (1).
    # Eso significa que acaba de llegar un cubo nuevo.
    if estado == 1 and estado_anterior == 0:
        print()
        print("Cubo detectado por el sensor!")

        # Paramos la cinta para que el cubo no se escape
        print("Parando la cinta...")
        robot.stop_conveyor(conveyor_id)

        # El robot va a buscar el cubo a la posicion A
        print("Voy a recoger el cubo a la posicion A...")
        robot.move(JointsPosition(*posicion_cubo))

        # Esperamos 3 segundos para que el brazo este bien quieto antes de agarrar
        robot.wait(3)
        print("Cerrando la pinza para agarrar el cubo...")
        robot.close_gripper()

        # Llevamos el cubo a la posicion B
        print("Llevando el cubo a la posicion B...")
        robot.move(JointsPosition(*posicion_destino))

        # Otra pequena espera para soltar el cubo con cuidado
        robot.wait(3)
        print("Abriendo la pinza para soltar el cubo.")
        robot.open_gripper()

        # El robot vuelve al inicio, listo para el siguiente cubo
        print("Volviendo a la posicion de inicio...")
        robot.move(JointsPosition(*posicion_inicio))

        # Arrancamos la cinta otra vez para que traiga el siguiente cubo
        print("Arrancando la cinta de nuevo...")
        robot.run_conveyor(conveyor_id, speed=50, direction=ConveyorDirection.FORWARD)

        # Preguntamos si quiere seguir con mas cubos
        respuesta = input("Quieres que el robot recoja otro cubo? (s/n): ")
        if respuesta.lower() != "s":
            # Apagamos el interruptor: el bucle while terminara
            seguir_trabajando = False

    # Guardamos el estado actual para compararlo en la siguiente vuelta del bucle
    estado_anterior = estado

# Al salir del bucle, dejamos todo ordenado
print()
print("Parando la cinta transportadora...")
robot.stop_conveyor(conveyor_id)

print("Mision cumplida! Apagando la conexion con el robot.")
robot.close_connection()
print("Hasta la proxima aventura robotica!")
