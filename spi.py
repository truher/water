"""Decode and log angular data from AMS AS5048A."""
import spidev # type: ignore
import lib
import time

def main() -> None:
    """Do everything."""
    spi = spidev.SpiDev()
    spi.open(0, 0)
    #spi.max_speed_hz = 1000000
    spi.max_speed_hz = 4000
    spi.mode = 1
    sample_delay_sec = 0.0075

    sensor = lib.Sensor(spi)

    while True:
        try:
            time.sleep(sample_delay_sec)
            angle = sensor.transfer(lib.ANGLE_READ_REQUEST) & 0b0011111111111111
            if angle > 0:
                lib.log_angle(angle)
        except lib.ResponseLengthException as err:
            print(err)
        except lib.ResponseParityException as err:
            print(err)
        except lib.ResponseErrorRegisterException as err:
            print(err)


if __name__ == "__main__":
    main()
