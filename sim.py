"""Simulated spi interface"""
from typing import List
import lib

#pylint: disable=too-few-public-methods
class SimulatorSpiDev:
    """simulated sensor"""
    def __init__(self) -> None:
        self.angle = 0
    #pylint: disable=unused-argument, missing-function-docstring
    def xfer2(self, req: List[int]) -> List[int]:
        self.angle += 1
        if self.angle > 16383:
            self.angle -= 16384
        parity = lib.has_even_parity(self.angle)
        return [((not parity) << 7) | (self.angle >> 8) & 0xff, self.angle & 0xff]
    def open(self, bus: int, device: int) -> None:
        pass
