 · PY
"""
Controla tu robot Niryo con los dedos de tu mano!
 
Como funciona?
1. La camara del ordenador mira tu mano todo el tiempo.
2. El programa cuenta cuantos dedos tienes levantados.
3. Segun el numero de dedos, el robot obedece una orden:
 
   - 1 dedo  : abrir la pinza
   - 2 dedos : cerrar la pinza
   - 3 dedos : moverse a la posicion de descanso
   - 4 dedos : moverse a la posicion de trabajo
 
Para salir del programa, presiona la tecla ESC.
 
Trucos importantes que usa el programa:
- El programa espera a ver el mismo gesto varias veces seguidas
  antes de obedecer. Asi no se confunde si tu mano tiembla un poco.
- Despues de cada orden hay un pequeno tiempo de calma (1 segundo)
  para que el robot no reciba mil ordenes a la vez.
"""
 
# OpenCV: sirve para usar la camara y mostrar el video en una ventana
import cv2
# MediaPipe: es el "detective de manos", encuentra tu mano en la imagen
import mediapipe as mp
# pyniryo: sirve para darle ordenes al robot
from pyniryo import NiryoRobot, JointsPosition
# time: sirve para medir el tiempo (lo usamos para el tiempo de calma)
import time
 
# =========================
# PREPARAR EL DETECTIVE DE MANOS
# =========================
detector_de_manos = mp.solutions.hands
dibujante = mp.solutions.drawing_utils
 
# Encendemos el detective: buscara solo 1 mano y tiene que estar
# bastante seguro (70 por ciento) antes de avisar que la encontro
detector = detector_de_manos.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
)
 
# Encendemos la camara (el numero 0 es la camara principal del ordenador)
camara = cv2.VideoCapture(0)
 
# =========================
# CONECTAR CON EL ROBOT
# Escribe aqui la IP de tu robot (preguntala a tu profe)
# =========================
print("Hola! Conectando con tu robot...")
robot = NiryoRobot("169.254.200.200")
robot.calibrate_auto()
 
print("Robot listo! Muestra tu mano a la camara.")
print("Recuerda: 1 dedo abre la pinza, 2 dedos la cierran,")
print("3 y 4 dedos mueven el robot. Presiona ESC para salir.")
 
# =========================
# MEMORIA DEL PROGRAMA
# =========================
ultimo_gesto = -1            # el ultimo gesto que el robot obedecio
momento_ultima_orden = 0     # cuando dimos la ultima orden
tiempo_de_calma = 1          # segundos de espera entre ordenes
historial = []               # los ultimos gestos que vimos
VECES_SEGUIDAS = 5           # cuantas veces seguidas hay que ver el gesto
 
dedos = 0  # empezamos suponiendo que no hay dedos levantados
 
# =========================
# BUCLE PRINCIPAL
# Se repite sin parar hasta que presiones ESC
# =========================
while True:
 
    # Sacamos una foto con la camara
    foto_correcta, foto = camara.read()
    if not foto_correcta:
        print("No pude leer la camara.")
        break
 
    # La camara da los colores al reves de como los quiere MediaPipe,
    # asi que los convertimos antes de buscar la mano
    foto_en_colores_rgb = cv2.cvtColor(foto, cv2.COLOR_BGR2RGB)
    resultado = detector.process(foto_en_colores_rgb)
 
    # Si el detective encontro una mano...
    if resultado.multi_hand_landmarks:
        for i, mano in enumerate(resultado.multi_hand_landmarks):
 
            # Dibujamos los puntos sobre la mano para que los veas en pantalla
            dibujante.draw_landmarks(foto, mano, detector_de_manos.HAND_CONNECTIONS)
 
            # Preguntamos si es la mano derecha o la izquierda
            lado = resultado.multi_handedness[i].classification[0].label
 
            # =========================
            # CONTAR LOS DEDOS LEVANTADOS
            # MediaPipe pone 21 puntos sobre tu mano, como pegatinas:
            # uno en cada punta de dedo, en cada nudillo y en la muneca.
            # Comparando esos puntos sabemos si cada dedo esta arriba o abajo.
            # =========================
            dedos_levantados = []
 
            # EL PULGAR es especial: se mueve hacia los lados, no hacia arriba.
            # Miramos si su punta (punto 4) esta a un lado o al otro de su
            # nudillo (punto 3). Cambia segun la mano sea derecha o izquierda.
            if lado == "Right":
                if mano.landmark[4].x < mano.landmark[3].x:
                    dedos_levantados.append(1)
                else:
                    dedos_levantados.append(0)
            else:
                if mano.landmark[4].x > mano.landmark[3].x:
                    dedos_levantados.append(1)
                else:
                    dedos_levantados.append(0)
 
            # LOS OTROS 4 DEDOS (indice, medio, anular y menique) son faciles:
            # si la punta esta MAS ARRIBA que su nudillo, el dedo esta levantado.
            # Los numeros 8, 12, 16 y 20 son las pegatinas de las puntas.
            puntas = [8, 12, 16, 20]
            for punta in puntas:
                if mano.landmark[punta].y < mano.landmark[punta - 2].y:
                    dedos_levantados.append(1)
                else:
                    dedos_levantados.append(0)
 
            # Sumamos los unos: el resultado es un numero entre 0 y 5
            dedos = sum(dedos_levantados)
            print("Dedos levantados:", dedos)
 
            # =========================
            # DECIDIR SI OBEDECEMOS EL GESTO
            # =========================
 
            # Guardamos el gesto en el historial (solo los ultimos 5)
            historial.append(dedos)
            if len(historial) > VECES_SEGUIDAS:
                historial.pop(0)
 
            # Solo obedecemos si vimos el MISMO gesto 5 veces seguidas.
            # Asi el robot no se confunde con manos temblorosas.
            if historial.count(dedos) == VECES_SEGUIDAS:
 
                ahora = time.time()
                es_un_gesto_nuevo = dedos != ultimo_gesto
                ya_paso_la_calma = (ahora - momento_ultima_orden) > tiempo_de_calma
 
                # Obedecemos solo si es un gesto nuevo Y ya paso el tiempo de calma
                if es_un_gesto_nuevo and ya_paso_la_calma:
                    ultimo_gesto = dedos
                    momento_ultima_orden = ahora
 
                    # Cada numero de dedos es una orden diferente
                    if dedos == 1:
                        print("Orden: abrir la pinza")
                        robot.open_gripper()
                    elif dedos == 2:
                        print("Orden: cerrar la pinza")
                        robot.close_gripper()
                    elif dedos == 3:
                        print("Orden: ir a la posicion de descanso")
                        posicion_descanso = JointsPosition(0, 0, 0, 0, 0, 0)
                        robot.move(posicion_descanso)
                    elif dedos == 4:
                        print("Orden: ir a la posicion de trabajo")
                        posicion_trabajo = JointsPosition(0.059, -0.597, -0.305, -0.017, -0.006, -0.015)
                        robot.move(posicion_trabajo)
 
    # Escribimos en la pantalla cuantos dedos vemos ahora mismo
    if resultado.multi_hand_landmarks:
        texto = "Dedos: " + str(dedos)
    else:
        texto = "Dedos: 0 (no veo tu mano)"
    cv2.putText(foto, texto, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
 
    # Mostramos el video en una ventana
    cv2.imshow("Camara", foto)
 
    # Si presionas la tecla ESC (numero 27), salimos del bucle
    if cv2.waitKey(1) & 0xFF == 27:
        break
 
# =========================
# APAGAR TODO CON ORDEN
# Cuando salimos del bucle, apagamos la camara,
# cerramos la ventana y nos despedimos del robot
# =========================
print("Cerrando el programa con cuidado...")
camara.release()
cv2.destroyAllWindows()
robot.close_connection()
print("Hasta la proxima aventura robotica!")
