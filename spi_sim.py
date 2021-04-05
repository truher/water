"""Simulated sensor output"""
from typing import List
import lib


def main() -> None:
    """simulate sensor output"""

    #pylint: disable=too-few-public-methods
    class SimulatorSpiDev:
        """simulated sensor"""
        def __init__(self) -> None:
            self.angle = 0
        #pylint: disable=unused-argument, missing-function-docstring
        def xfer2(self, req: List[int]) -> List[int]:
            self.angle += 1
            if self.angle > 16383:
                self.angle -= 16384
            parity = lib.has_even_parity(self.angle)
            return [((not parity) << 7) | (self.angle >> 8) & 0xff, self.angle & 0xff]

    spi = SimulatorSpiDev()

    sensor = lib.Sensor(spi)

    while True:
        try:
            lib.log_angle(sensor.transfer(lib.ANGLE_READ_REQUEST) & 0b0011111111111111)
        except lib.ResponseLengthException as err:
            print(f"Response Length Exception {err}")
        except lib.ResponseParityException as err:
            print(f"Response Parity Exception {err}")
        except lib.ResponseErrorRegisterException as err:
            print(f"Response Error Register {err}")


if __name__ == "__main__":
    main()
