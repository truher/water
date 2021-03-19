"""Decode and log angular data from AMS AS5048A."""
import spidev # type: ignore
import lib

def main() -> None:
    """Do everything."""
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1000000
    spi.mode = 1

    sensor = lib.Sensor(spi)

    while True:
        try:
            lib.log_angle(sensor.transfer(lib.ANGLE_READ_REQUEST) & 0b0011111111111111)
        except lib.ResponseLengthException as err:
            print(err)
        except lib.ResponseParityException as err:
            print(err)
        except lib.ResponseErrorRegisterException as err:
            print(err)


if __name__ == "__main__":
    main()
