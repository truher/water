"""libary for Meter behavior"""
# pylint: disable=fixme
import logging

class Meter:
    """Keep the angular state of the meter."""
    def __init__(self) -> None:
        self.turns: int = 0
        self.angle: int = 0

    # 5hz full speed
    # 50hz sample rate
    # = 10 samples per revolution
    # so make threshold double that
    _ZERO_CROSSING_THRESHOLD: int = 7168

    def update(self, angle: int) -> None:
        """handle an angle observation. call frequently to avoid aliasing"""
        if angle == 0:
            # TODO: zero is not *always* an error.  fix this.
            logging.error("skipping zero result")
            return
        if self.angle == 0:
            self.angle = angle
        d_angle: int = angle - self.angle
        self.angle = angle

        if d_angle < (-1 * Meter._ZERO_CROSSING_THRESHOLD):
            self.turns += 1
        if d_angle > Meter._ZERO_CROSSING_THRESHOLD:
            self.turns -= 1


    def read(self) -> int:
        """read the cumulative angle"""
        return self.turns * 16384 + self.angle
