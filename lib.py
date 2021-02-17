"""Library for water logging."""
from typing import Any, List

# AMS AS5048A encoder

# from datasheet
# https://ams.com/documents/20143/36005/AS5048_DS000298_4-00.pdf

# (all even parity below)

# request bits: 15=parity, 14=read(1) or write(0), 13:0=address
# read response bits: 15=parity, 14=error, 13:0=data
# write request bits: 15=parity, 14=0, 13:0=data

# registers (hex):
# 0000: NOP
# 0001: clear error (0=framing, 1=invalid command, 2=parity)
# 0003: programming
# 0016: zero position
# 0017: zero position
# 3FFD: diagnostics, AGC
# 3FFE: magnitude
# 3FFF: angle

# diagnostics
# OCF = offset compensation finished, should be high
# COF = cordic overflow, high is bad
# COMP low = high field
# COMP high = low field

# note that nop is exactly 0x0000 even though it's a "read"

# even parity == make the number of 1's even
#                           PR<----addr---->
#                           5432109876543210
NOP_REQUEST: int        = 0b0000000000000000
ERR_REQUEST: int        = 0b0100000000000001
DIAGNOSTIC_REQUEST: int = 0b0111111111111101
MAGNITUDE_REQUEST: int  = 0b0111111111111110
ANGLE_READ_REQUEST: int = 0b1111111111111111
# read response comes in the subsequent message


def has_even_parity(message: int) -> bool:
    """ Return true if message has even parity."""
    parity_is_even: bool = True
    while message:
        parity_is_even = not parity_is_even
        message = message & (message - 1)
    return parity_is_even

def log(angle: int, magnitude: int, comp_high: int, comp_low: int,
        cof: int, ocf: int) -> None:
    """Log an observation."""
    #pylint: disable=unused-argument
    #pylint: disable=too-many-arguments
    print(f"angle: {angle:5} magnitude: {magnitude:5} "
           "{comp_high>0:d} {comp_low>0:d} {cof>0:d} {ocf>0:d}")

class ResponseLengthException(Exception):
    pass

class ResponseParityException(Exception):
    pass

class Sensor:
    """Wrapper for talking to the sensor."""
    def __init__(self, spi: Any) -> None:
        """Init with supplied SpiDev."""
        self.spi = spi

    def transfer(self, req: int) -> int:
        """SPI transfer request, read and return response, check parity."""
        reqh: int = (req >> 8) & 0xff
        reql: int = req & 0xff

        res_list: List[int] = self.spi.xfer2([reqh, reql])
        if len(res_list) != 2:
            raise ResponseLengthException(f"response length {len(res_list)}")

        res: int = ((res_list[0] & 0xff) << 8) + (res_list[1] & 0xff)
        if not has_even_parity(res):
            raise ResponseParityException()

        err: int = res & 0b0100000000000000
        if err:
            print ("err flag set!")
            # try to clear it
            # TODO: some sort of exception?
            self.spi.xfer2([((ERR_REQUEST >> 8) & 0xff),
                             ERR_REQUEST & 0xff])
        return res

    def transfer_and_log(self, name: str, req: int) -> int:
        """Transmit request, read and return response, also log both."""
        res: int = self.transfer(req)
        print()
        print(name)
        print("5432109876543210    5432109876543210")
        print(f"{req:016b} => {res:016b}")
        return res
