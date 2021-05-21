"""Decodes and logs angular data from AMS AS5048A."""
# pylint: disable=import-error, import-outside-toplevel, fixme, missing-function-docstring

import argparse
import time
import logging
from typing import Any, List
from meter import Meter
from sensor import Sensor
from volume import Volume
from writer import DataWriter
import spi

# pylint: disable=too-few-public-methods
class Reader:
    """Reads data from the sensor and sends it to the listeners."""
    def __init__(self, spi: Any, writers: List[DataWriter]) -> None:
        self.spi = spi
        self.writers = writers

    _SAMPLE_PERIOD_NS: int = 4000000 # 0.004s = 250hz = 4x oversampling

    @staticmethod
    def _wait_for_next_sample() -> None:
        """Sleeps until time to take the next sample."""
        now_ns: int = time.time_ns()
        waiting_ns: int = int(Reader._SAMPLE_PERIOD_NS - (now_ns % Reader._SAMPLE_PERIOD_NS))
        time.sleep(waiting_ns / 1e9)

    def run(self) -> None:
        """Handles input in a continuous loop."""

        sensor: Sensor = Sensor(self.spi)
        meter: Meter = Meter()
        volume: Volume = Volume()

        # used for error recovery and startup
        make_extra_request: bool = True

        while True:
            try:
                if make_extra_request:
                    make_extra_request = False
                    sensor.read_angle()

                Reader._wait_for_next_sample()
                now_ns = time.time_ns()

                # TODO: hide this spi-specific stuff
                #angle = sensor.transfer(Sensor.ANGLE_READ_REQUEST) & Sensor.RESPONSE_MASK
                angle = sensor.read_angle()
                logging.debug("angle %s", angle)

                meter.update(angle)
                volume.update(now_ns, meter.read())
                for writer in self.writers:
                    writer.write(now_ns, meter.read(), volume.read())

            except Sensor.ResponseLengthException as err:
                make_extra_request = True
                logging.debug("Response Length Exception %s", err)
            except Sensor.ResponseParityException as err:
                make_extra_request = True
                logging.debug("Response Parity Exception %s", err)
            except Sensor.ResponseErrorRegisterException as err:
                make_extra_request = True
                logging.debug("Response Error Register %s", err)

def parse() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true", help="use fake spidev, for testing")
    parser.add_argument("--verbose", action="store_true", help="read everything, not just angle")
    args: argparse.Namespace = parser.parse_args()
    return args

def main() -> None:
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S', level=logging.INFO)

    writer_min = DataWriter("data_min", 60, 0)     # archival, keep forever
    writer_sec = DataWriter("data_sec", 1, 604800) # temporary, keep 7 days
    Reader(spi.make_and_setup_spi(parse()), [writer_sec, writer_min]).run()

if __name__ == "__main__":
    main()
