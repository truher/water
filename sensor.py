"""Details of the sensor SPI interface."""
from typing import Any, List
from datetime import datetime
import lib

# AMS AS5048A encoder

# from datasheet
# https://ams.com/documents/20143/36005/AS5048_DS000298_4-00.pdf

# (all even parity below)

# request bits: 15=parity, 14=read(1) or write(0), 13:0=address
# read response bits: 15=parity, 14=error, 13:0=data
# write request bits: 15=parity, 14=0, 13:0=data

# registers (hex):
# 0000: NOP
# 0001: read and clear error (0=framing, 1=invalid command, 2=parity)
# 0003: programming
# 0016: zero position
# 0017: zero position
# 3FFD: diagnostics, AGC
# 3FFE: read magnitude
# 3FFF: read angle

# diagnostics
# OCF = offset compensation finished, should be high
# COF = cordic overflow, high is bad
# COMP low = high field
# COMP high = low field

# note that nop is exactly 0x0000 even though it's a "read"

class Sensor:
    """Wrapper for talking to the sensor."""
    def __init__(self, spi: Any) -> None:
        """Init with supplied SpiDev."""
        self.spi = spi

    #                           PR<----addr---->
    #                           5432109876543210
    NOP_REQUEST: int        = 0b0000000000000000
    ERR_REQUEST: int        = 0b0100000000000001
    DIAGNOSTIC_REQUEST: int = 0b0111111111111101
    MAGNITUDE_REQUEST: int  = 0b0111111111111110
    ANGLE_READ_REQUEST: int = 0b1111111111111111
    # read response comes in the subsequent message

    RESPONSE_MASK: int      = 0b0011111111111111
    ERR_MASK: int           = 0b0100000000000000

    class ResponseLengthException(Exception):
        """The response is not of length two"""

    class ResponseParityException(Exception):
        """The response parity is not even"""

    class ResponseErrorRegisterException(Exception):
        """The slave passes an error code"""

    @staticmethod
    def _make_res(res_list: List[int]) -> int:
        if len(res_list) != 2:
            raise Sensor.ResponseLengthException(f"response length {len(res_list)}")
        res: int = ((res_list[0] & 0xff) << 8) + (res_list[1] & 0xff)
        if not lib.has_even_parity(res):
            raise Sensor.ResponseParityException()
        return res

    def transfer(self, req: int) -> int:
        """SPI transfer request, read and return response, check parity."""
        reqh: int = (req >> 8) & 0xff
        reql: int = req & 0xff

        # note spidev can only do 8 bits, which is why it's a list here
        # also note spidev *trims* each item to 8 bits :-)
        # is that really necessary?
        res_list: List[int] = self.spi.xfer2([reqh, reql])
        res = self._make_res(res_list)

        err: int = res & Sensor.ERR_MASK
        if err:
            print ("err flag set!")
            # ignore the response, try to clear the error, ignore the response
            self.spi.xfer2([((Sensor.ERR_REQUEST >> 8) & 0xff),
                           Sensor.ERR_REQUEST & 0xff])
            res_list = self.spi.xfer2([((Sensor.NOP_REQUEST >> 8) & 0xff),
                                      Sensor.NOP_REQUEST & 0xff])
            res = self._make_res(res_list)
            raise Sensor.ResponseErrorRegisterException(f"error register {res}")

        return res

    def verbose(self) -> None:
        """debugging output"""
        self.transfer(Sensor.ANGLE_READ_REQUEST)
        angle: int = self.transfer(Sensor.NOP_REQUEST) & Sensor.RESPONSE_MASK

        self.transfer(Sensor.MAGNITUDE_REQUEST)
        magnitude: int = self.transfer(Sensor.NOP_REQUEST) & Sensor.RESPONSE_MASK

        self.transfer(Sensor.DIAGNOSTIC_REQUEST)
        diagnostic: int = self.transfer(Sensor.NOP_REQUEST)
        #                               5432109876543210
        comp_high: int = diagnostic & 0b0000100000000000
        comp_low: int  = diagnostic & 0b0000010000000000
        cof: int       = diagnostic & 0b0000001000000000
        ocf: int       = diagnostic & 0b0000000100000000
        agc: int       = diagnostic & 0b0000000011111111

        now_s: str = datetime.now().isoformat(timespec='microseconds')
        print(f"time: {now_s} angle: {angle:5} magnitude: {magnitude:5} "
              f"comp_high: {comp_high>0:d} comp_low: {comp_low>0:d} "
              f"cof: {cof>0:d} ocf: {ocf>0:d} agc: {agc>0:d}")
