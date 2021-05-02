"""Implements details of the sensor SPI interface."""
import logging
from typing import Any, List
from datetime import datetime
import lib

# AMS AS5048A encoder
#
# from datasheet
# https://ams.com/documents/20143/36005/AS5048_DS000298_4-00.pdf
#
# (all even parity below)
#
# request bits: 15=parity, 14=read(1) or write(0), 13:0=address
# read response bits: 15=parity, 14=error, 13:0=data
# write request bits: 15=parity, 14=0, 13:0=data
#
# registers (hex):
# 0000: NOP
# 0001: read and clear error (0=framing, 1=invalid command, 2=parity)
# 0003: programming
# 0016: zero position
# 0017: zero position
# 3FFD: diagnostics, AGC
# 3FFE: read magnitude
# 3FFF: read angle
#
# diagnostics
# OCF = offset compensation finished, should be high
# COF = cordic overflow, high is bad
# COMP low = high field
# COMP high = low field

# note that nop is exactly 0x0000 even though it's a "read"

class Sensor:
    """Talks to the sensor."""
    def __init__(self, spi: Any) -> None:
        """Initalizes with supplied SpiDev."""
        self.spi = spi

    #                            PR<----addr---->
    #                            5432109876543210
    _NOP_REQUEST: int        = 0b0000000000000000
    _ERR_REQUEST: int        = 0b0100000000000001
    _DIAGNOSTIC_REQUEST: int = 0b0111111111111101
    _MAGNITUDE_REQUEST: int  = 0b0111111111111110
    _ANGLE_READ_REQUEST: int = 0b1111111111111111
    # read response comes in the subsequent message

    _RESPONSE_MASK: int      = 0b0011111111111111
    _ERR_MASK: int           = 0b0100000000000000

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
            logging.debug("parity error for response %s", "{0:016b}".format(res))
            raise Sensor.ResponseParityException()
        return res

    def read_angle(self) -> int:
        """Reads the magnet angle."""
        return self._transfer(Sensor._ANGLE_READ_REQUEST) & Sensor._RESPONSE_MASK

    def _transfer(self, req: int) -> int:
        """Makes SPI request, read and return response, check parity."""
        reqh: int = (req >> 8) & 0xff
        reql: int = req & 0xff

        # note spidev can only do 8 bits, which is why it's a list here
        # also note spidev *trims* each item to 8 bits :-)
        # is that really necessary?
        res_list: List[int] = self.spi.xfer2([reqh, reql])
        res = self._make_res(res_list)

        err: int = res & Sensor._ERR_MASK
        if err:
            logging.debug("err flag set for response %s", "{0:016b}".format(res))
            # ignore the response, try to clear the error, ignore the response
            res_list = self.spi.xfer2([((Sensor._ERR_REQUEST >> 8) & 0xff),
                                      Sensor._ERR_REQUEST & 0xff])
            res = self._make_res(res_list)
            logging.debug("ignoring response %s", "{0:016b}".format(res))

            res_list = self.spi.xfer2([((Sensor._NOP_REQUEST >> 8) & 0xff),
                                      Sensor._NOP_REQUEST & 0xff])
            res = self._make_res(res_list)
            if res & 0b0000000000000001 != 0:
                logging.error("framing error %s", "{0:016b}".format(res))
            if res & 0b0000000000000010 != 0:
                logging.error("command invalid %s", "{0:016b}".format(res))
            if res & 0b0000000000000100 != 0:
                logging.error("parity error %s", "{0:016b}".format(res))
            if res & 0b0000000000000111 == 0:
                logging.error("other error %s", "{0:016b}".format(res))

            raise Sensor.ResponseErrorRegisterException(f"error register {res}")

        return res

    def verbose(self) -> None:
        """Produces debugging output."""
        self._transfer(Sensor._ANGLE_READ_REQUEST)
        angle: int = self._transfer(Sensor._NOP_REQUEST) & Sensor._RESPONSE_MASK

        self._transfer(Sensor._MAGNITUDE_REQUEST)
        magnitude: int = self._transfer(Sensor._NOP_REQUEST) & Sensor._RESPONSE_MASK

        self._transfer(Sensor._DIAGNOSTIC_REQUEST)
        diagnostic: int = self._transfer(Sensor._NOP_REQUEST)
        #                               5432109876543210
        comp_high: int = diagnostic & 0b0000100000000000
        comp_low: int  = diagnostic & 0b0000010000000000
        cof: int       = diagnostic & 0b0000001000000000
        ocf: int       = diagnostic & 0b0000000100000000
        agc: int       = diagnostic & 0b0000000011111111

        now_s: str = datetime.now().isoformat(timespec='microseconds')
        logging.info("time: %s angle: %5d magnitude: %5d comp_high: %0d comp_low: %0d cof: %0d"
                     " ocf: %0d agc: %0d",
                     now_s, angle, magnitude, comp_high, comp_low, cof, ocf, agc)
