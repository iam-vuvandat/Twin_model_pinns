import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(src_dir))

from ansys_electronic_desktop.rmxprt.synchronous_machine.reluctance_synchronous_machine.reluctance_synchronous_motor import ReluctanceSynchronousMotor

if __name__ == "__main__":
    motor = ReluctanceSynchronousMotor()
    motor.create_model()