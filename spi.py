"""Decode and log angular data from AMS AS5048A."""
import spidev # type: ignore
import lib

def main() -> None:
    """Do everything."""
    spi = spidev.SpiDev()
    spi.open(0, 0) # bus,device
    #spi.open(0, 1) # bus,device

    # AS5048 min clk period = 100ns (10Mhz)
    # raspberry pi minimum is 4khz
    # 60 foot cable means slower is better :-)
    # but it seems like 1Mhz works through the cable
    # but use the minimum anyway.
    # TODO: what's the rotational speed of the meter?
    #spi.max_speed_hz = 4000
    spi.max_speed_hz = 1000000

    # between commands, CS is high, clock is low
    # CS is active low
    # looks like datasheet says the input is valid on
    # falling clock edge, and output is valid on rising edge:
    # "The AS5048A then reads the digital value on the MOSI (master out
    # slave in) input with every falling edge of CLK and writes on its
    # MISO (master in slave out) output with the rising edge."
    # which is mode "1"

    spi.mode = 1
    # this doesn't work
    # spi.bits_per_word = 16
    # this doesn't work
    # https://www.raspberrypi.org/forums/viewtopic.php?t=284134
    # == the usual python nightmare
    # spi.cshigh = False

    sensor = lib.Sensor(spi)

    sensor.transfer_and_log("nop", lib.NOP_REQUEST)
    sensor.transfer_and_log("nop", lib.NOP_REQUEST)

    #sensor.transfer_and_log("random1", 1234)
    #sensor.transfer_and_log("random2", 5678)

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
    #                                                     5432109876543210
    try_angle: int = sensor.transfer(lib.NOP_REQUEST) & 0b0011111111111111
    print(f"try_angle: {try_angle}")

    while True:
        try:
            sensor.transfer(lib.ANGLE_READ_REQUEST)
            #                                                 5432109876543210
            angle: int = sensor.transfer(lib.NOP_REQUEST) & 0b0011111111111111

            sensor.transfer(lib.MAGNITUDE_REQUEST)
            #                                                     5432109876543210
            magnitude: int = sensor.transfer(lib.NOP_REQUEST) & 0b0011111111111111

            sensor.transfer(lib.DIAGNOSTIC_REQUEST)
            diagnostic: int = sensor.transfer(lib.NOP_REQUEST)
            #                               5432109876543210
            comp_high: int = diagnostic & 0b0000100000000000
            comp_low: int  = diagnostic & 0b0000010000000000
            cof: int       = diagnostic & 0b0000001000000000
            ocf: int       = diagnostic & 0b0000000100000000

            lib.log(angle, magnitude, comp_high, comp_low, cof, ocf)
        except lib.ResponseLengthException as err:
            print(err)


if __name__ == "__main__":
    main()
