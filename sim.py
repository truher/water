"""Simulated spi interface"""
from math import log
from random import random
from typing import List
import lib

# negative angle is positive flow
# i think 4000 is about full speed? TODO: find out
INCREMENT = -4000

#pylint: disable=too-few-public-methods
class SimulatorSpiDev:
    """simulated sensor"""
    def __init__(self) -> None:
        self.angle: int = 0

    @staticmethod
    def _noise() -> int:
        """based on eyeballing the error distribution, it's logistic"""
        p_val: float = random()
        return int(11 * log(p_val / (1 - p_val)))

    #pylint: disable=unused-argument, missing-function-docstring
    def xfer2(self, req: List[int]) -> List[int]:
        if len(req) != 2:
            return [0, 0]
        if req[0] == 0xff and req[1] == 0xff:
            self.angle += INCREMENT  # TODO: make this about time instead, make it adjustable
            if self.angle > 16383:
                self.angle -= 16384
            if self.angle < 0:
                self.angle += 16384

            noise: int = self._noise()
            observation: int = self.angle + noise
            if observation > 16383:
                observation -= 16384
            elif observation < 0:
                observation += 16384

            parity: int = lib.has_even_parity(observation)
            return [((not parity) << 7) | (observation >> 8) & 0xff, observation & 0xff]

        return [0, 0] # this should produce an error

    def open(self, bus: int, device: int) -> None:
        pass
