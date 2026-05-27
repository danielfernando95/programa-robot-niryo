"""Control de robot Niryo con reconocimiento de gestos de mano.

Este script utiliza OpenCV y MediaPipe para capturar la mano desde la cámara,
contar los dedos levantados y enviar comandos básicos al robot Niryo.

Los gestos reconocidos son:
- 1 dedo: abrir pinza
- 2 dedos: cerrar pinza
- 3 dedos: mover a una posición de ejemplo
- 4 dedos: mover a otra posición de ejemplo

Se incluye un filtro de estabilidad para evitar respuestas a detecciones ruidosas
y un cooldown para evitar ejecuciones repetidas demasiado rápidas.
"""

# Importamos OpenCV para capturar la cámara y mostrar video.
import cv2
# Importamos MediaPipe para la detección de manos y sus landmarks.
import mediapipe as mp
# Importamos las clases necesarias para controlar el robot Niryo.
from pyniryo import NiryoRobot, JointsPosition
# Importamos time para manejar el cooldown entre comandos.
import time

# =========================
# CONFIGURACIÓN MEDIAPIPE
# =========================
# Guardamos referencias a los módulos de mano y dibujo de MediaPipe.
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# =========================
# FUNCIONES AUXILIARES
# =========================

def contar_dedos(hand_landmarks, handedness):
    """Cuenta los dedos levantados en una mano detectada por MediaPipe.

    El resultado depende de la posición de landmarks específicos de la mano.
    El pulgar se calcula de forma distinta según si la mano es derecha o izquierda.
    """
    dedos = []

    # ===== Pulgar =====
    # El pulgar se evalúa comparando la posición x de los landmarks 4 y 3.
    # Para la mano derecha, el pulgar está abierto si el pulgar está a la izquierda
    # del dedo indicador (landmark 3). Para la mano izquierda se aplica al revés.
    if handedness == "Right":
        dedos.append(1 if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x else 0)
    else:
        dedos.append(1 if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x else 0)

    # ===== Índice, medio, anular y meñique =====
    # Para cada dedo, comparamos la altura (coordenada y) de la punta del dedo
    # con la segunda articulación. Si la punta está más arriba, el dedo está levantado.
    tips = [8, 12, 16, 20]
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            dedos.append(1)
        else:
            dedos.append(0)

    # Sumamos los dedos abiertos para obtener un número entre 0 y 5.
    return sum(dedos)


def crear_hands():
    """Crea y configura el detector de manos de MediaPipe."""
    return mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )


# =========================
# FUNCIÓN PRINCIPAL
# =========================

def main():
    """Ejecuta el bucle principal de captura, detección y control del robot."""
    # Inicializa el detector de manos y la cámara web.
    hands = crear_hands()
    cap = cv2.VideoCapture(0)

    # Intentamos conectar al robot Niryo en la IP especificada.
    # Si falla la conexión o calibración, liberamos la cámara y salimos.
    try:
        robot = NiryoRobot("169.254.200.200")
        robot.calibrate_auto()
    except Exception as e:
        print("❌ Error conectando al robot:", e)
        cap.release()
        return

    # Variables de control para evitar comandos repetidos.
    ultimo_estado = -1
    ultimo_comando_tiempo = 0
    cooldown = 1
    historial = []
    N = 5

    try:
        while True:
            # Captura un frame de la cámara.
            ret, frame = cap.read()
            if not ret:
                print("❌ Error leyendo la cámara")
                break

            # Convierte el frame a RGB porque MediaPipe espera ese formato.
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(frame_rgb)

            # Si hay al menos una mano detectada, procesamos la primera mano.
            if result.multi_hand_landmarks:
                for i, handLms in enumerate(result.multi_hand_landmarks):
                    # Dibuja los landmarks de la mano en el frame para visualización.
                    mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
                    handedness = result.multi_handedness[i].classification[0].label
                    dedos = contar_dedos(handLms, handedness)
                    print("Dedos:", dedos)

                    # Agrega el conteo al historial de los últimos N frames.
                    historial.append(dedos)
                    if len(historial) > N:
                        historial.pop(0)

                    # Solo ejecuta el comando si el mismo gesto aparece en N frames seguidos.
                    # Esto reduce la respuesta a detecciones inconsistentes.
                    if historial.count(dedos) == N:
                        tiempo_actual = time.time()
                        # Aplicamos cooldown para no enviar comandos demasiado rápido.
                        if dedos != ultimo_estado and (tiempo_actual - ultimo_comando_tiempo > cooldown):
                            ultimo_estado = dedos
                            ultimo_comando_tiempo = tiempo_actual

                            # Mapea el número de dedos detectados a acciones del robot.
                            if dedos == 1:
                                print("🟢 Abrir pinza")
                                robot.open_gripper()
                            elif dedos == 2:
                                print("🔴 Cerrar pinza")
                                robot.close_gripper()
                            elif dedos == 3:
                                print("➡️ Movimiento ejemplo")
                                pose = JointsPosition(0, 0, 0, 0, 0, 0)
                                robot.move(pose)
                            elif dedos == 4:
                                print("➡️ Movimiento ejemplo")
                                pose = JointsPosition(0.059, -0.597, -0.305, -0.017, -0.006, -0.015)
                                robot.move(pose)

            # Muestra el número de dedos detectados en la ventana de video.
            cv2.putText(
                frame,
                f"Dedos: {dedos if result.multi_hand_landmarks else 0}",
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )
            cv2.imshow("Camara", frame)

            # Comprueba si se ha pulsado ESC para salir del bucle.
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        # Liberar siempre los recursos de cámara, ventana y robot al finalizar.
        print("🔻 Cerrando programa...")
        cap.release()
        cv2.destroyAllWindows()
        robot.close_connection()


# Punto de entrada del script.
if __name__ == "__main__":
    main()
