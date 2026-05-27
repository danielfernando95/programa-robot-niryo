## 🎥 Demo

Haz clic en la imagen para ver el robot en acción:

[![Ver demo del robot](https://img.youtube.com/vi/D8cBuTXmOnY/0.jpg)](https://youtu.be/D8cBuTXmOnY)


# 🤖 Control de robot Niryo con gestos de mano

Proyecto para controlar un robot Niryo mediante reconocimiento de gestos usando OpenCV y MediaPipe.

Incluye:
- Control en tiempo real con la mano
- Ejemplos básicos de movimiento del robot

---

## 📂 Estructura del proyecto

- `programa.py` → Control del robot mediante gestos de mano
- `codigorobotnirio.py` → Ejemplos básicos de movimiento y control de pinza

---

## 🧠 Funcionalidad (gestos)

El sistema detecta el número de dedos levantados:

- 1 dedo → Abrir pinza
- 2 dedos → Cerrar pinza
- 3 dedos → Movimiento a posición 1
- 4 dedos → Movimiento a posición 2

Incluye:
- Filtro de estabilidad
- Cooldown entre comandos

---

## 📦 Requisitos

- Python 3
- OpenCV
- MediaPipe
- pyniryo

Instalar dependencias:

```bash
pip install opencv-python mediapipe pyniryo
