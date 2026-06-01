from pyniryo import JointsPosition, NiryoRobot, ConveyorDirection, PinID

# Conexion con el robot Niryo
robot = NiryoRobot('<robot_ip_address>')

# Calibrar robot
robot.calibrate_auto()

# Abrir pinza
robot.open_gripper()

posiciones = []

# Guardar 3 posiciones manualmente
for i in range(3):
    input(f"Coloca posición {i+1} y pulsa ENTER...")
    posiciones.append(robot.get_joints())

# Salir del modo aprendizaje
robot.set_learning_mode(False)

# Configurar cinta
conveyor_id = robot.set_conveyor()

# Arrancar cinta
robot.run_conveyor(conveyor_id, speed=50, direction=ConveyorDirection.FORWARD)

Bandera = True
estado_anterior = 0  # Para detectar flanco

# Bucle principal
while Bandera:
    estado = robot.digital_read(PinID.DI5)
    print("Sensor:", estado)

    # Detectar cambio de 0 -> 1 (flanco)
    if estado == 1 and estado_anterior == 0:
        print("Objeto detectado")

        # Parar cinta
        robot.stop_conveyor(conveyor_id)

        # Ir a recoger
        robot.move(JointsPosition(*posiciones[1]))
        robot.wait(3)
        robot.close_gripper()

        # Ir a dejar
        robot.move(JointsPosition(*posiciones[2]))
        robot.wait(3)
        robot.open_gripper()

        # Reanudar cinta
        robot.run_conveyor(conveyor_id, speed=50, direction=ConveyorDirection.FORWARD)

        # Preguntar al usuario
        respuesta = input("¿Continuar? (s/n): ")
        if respuesta.lower() != 's':
            Bandera = False

    estado_anterior = estado