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

import cv2
import mediapipe as mp
from pyniryo import NiryoRobot, JointsPosition
import time

# =========================
# CONFIGURACIÓN MEDIAPIPE
# =========================
# Exportamos solo las clases y utilidades de MediaPipe necesarias.
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# =========================
# FUNCIONES AUXILIARES
# =========================

def contar_dedos(hand_landmarks, handedness):
    """Cuenta los dedos levantados en una mano detectada por MediaPipe.

    :param hand_landmarks: Landmarks normalizados de la mano.
    :type hand_landmarks: mediapipe.framework.formats.landmark_pb2.NormalizedLandmarkList
    :param handedness: Etiqueta de la mano detectada, "Left" o "Right".
    :type handedness: str
    :returns: Cantidad de dedos levantados (0-5).
    :rtype: int
    """
    dedos = []

    # ===== Pulgar =====
    # El pulgar se evalúa en función de la mano izquierda o derecha.
    if handedness == "Right":
        dedos.append(1 if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x else 0)
    else:
        dedos.append(1 if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x else 0)

    # ===== Índice, medio, anular y meñique =====
    tips = [8, 12, 16, 20]
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            dedos.append(1)
        else:
            dedos.append(0)

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
    hands = crear_hands()
    cap = cv2.VideoCapture(0)

    try:
        robot = NiryoRobot("169.254.200.200")
        robot.calibrate_auto()
    except Exception as e:
        print("❌ Error conectando al robot:", e)
        cap.release()
        return

    ultimo_estado = -1
    ultimo_comando_tiempo = 0
    cooldown = 1
    historial = []
    N = 5

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error leyendo la cámara")
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(frame_rgb)

            if result.multi_hand_landmarks:
                for i, handLms in enumerate(result.multi_hand_landmarks):
                    mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
                    handedness = result.multi_handedness[i].classification[0].label
                    dedos = contar_dedos(handLms, handedness)
                    print("Dedos:", dedos)

                    historial.append(dedos)
                    if len(historial) > N:
                        historial.pop(0)

                    if historial.count(dedos) == N:
                        tiempo_actual = time.time()
                        if dedos != ultimo_estado and (tiempo_actual - ultimo_comando_tiempo > cooldown):
                            ultimo_estado = dedos
                            ultimo_comando_tiempo = tiempo_actual

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

            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        print("🔻 Cerrando programa...")
        cap.release()
        cv2.destroyAllWindows()
        robot.close_connection()


if __name__ == "__main__":
    main()
