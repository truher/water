"""Maintains the state of the meter."""
# pylint: disable=fixme
import logging

class Meter:
    """Keeps the angular state of the meter."""
    def __init__(self) -> None:
        self.turns: int = 0
        self.angle: int = 0

    _ZERO_CROSSING_THRESHOLD: int = 8192

    def update(self, angle: int) -> None:
        """Handles an angle observation.

        Call frequently to avoid aliasing
        """
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
        """Reads the cumulative angle."""
        return self.turns * 16384 + self.angle
