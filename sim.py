"""Simulated spi interface"""
# pylint: disable=fixme
from datetime import datetime
from math import log
from random import random
from typing import List
import logging
import lib

# TODO: make this about time instead, make it adjustable
# 1200 is the max i could get with the hose, max rated, 30gpm, is about 4000
HIGH_INCREMENT = -1200
LOW_INCREMENT = 0

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
            logging.error("wrong length request")
            return [0, 0]

        if req[0] == 0xff and req[1] == 0xff:
            if datetime.now().minute % 2 == 0:
                self.angle += HIGH_INCREMENT
            else:
                self.angle += LOW_INCREMENT
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

        logging.error("weird request")
        return [0, 0] # this should produce an error

    def open(self, bus: int, device: int) -> None:
        pass
