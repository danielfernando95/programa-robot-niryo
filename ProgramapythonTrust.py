"""
ROBOT NIRYO - CLASIFICADOR DE FIGURAS
Para ninos curiosos que quieren aprender robotica!

Como funciona?
  Tenemos una camara que VE las figuras, como tus ojos.
  El robot distingue CUADRADOS de CIRCULOS usando la camara
  conectada al panel trasero del Niryo.
  Solo presta atencion a figuras de color ROJO, VERDE o AZUL.
  Todo lo demas (cinta negra, sombras, paredes) es invisible para el.

La cadena de trabajo es:
  1. La cinta transportadora avanza con la figura.
  2. El sensor infrarrojo detecta que llega algo y PARA la cinta.
  3. La camara hace una foto y busca algo ROJO, VERDE o AZUL.
  4. Mide su forma: es un CUADRADO o un CIRCULO?
  5. El brazo recoge la figura y la lleva a su caja.

El programa tiene 3 escuelas:
  ESCUELA 0: ajustar la camara en directo (ventana de video).
  ESCUELA 1: ensenar las 4 posiciones al brazo.
  ESCUELA 2: a trabajar!

Necesitas instalar estas herramientas en tu ordenador:
  pip install pyniryo opencv-python numpy
"""

import time

import cv2
import numpy as np
from pyniryo import (
    JointsPosition,
    NiryoRobot,
    ConveyorDirection,
    PinID,
    PinState,
)

# ----------------------------------------------------------
# AJUSTES QUE PUEDES CAMBIAR
# ----------------------------------------------------------
IP_ROBOT = "169.254.200.200"     # <- cambia esto si hace falta
VELOCIDAD_CINTA = 25             # Velocidad de la cinta (0 = parado, 100 = maxima)

PIN_SENSOR = PinID.DI5           # Pin donde esta conectado el sensor infrarrojo
DETECTA_EN_LOW = True            # El sensor da HIGH sin objeto y LOW cuando detecta algo

AREA_MINIMA = 1500               # Tamano minimo en pixeles para considerar
                                 # que algo es una figura (descarta motas de polvo)

# La VENTANA DE ATENCION: el trozo de la foto donde esta la cinta.
# Los 4 numeros son fracciones entre 0 y 1: (izquierda, arriba, derecha, abajo)
# Se puede ajustar en vivo en la ESCUELA 0.
ZONA = [0.25, 0.25, 0.75, 0.75]
CAMARA_DEL_REVES = False         # Cambia a True si la imagen sale boca abajo

GUARDAR_FOTOS = True             # Guarda cada foto analizada como archivo .png


# ----------------------------------------------------------
# LOS COLORES QUE EL ROBOT CONOCE
# ----------------------------------------------------------
# Usamos el espacio de colores HSV (en lugar de RGB) porque
# es mas estable con cambios de luz.
#   H = tono (que color es): va de 0 a 180 en OpenCV
#   S = saturacion (cuanto color tiene): 0 = gris, 255 = color puro
#   V = brillo: 0 = negro, 255 = muy brillante
#
# El ROJO necesita dos rangos porque en la rueda de colores
# aparece tanto al principio (cerca del 0) como al final (cerca del 180).
S_MINIMA = 70    # Saturacion minima: descarta grises y colores muy palidos
V_MINIMO = 50    # Brillo minimo: descarta zonas muy oscuras o en sombra

RANGOS_COLOR = {
    "ROJO": [
        (np.array([0,   S_MINIMA, V_MINIMO]), np.array([10,  255, 255])),
        (np.array([170, S_MINIMA, V_MINIMO]), np.array([180, 255, 255])),
    ],
    "VERDE": [
        (np.array([35, S_MINIMA, V_MINIMO]), np.array([85, 255, 255])),
    ],
    "AZUL": [
        (np.array([90, S_MINIMA, V_MINIMO]), np.array([130, 255, 255])),
    ],
}


# ----------------------------------------------------------
# LA CAMARA
# ----------------------------------------------------------
def hacer_foto():
    """Pide una foto a la camara del panel trasero del robot.

    La foto llega comprimida (como un archivo .jpg por dentro)
    y la descomprimimos con np.frombuffer + cv2.imdecode.
    Si la camara esta del reves, la giramos 180 grados.
    Si algo sale mal, devuelve None (que significa "nada").
    """
    try:
        datos = np.frombuffer(robot.get_img_compressed(), dtype=np.uint8)
        img = cv2.imdecode(datos, cv2.IMREAD_COLOR)
        if img is not None and CAMARA_DEL_REVES:
            img = cv2.rotate(img, cv2.ROTATE_180)
        return img
    except Exception as error:
        print("   No pude recibir la foto: " + str(error))
        return None


def recortar_zona(imagen):
    """Recorta la ventana de atencion de la imagen completa.

    Convierte las fracciones de ZONA en pixeles reales y devuelve
    solo ese trozo de la imagen, mas las coordenadas x1 e y1
    (las necesitamos despues para dibujar el contorno en la foto completa).
    """
    alto, ancho = imagen.shape[:2]
    x1 = int(ZONA[0] * ancho)
    y1 = int(ZONA[1] * alto)
    x2 = int(ZONA[2] * ancho)
    y2 = int(ZONA[3] * alto)
    return imagen[y1:y2, x1:x2], x1, y1


# ----------------------------------------------------------
# EL CEREBRO: ENCONTRAR LA FIGURA Y DECIR SU FORMA Y COLOR
# ----------------------------------------------------------
def que_figura_es(recorte):
    """Busca algo ROJO, VERDE o AZUL y decide si es cuadrado o circulo.

    PASO A - crear mascaras de color:
      Para cada color conocido, crea una imagen donde solo se ve
      lo que es de ese color. Todo lo demas queda negro (invisible).

    PASO B - quedarse con la mancha mas grande:
      Si hay varias manchas de distintos colores, gana la mas grande.
      Asi el robot se centra en la figura principal.

    PASO C - medir la forma de la mancha:
      Calculamos cuanto rellena la mancha su rectangulo minimo
      y su circulo minimo.
        Un cuadrado rellena ~100% del rectangulo y ~64% del circulo.
        Un circulo rellena ~78% del rectangulo y ~100% del circulo.
      Comparamos con esos valores ideales y gana el que mas se parezca.

    Devuelve (forma, color, contorno, explicacion).
    Si no encuentra nada, devuelve (None, None, None, explicacion).
    """
    # Convertimos la imagen a HSV y la suavizamos un poco
    # para reducir el ruido (puntitos de color que no son figura)
    hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)
    hsv = cv2.GaussianBlur(hsv, (5, 5), 0)
    nucleo = np.ones((5, 5), np.uint8)

    mejor_color = None
    mejor_contorno = None
    mejor_area = 0

    # PASO A y B: buscar la mancha de color mas grande
    for nombre_color, rangos in RANGOS_COLOR.items():
        mascara = None
        for bajo, alto_rango in rangos:
            trozo = cv2.inRange(hsv, bajo, alto_rango)
            # Para el rojo, unimos los dos trozos de la rueda de colores
            mascara = trozo if mascara is None else cv2.bitwise_or(mascara, trozo)

        # MORPH_OPEN: elimina motas pequenas (ruido)
        # MORPH_CLOSE: rellena agujeritos dentro de la figura (brillos del plástico)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN,  nucleo)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, nucleo)

        contornos, _ = cv2.findContours(
            mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contornos:
            continue

        contorno = max(contornos, key=cv2.contourArea)
        area = cv2.contourArea(contorno)
        if area > mejor_area:
            mejor_area = area
            mejor_color = nombre_color
            mejor_contorno = contorno

    if mejor_contorno is None or mejor_area < AREA_MINIMA:
        return None, None, None, "no veo nada rojo, verde ni azul"

    # PASO C: medir la forma
    # Rectangulo minimo que rodea la figura
    rect = cv2.minAreaRect(mejor_contorno)
    ancho_r, alto_r = rect[1]
    if ancho_r == 0 or alto_r == 0:
        return None, None, None, "contorno raro"
    relleno_rect = mejor_area / (ancho_r * alto_r)

    # Circulo minimo que rodea la figura
    (_, _), radio = cv2.minEnclosingCircle(mejor_contorno)
    relleno_circ = mejor_area / (np.pi * radio * radio)

    # Distancia al perfil ideal de cada forma
    # Cuanto menor sea la distancia, mas se parece a esa forma
    dist_cuadrado = ((relleno_rect - 1.00) ** 2
                     + (relleno_circ - 0.64) ** 2)
    dist_circulo  = ((relleno_rect - 0.78) ** 2
                     + (relleno_circ - 1.00) ** 2)

    forma = "CUADRADO" if dist_cuadrado < dist_circulo else "CIRCULO"

    explicacion = (mejor_color
                   + " | rect " + str(round(relleno_rect * 100)) + "%"
                   + " circ " + str(round(relleno_circ * 100)) + "%")
    return forma, mejor_color, mejor_contorno, explicacion


def dibujar_resultado(imagen, forma, color, contorno, explicacion):
    """Dibuja en la foto lo que el robot ha visto y decidido.

    Dibuja:
      - Un rectangulo azul alrededor de la ventana de atencion
      - El contorno verde alrededor de la figura encontrada
      - Un texto con la forma y el color detectados
    """
    alto, ancho = imagen.shape[:2]
    x1 = int(ZONA[0] * ancho)
    y1 = int(ZONA[1] * alto)
    x2 = int(ZONA[2] * ancho)
    y2 = int(ZONA[3] * alto)
    cv2.rectangle(imagen, (x1, y1), (x2, y2), (255, 0, 0), 2)
    if contorno is not None:
        cv2.drawContours(imagen, [contorno + np.array([[x1, y1]])],
                         -1, (0, 255, 0), 3)
    titulo = (str(forma) + " " + str(color)) if forma else "nada"
    cv2.putText(imagen, titulo, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    cv2.putText(imagen, str(explicacion), (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return imagen


def mirar_y_decidir(numero_foto):
    """Hace una foto, analiza la ventana de atencion y decide que figura es.

    Si GUARDAR_FOTOS esta activado, guarda la foto con el resultado dibujado.
    Devuelve (forma, color) o (None, None) si no encuentra nada.
    """
    imagen = hacer_foto()
    if imagen is None:
        return None, None

    recorte, _, _ = recortar_zona(imagen)
    forma, color, contorno, explicacion = que_figura_es(recorte)
    print("   (" + str(explicacion) + ")")

    if GUARDAR_FOTOS:
        dibujar_resultado(imagen, forma, color, contorno, explicacion)
        cv2.imwrite("foto_analizada_" + str(numero_foto) + ".png", imagen)

    return forma, color


# ----------------------------------------------------------
# CONECTAR CON EL ROBOT
# ----------------------------------------------------------
print("Hola! Conectando con tu robot Niryo...")
robot = NiryoRobot(IP_ROBOT)

print("Conectado! El robot va a calibrarse, no lo toques todavia...")
robot.calibrate_auto()  # El robot comprueba que sus brazos funcionan bien

print("Abriendo la pinza...")
robot.open_gripper()

print()
print("Probando la camara del panel trasero...")
foto_prueba = hacer_foto()
if foto_prueba is None:
    print("ATENCION: no recibo imagen de la camara.")
    print("Revisa el cable USB del panel trasero y vuelve a ejecutar.")
    robot.close_connection()
    raise SystemExit
alto, ancho = foto_prueba.shape[:2]
print("Camara funcionando! Imagenes de "
      + str(ancho) + "x" + str(alto) + " pixeles.")


# ----------------------------------------------------------
# ESCUELA 0: AJUSTAR LA CAMARA EN DIRECTO
# ----------------------------------------------------------
print()
print("=== ESCUELA 0: ajustar la camara en directo ===")
respuesta = input("Quieres abrir la ventana de ajuste? (s/n): ")

if respuesta.lower() == "s":
    print()
    print("Se va a abrir una ventana de video en directo. TECLAS:")
    print("   J / L -> mover la ventana azul a izquierda / derecha")
    print("   U / O -> mover la ventana azul arriba / abajo")
    print("   I / K -> ventana mas pequena / mas grande")
    print("   R     -> girar la imagen 180 grados")
    print("   Q     -> terminar el ajuste y continuar")
    print()
    print("Pon una figura en la zona y mueve la camara hasta que")
    print("la decision sea correcta y estable. Lo que ajustes")
    print("aqui se usa directamente en el resto del programa.")

    PASO = 0.02  # Cuanto se mueve la ventana azul con cada tecla
    while True:
        imagen = hacer_foto()
        if imagen is None:
            continue

        recorte, _, _ = recortar_zona(imagen)
        forma, color, contorno, explicacion = que_figura_es(recorte)
        dibujar_resultado(imagen, forma, color, contorno, explicacion)

        cv2.imshow("Ajustar camara (Q para continuar)", imagen)
        tecla = cv2.waitKey(30) & 0xFF

        if tecla == ord("q"):
            break
        elif tecla == ord("r"):
            CAMARA_DEL_REVES = not CAMARA_DEL_REVES
        elif tecla == ord("j"):
            ZONA[0] = max(0, ZONA[0] - PASO)
            ZONA[2] = max(ZONA[0] + 0.1, ZONA[2] - PASO)
        elif tecla == ord("l"):
            ZONA[2] = min(1, ZONA[2] + PASO)
            ZONA[0] = min(ZONA[2] - 0.1, ZONA[0] + PASO)
        elif tecla == ord("u"):
            ZONA[1] = max(0, ZONA[1] - PASO)
            ZONA[3] = max(ZONA[1] + 0.1, ZONA[3] - PASO)
        elif tecla == ord("o"):
            ZONA[3] = min(1, ZONA[3] + PASO)
            ZONA[1] = min(ZONA[3] - 0.1, ZONA[1] + PASO)
        elif tecla == ord("i"):
            # Hacer la ventana mas pequeña por los 4 lados
            ZONA[0] = min(ZONA[0] + PASO, ZONA[2] - 0.1)
            ZONA[1] = min(ZONA[1] + PASO, ZONA[3] - 0.1)
            ZONA[2] = max(ZONA[2] - PASO, ZONA[0] + 0.1)
            ZONA[3] = max(ZONA[3] - PASO, ZONA[1] + 0.1)
        elif tecla == ord("k"):
            # Hacer la ventana mas grande por los 4 lados
            ZONA[0] = max(0, ZONA[0] - PASO)
            ZONA[1] = max(0, ZONA[1] - PASO)
            ZONA[2] = min(1, ZONA[2] + PASO)
            ZONA[3] = min(1, ZONA[3] + PASO)

    cv2.destroyAllWindows()
    print()
    print("Ajuste guardado para esta sesion.")
    print("Si quieres que sea el ajuste por defecto, copia esto al principio del codigo:")
    print("   ZONA = [" + str(round(ZONA[0], 2)) + ", "
          + str(round(ZONA[1], 2)) + ", "
          + str(round(ZONA[2], 2)) + ", "
          + str(round(ZONA[3], 2)) + "]")
    print("   CAMARA_DEL_REVES = " + str(CAMARA_DEL_REVES))


# ----------------------------------------------------------
# ESCUELA 1: ENSENAR LAS 4 POSICIONES AL BRAZO
# ----------------------------------------------------------
robot.set_learning_mode(True)
print()
print("=== ESCUELA 1: ensenamos al robot donde ir ===")
print("Ahora puedes mover el brazo del robot con tus manos.")
print()

# Los 4 sitios que el robot tiene que conocer
nombres = [
    "inicio (que NO tape la camara!)",
    "donde recoger la figura de la cinta",
    "caja de los CUADRADOS",
    "caja de los CIRCULOS",
]
posiciones = []

for i in range(4):
    input("Mueve el robot a: " + nombres[i] + " -> pulsa ENTER cuando este listo...")
    posiciones.append(robot.get_joints())  # Guardamos la posicion
    print("   Posicion guardada!")

# Guardamos cada posicion con un nombre facil de recordar
posicion_inicio = posiciones[0]
posicion_figura = posiciones[1]
cajas = {
    "CUADRADO": posiciones[2],
    "CIRCULO":  posiciones[3],
}

robot.set_learning_mode(False)  # Desactivamos el modo manual
print("Moviendo el robot a la posicion de inicio...")
robot.move(JointsPosition(*posicion_inicio))


# ----------------------------------------------------------
# ESCUELA 2: A TRABAJAR!
# ----------------------------------------------------------
print()
print("=== ESCUELA 2: el robot ya sabe todo, a trabajar! ===")
print("Preparando la cinta transportadora...")
conveyor_id = robot.set_conveyor()

input("Pon las figuras sobre la cinta y pulsa ENTER para empezar...")

robot.run_conveyor(conveyor_id, speed=VELOCIDAD_CINTA,
                   direction=ConveyorDirection.FORWARD)
print("La cinta esta en marcha! El sensor infrarrojo vigila...")

seguir_trabajando = True
detectado_antes = False   # Recordamos si en el ciclo anterior habia figura
contador_fotos = 0


def sensor_detecta():
    """Pregunta al sensor infrarrojo: hay algo delante de ti?

    El sensor da HIGH cuando no hay nada y LOW cuando detecta un objeto.
    Esto se llama logica invertida y es normal en sensores de este tipo.
    Devuelve True si hay un objeto, False si no hay nada.
    """
    estado = robot.digital_read(PIN_SENSOR)
    if DETECTA_EN_LOW:
        return estado == PinState.LOW
    return estado == PinState.HIGH


while seguir_trabajando:

    detectado_ahora = sensor_detecta()

    # Solo actuamos en el momento exacto en que LLEGA la figura
    # (cuando pasa de "no habia nada" a "hay algo")
    if detectado_ahora and not detectado_antes:
        print()
        print("Figura detectada por el sensor infrarrojo!")
        print("Parando la cinta...")
        robot.stop_conveyor(conveyor_id)

        robot.wait(1)  # Esperamos a que la figura este bien quieta

        print("La camara esta mirando la figura...")
        contador_fotos += 1
        forma, color = mirar_y_decidir(contador_fotos)

        # Si no lo tiene claro, lo intenta una segunda vez
        if forma is None:
            print("No lo veo claro. Miro otra vez...")
            robot.wait(1)
            contador_fotos += 1
            forma, color = mirar_y_decidir(contador_fotos)

        if forma is None:
            print("No veo ninguna figura roja, verde o azul.")
            print("Revisa la foto guardada, la luz y la ventana azul.")
            input("Retira la figura de la cinta y pulsa ENTER...")
        else:
            print("Es un " + forma + " de color " + color + "!")

            print("Voy a recoger la figura...")
            robot.move(JointsPosition(*posicion_figura))
            robot.wait(3)

            print("Cerrando la pinza para agarrar la figura...")
            robot.close_gripper()

            print("Llevando la figura a la caja de " + forma + "S...")
            robot.move(JointsPosition(*cajas[forma]))
            robot.wait(3)

            print("Abriendo la pinza para soltar la figura.")
            robot.open_gripper()

            print("Volviendo a la posicion de inicio...")
            robot.move(JointsPosition(*posicion_inicio))

        respuesta = input("Quieres clasificar otra figura? (s/n): ")
        if respuesta.lower() != "s":
            seguir_trabajando = False
        else:
            print("Arrancando la cinta de nuevo...")
            robot.run_conveyor(conveyor_id, speed=VELOCIDAD_CINTA,
                               direction=ConveyorDirection.FORWARD)
            print("El sensor vigila...")
            detectado_ahora = False
            time.sleep(0.5)

    detectado_antes = detectado_ahora
    time.sleep(0.05)  # Esperamos un poquito antes de volver a mirar el sensor


# ----------------------------------------------------------
# RECOGER Y APAGAR TODO
# ----------------------------------------------------------
print()
print("Parando la cinta transportadora...")
robot.stop_conveyor(conveyor_id)

print("Mision cumplida! Apagando la conexion con el robot.")
robot.close_connection()
print("Hasta la proxima aventura robotica!")
