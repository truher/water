"""Decode and log angular data from AMS AS5048A."""
# pylint: disable=import-error, import-outside-toplevel
from typing import Any
import argparse
from datetime import datetime
import time
import lib

def parse() -> Any:
    """define and parse command line args"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true",
                        help="use fake spidev, for testing/calibration")
    parser.add_argument("--verbose", action="store_true",
                        help="read everything, not just angle")
    return parser.parse_args()

def make_spi(args: Any) -> Any:
    """poor man's DI"""
    if args.fake:
        print("using fake spidev")
        import sim
        return sim.SimulatorSpiDev()
    print("using real spidev")
    import spidev # type: ignore
    return spidev.SpiDev()

def verbose(sensor: Any) -> None:
    """log extra"""
    sensor.transfer(lib.ANGLE_READ_REQUEST)
    angle: int = sensor.transfer(lib.NOP_REQUEST) & lib.RESPONSE_MASK

    sensor.transfer(lib.MAGNITUDE_REQUEST)
    magnitude: int = sensor.transfer(lib.NOP_REQUEST) & lib.RESPONSE_MASK

    sensor.transfer(lib.DIAGNOSTIC_REQUEST)
    diagnostic: int = sensor.transfer(lib.NOP_REQUEST)
    #                               5432109876543210
    comp_high: int = diagnostic & 0b0000100000000000
    comp_low: int  = diagnostic & 0b0000010000000000
    cof: int       = diagnostic & 0b0000001000000000
    ocf: int       = diagnostic & 0b0000000100000000
    agc: int       = diagnostic & 0b0000000011111111

    lib.log(angle, magnitude, comp_high, comp_low, cof, ocf, agc)


def main() -> None:
    """Do everything."""
    args = parse()
    spi = make_spi(args)

    spi.open(0, 0)
    #spi.max_speed_hz = 1000000
    spi.max_speed_hz = 4000
    spi.mode = 1
    # 5hz full speed
    # nyquist would be 10hz sample rate
    # let's leave it at 50hz for now
    # maybe reduce it later
    #sample_period_ns = 2e7 # 0.02s
    sample_period_ns = 5e6 # 0.005s
    # 5hz full speed
    # 50hz sample rate
    # = 10 samples per revolution
    # so make threshold double that
    zero_crossing_threshold = 7168

    sensor = lib.Sensor(spi)

    cumulative_turns = 0
    previous_angle = 0

    while True:
        try:
            if args.verbose:
                verbose(sensor)
                continue

            now_ns = time.time_ns()
            waiting_ns = int(sample_period_ns - (now_ns % sample_period_ns))
            time.sleep(waiting_ns / 1e9)
            now_ns = time.time_ns()

            angle = sensor.transfer(lib.ANGLE_READ_REQUEST) & lib.RESPONSE_MASK

            if angle == 0:
                print("skipping zero result")
                continue

            dt_now = datetime.utcfromtimestamp(now_ns // 1e9)
            dts = dt_now.isoformat() + '.' + str(int(now_ns % 1e9)).zfill(9)

            if previous_angle == 0:
                previous_angle = angle
            d_angle = angle - previous_angle

            if d_angle > zero_crossing_threshold:
                cumulative_turns += 1

            if d_angle < (-1 * zero_crossing_threshold):
                cumulative_turns -= 1

            print(f"{dts} {angle:5} {cumulative_turns:5}")

            previous_angle = angle

        except lib.ResponseLengthException as err:
            print(f"Response Length Exception {err}")
        except lib.ResponseParityException as err:
            print(f"Response Parity Exception {err}")
        except lib.ResponseErrorRegisterException as err:
            print(f"Response Error Register {err}")


if __name__ == "__main__":
    main()
