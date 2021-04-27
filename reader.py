"""Decode and log angular data from AMS AS5048A."""
# pylint: disable=import-error, import-outside-toplevel, fixme
import time
from typing import Any, List
from meter import Meter
from volume import Volume
from writer import DataWriter
from sensor import Sensor

# pylint: disable=too-few-public-methods
class Reader:
    """read from the sensor"""
    def __init__(self, spi: Any, writers: List[DataWriter]) -> None:
        self.spi = spi
        self.writers = writers

    # 5hz full speed
    # nyquist would be 10hz sample rate
    # let's leave it at 50hz for now
    # maybe reduce it later
    #sample_period_ns = 2e7 # 0.02s
    _SAMPLE_PERIOD_NS: int = 5000000 # 0.005s

    def run(self) -> None:
        """read input"""

        sensor: Sensor = Sensor(self.spi)
        meter: Meter = Meter()
        volume: Volume = Volume()

        while True:
            try:
                now_ns: int = time.time_ns()
                waiting_ns: int = int(Reader._SAMPLE_PERIOD_NS
                                      - (now_ns % Reader._SAMPLE_PERIOD_NS))
                time.sleep(waiting_ns / 1e9)
                now_ns = time.time_ns()

                # TODO: hide this spi-specific stuff
                angle = sensor.transfer(Sensor.ANGLE_READ_REQUEST) & Sensor.RESPONSE_MASK

                meter.update(angle)
                volume.update(now_ns, meter.read())
                for writer in self.writers:
                    writer.write(now_ns, meter.read(), volume.read())

            except Sensor.ResponseLengthException as err:
                print(f"Response Length Exception {err}")
            except Sensor.ResponseParityException as err:
                print(f"Response Parity Exception {err}")
            except Sensor.ResponseErrorRegisterException as err:
                print(f"Response Error Register {err}")
