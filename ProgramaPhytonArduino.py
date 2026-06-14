"""
ROBOT NIRYO - CLASIFICADOR DE CUBOS POR COLOR
Para ninos curiosos que quieren aprender robotica!

Como funciona?
  Tenemos un sensor que VE los colores, como tus ojos.
  Primero le ensenamos al robot que colores son ROJO, VERDE y AZUL.
  Luego, cuando la cinta pone un cubo delante del sensor...
  el robot lo recoge y lo mete en la caja correcta!

Necesitas instalar estas herramientas en tu ordenador:
  pip install pyniryo pyserial
"""

import serial
import time
from pyniryo import JointsPosition, NiryoRobot, ConveyorDirection

# ----------------------------------------------------------
# PASO 1: CONECTAR CON EL ARDUINO (sensor de color)
# ----------------------------------------------------------
# Aqui ponemos el puerto donde esta conectado el Arduino.
# Es como la direccion de una casa, le decimos al ordenador donde encontrarlo.
PUERTO_ARDUINO = "COM3"   # <- cambialo si tu ordenador usa otro numero, lee el numero del arduino.

print("Hola! Conectando con el sensor de color...")
arduino = serial.Serial(PUERTO_ARDUINO, 9600, timeout=1)  #velocidad del arduino tiene que estar con la misma velocidad.
time.sleep(2)  # Esperamos 2 segundos: el Arduino necesita "despertar"
arduino.reset_input_buffer()
print("Sensor conectado!")


def leer_sensor():
    """Le preguntamos al sensor: que color ves ahora mismo?
    Nos responde con 4 numeros:
      r = cuanto ROJO hay
      g = cuanto VERDE hay  (g de "green" en ingles)
      b = cuanto AZUL hay   (b de "blue" en ingles)
      c = cuanta LUZ hay en total
    Si algo sale mal, devuelve None (que significa "nada").
    """
    arduino.reset_input_buffer()
    arduino.write(b"C")  # Mandamos la letra C al Arduino: "mide el color!"
    linea = arduino.readline().decode().strip()
    try:
        partes = linea.split(",")
        r = int(partes[0])
        g = int(partes[1])
        b = int(partes[2])
        c = int(partes[3])
        return r, g, b, c
    except (ValueError, IndexError):
        return None  # Algo salio mal, avisamos con None


def medir_promedio(veces=10):
    """Hacemos 10 medidas seguidas y calculamos el promedio.
    Por que? Porque una sola medida puede ser un error.
    Es como cuando mides algo con una regla varias veces
    para asegurarte de que el resultado es correcto.
    """
    suma_r, suma_g, suma_b, suma_c = 0, 0, 0, 0
    medidas_buenas = 0

    while medidas_buenas < veces:
        medida = leer_sensor()
        if medida is not None:
            r, g, b, c = medida
            suma_r += r
            suma_g += g
            suma_b += b
            suma_c += c
            medidas_buenas += 1
        time.sleep(0.05)

    return (suma_r / veces, suma_g / veces,
            suma_b / veces, suma_c / veces)


def a_porcentajes(r, g, b):
    """Convierte los numeros de color a porcentajes.
    Ejemplo: si r=150, g=50, b=50 -> total=250
      rojo  = 150/250 x 100 = 60%
      verde =  50/250 x 100 = 20%
      azul  =  50/250 x 100 = 20%
    Asi no importa si hay mas o menos luz en la habitacion:
    solo nos importa la MEZCLA de colores.
    """
    total = r + g + b
    if total == 0:
        return 0, 0, 0
    return (r / total * 100, g / total * 100, b / total * 100)


def parecido(color1, color2):
    """Mide cuanto se parecen dos colores.
    Cuanto MAS PEQUENO sea el numero, MAS se parecen.

    Imagina que cada color es un punto en el espacio.
    Calculamos la distancia entre los dos puntos.
    Si estan muy cerca -> colores parecidos.
    Si estan muy lejos -> colores distintos.
    """
    dr = color1[0] - color2[0]
    dg = color1[1] - color2[1]
    db = color1[2] - color2[2]
    return dr * dr + dg * dg + db * db


# ----------------------------------------------------------
# PASO 2: CONECTAR CON EL ROBOT NIRYO
# ----------------------------------------------------------
print("Conectando con el robot Niryo...")
robot = NiryoRobot("169.254.200.200")

print("Conectado! El robot se va a calibrar solo, no lo toques...")
robot.calibrate_auto()  # El robot comprueba que sus brazos funcionan bien

print("Abriendo la pinza...")
robot.open_gripper()


# ----------------------------------------------------------
# ESCUELA 1: ENSENAR LAS 5 POSICIONES AL BRAZO
# ----------------------------------------------------------
# Ponemos el robot en modo "puedo moverme con las manos"
robot.set_learning_mode(True)
print()
print("=== ESCUELA 1: ensenamos al robot donde ir ===")
print("Ahora puedes mover el brazo del robot con tus manos.")
print()

# Los 5 sitios que el robot tiene que conocer
nombres = [
    "posicion de inicio (donde espera)",
    "donde recoger el cubo de la cinta",
    "caja de los cubos ROJOS",
    "caja de los cubos VERDES",
    "caja de los cubos AZULES",
]
posiciones = []

for i in range(5):
    input("Mueve el robot a: " + nombres[i] + " -> pulsa ENTER cuando este listo...")
    posiciones.append(robot.get_joints())  # Guardamos la posicion
    print("   Posicion guardada!")

# Guardamos cada posicion con un nombre facil de recordar
posicion_inicio = posiciones[0]
posicion_cubo   = posiciones[1]
cajas = {
    "ROJO":  posiciones[2],
    "VERDE": posiciones[3],
    "AZUL":  posiciones[4],
}

robot.set_learning_mode(False)  # Desactivamos el modo manual
print("Moviendo el robot a la posicion de inicio...")
robot.move(JointsPosition(*posicion_inicio))


# ----------------------------------------------------------
# ESCUELA 2: ENSENAR LOS COLORES AL SENSOR (CALIBRACION)
# ----------------------------------------------------------
print()
print("=== ESCUELA 2: el sensor aprende los colores ===")
print("Ahora le ensenamos al sensor como se ven tus cubos.")
print("Cada cubo en cada habitacion puede verse un poco diferente")
print("segun la luz. Por eso el robot aprende CON TUS CUBOS!")
print()

# Primero medimos la cinta sin ningun cubo
# -> esto es el "color del fondo", lo usamos para detectar cuando llega un cubo
input("Deja la cinta vacia (sin cubos) y pulsa ENTER...")
r, g, b, c_vacio = medir_promedio()
print("   Sin cubo, la luz que ve el sensor es: " + str(round(c_vacio)))

# Ahora aprendemos cada color uno a uno
colores_aprendidos = {}  # Aqui guardamos lo que aprende
luz_con_cubo = []        # Cuanta luz llega con cada cubo

for nombre_color in ["ROJO", "VERDE", "AZUL"]:
    input("Pon el cubo " + nombre_color + " delante del sensor -> pulsa ENTER...")
    r, g, b, c = medir_promedio()
    mezcla = a_porcentajes(r, g, b)
    colores_aprendidos[nombre_color] = mezcla
    luz_con_cubo.append(c)
    print("   Aprendido! El " + nombre_color + " tiene -> "
          + "rojo "  + str(round(mezcla[0])) + "%, "
          + "verde " + str(round(mezcla[1])) + "%, "
          + "azul "  + str(round(mezcla[2])) + "%"
          + "  (luz total: " + str(round(c)) + ")")

# Calculamos el "umbral": el punto entre "no hay cubo" y "hay cubo"
# Si la luz supera este numero -> hay un cubo delante del sensor
umbral_deteccion = (c_vacio + min(luz_con_cubo)) / 2
print()
print("Umbral de deteccion: " + str(round(umbral_deteccion))
      + "  (entre " + str(round(c_vacio)) + " y "
      + str(round(min(luz_con_cubo))) + ")")

if min(luz_con_cubo) < c_vacio * 1.3:
    print()
    print("ATENCION: el sensor casi no nota la diferencia entre")
    print("   la cinta vacia y el cubo. Acerca mas el sensor (1-2 cm)")
    print("   y vuelve a ejecutar el programa.")


def que_color_es(r, g, b):
    """Compara el color medido con los colores que aprendimos.
    El robot elige el color que MAS se parezca.
    Es como adivinar quien es una persona mirando sus caracteristicas.
    """
    mezcla = a_porcentajes(r, g, b)
    mejor_color    = None
    mejor_parecido = None

    for nombre, mezcla_aprendida in colores_aprendidos.items():
        p = parecido(mezcla, mezcla_aprendida)
        if mejor_parecido is None or p < mejor_parecido:
            mejor_parecido = p
            mejor_color    = nombre

    return mejor_color


# ----------------------------------------------------------
# ESCUELA 3: A TRABAJAR!
# ----------------------------------------------------------
print()
print("=== ESCUELA 3: el robot ya sabe todo, a trabajar! ===")
print("Preparando la cinta transportadora...")
conveyor_id = robot.set_conveyor()

input("Pon los cubos sobre la cinta y pulsa ENTER para empezar...")

robot.run_conveyor(conveyor_id, speed=25, direction=ConveyorDirection.FORWARD)
print("La cinta esta en marcha! El sensor vigila...")

seguir_trabajando = True

while seguir_trabajando:

    medida = leer_sensor()
    if medida is None:
        time.sleep(0.1)
        continue

    r, g, b, c = medida

    # Hay cubo? Solo si la luz supera el umbral que calculamos antes
    if c < umbral_deteccion:
        time.sleep(0.05)
        continue  # Todavia no hay cubo, seguimos esperando...

    # CUBO DETECTADO!
    print()
    print("Cubo detectado! Parando la cinta...")
    robot.stop_conveyor(conveyor_id)

    robot.wait(1)  # Esperamos a que el cubo pare de moverse
    print("Mirando el color con calma...")
    r, g, b, c = medir_promedio()
    color = que_color_es(r, g, b)

    mezcla = a_porcentajes(r, g, b)
    print("   Veo -> rojo "  + str(round(mezcla[0])) + "%, "
          + "verde " + str(round(mezcla[1])) + "%, "
          + "azul "  + str(round(mezcla[2])) + "%")
    print("   Es un cubo " + color + "!")

    print("Voy a recoger el cubo...")
    robot.move(JointsPosition(*posicion_cubo))
    robot.wait(3)

    print("Cerrando la pinza para agarrar el cubo...")
    robot.close_gripper()

    print("Llevando el cubo a la caja " + color + "...")
    robot.move(JointsPosition(*cajas[color]))
    robot.wait(3)

    print("Abriendo la pinza para soltar el cubo.")
    robot.open_gripper()

    print("Volviendo a la posicion de inicio...")
    robot.move(JointsPosition(*posicion_inicio))

    respuesta = input("Quieres que el robot clasifique otro cubo? (s/n): ")
    if respuesta.lower() != "s":
        seguir_trabajando = False
    else:
        print("Arrancando la cinta de nuevo!")
        robot.run_conveyor(conveyor_id, speed=25,
                           direction=ConveyorDirection.FORWARD)
        print("El sensor vigila...")


# ----------------------------------------------------------
# RECOGER Y APAGAR TODO
# ----------------------------------------------------------
print()
print("Parando la cinta transportadora...")
robot.stop_conveyor(conveyor_id)

print("Cerrando la conexion con el sensor de color...")
arduino.close()

print("Mision cumplida! Apagando el robot.")
robot.close_connection()
print("Hasta la proxima aventura robotica!")
