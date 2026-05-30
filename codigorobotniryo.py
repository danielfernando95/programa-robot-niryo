"""Ejemplos básicos de movimientos y control de pinza para robot Niryo.

Este módulo contiene funciones de ejemplo para conectar al robot, calibrarlo y
moverlo tanto con posiciones de articulación como con posiciones cartesianas.
"""

from pyniryo import NiryoRobot, JointsPosition, PoseObject


def ejemplo_movimientos():
    """Ejecuta movimientos de ejemplo en el robot Niryo."""
    robot = NiryoRobot("169.254.200.200")
    try:
        """Calibra el robot."""
        robot.calibrate_auto()
        """Ejecuta movimientos del brazo robotico"""
        joints = JointsPosition(0, 0, 0, 0, 0, 0)
        robot.move(joints)

        pose = PoseObject(0.2, 0.0, 0.1, 0.0, 1.57, 0.0)
        robot.move(pose)
        """Abre y cierra el brazo robotico"""
        robot.open_gripper()
        robot.close_gripper()
    finally:
        robot.close_connection()


def main():
    """Función principal que ejecuta el ejemplo de movimiento."""
    ejemplo_movimientos()


if __name__ == "__main__":
    main()
