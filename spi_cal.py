"""Calibration/debugging for AMS AS5048A."""
import spidev # type: ignore
import lib

def main() -> None:
    """Do everything."""
    spi = spidev.SpiDev()
    spi.open(0, 0)
    #spi.max_speed_hz = 1000000
    spi.max_speed_hz = 4000
    spi.mode = 1

    sensor = lib.Sensor(spi)

    sensor.transfer_and_log("nop", lib.NOP_REQUEST)
    sensor.transfer_and_log("nop", lib.NOP_REQUEST)

    sensor.transfer_and_log("err", lib.ERR_REQUEST)
    sensor.transfer_and_log("nop", lib.NOP_REQUEST)

    sensor.transfer_and_log("angle", lib.ANGLE_READ_REQUEST)
    sensor.transfer_and_log("nop", lib.NOP_REQUEST)

    sensor.transfer_and_log("magnitude", lib.MAGNITUDE_REQUEST)
    sensor.transfer_and_log("nop", lib.NOP_REQUEST)

    sensor.transfer_and_log("diagnostic", lib.DIAGNOSTIC_REQUEST)
    sensor.transfer_and_log("nop", lib.NOP_REQUEST)

    print("try decoding the angle")
    sensor.transfer(lib.ANGLE_READ_REQUEST)
    try_angle: int = sensor.transfer(lib.NOP_REQUEST) & 0b0011111111111111
    print(f"try_angle: {try_angle}")

    while True:
        try:
            sensor.transfer(lib.ANGLE_READ_REQUEST)
            angle: int = sensor.transfer(lib.NOP_REQUEST) & 0b0011111111111111

            sensor.transfer(lib.MAGNITUDE_REQUEST)
            magnitude: int = sensor.transfer(lib.NOP_REQUEST) & 0b0011111111111111

            sensor.transfer(lib.DIAGNOSTIC_REQUEST)
            diagnostic: int = sensor.transfer(lib.NOP_REQUEST)
            #                               5432109876543210
            comp_high: int = diagnostic & 0b0000100000000000
            comp_low: int  = diagnostic & 0b0000010000000000
            cof: int       = diagnostic & 0b0000001000000000
            ocf: int       = diagnostic & 0b0000000100000000
            agc: int       = diagnostic & 0b0000000011111111

            lib.log(angle, magnitude, comp_high, comp_low, cof, ocf, agc)
        except lib.ResponseLengthException as err:
            print(err)
        except lib.ResponseParityException as err:
            print(err)
        except lib.ResponseErrorRegisterException as err:
            print(err)



if __name__ == "__main__":
    main()
