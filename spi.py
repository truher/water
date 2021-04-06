"""Decode and log angular data from AMS AS5048A."""
import spidev # type: ignore
import lib
import time
from datetime import datetime

def main() -> None:
    """Do everything."""
    spi = spidev.SpiDev()
    spi.open(0, 0)
    #spi.max_speed_hz = 1000000
    spi.max_speed_hz = 4000
    spi.mode = 1
    sample_period_ns = 5e8 # 0.5s
    sample_delay_ns = 0

    sensor = lib.Sensor(spi)

    while True:
        try:
            now_ns = time.time_ns()
            waiting_ns = int(sample_period_ns
                             - (now_ns % sample_period_ns)
                             - sample_delay_ns)
            time.sleep(waiting_ns / 1e9)
            now_ns = time.time_ns()

            angle = sensor.transfer(lib.ANGLE_READ_REQUEST) & 0b0011111111111111
            if angle > 0:

                dt = datetime.utcfromtimestamp(now_ns // 1e9)
                dts = dt.isoformat(timespec='microseconds')

                print(f"{dts} {angle:5}")

        except lib.ResponseLengthException as err:
            print(err)
        except lib.ResponseParityException as err:
            print(err)
        except lib.ResponseErrorRegisterException as err:
            print(err)


if __name__ == "__main__":
    main()
