""" Computes delivered volume from meter readings."""
# pylint: disable=invalid-name
import math

class Volume:
    """Calculates volume delivered."""
    def __init__(self) -> None:
        self.previous_second: int = 0
        self.previous_cumulative_angle: int = 0
        self.cumulative_volume_ul: int = 0

    @staticmethod
    def _volume_ul_per_angle_per_sec(angle_per_sec: int) -> float:
        """Looks like a good fit to the data.

        https://docs.google.com/spreadsheets/d/1O37uR9_JQVNBmYMsrM4oETmit82RlsSE_1_1l7Ao1wo
        """
        x: int = max(800, abs(angle_per_sec))
        f: float = 1.995 + 7970 * pow(abs(x), -1.503)
        return math.copysign(1, angle_per_sec) * f

    @staticmethod
    def _volume_ul(delta_cumulative_angle: int) -> int:
        """Calculates the volume delivered."""
        volume_ul_per_angle: float = Volume._volume_ul_per_angle_per_sec(delta_cumulative_angle)
        return int(delta_cumulative_angle * volume_ul_per_angle)

    def update(self, now_ns: int, cumulative_angle: int) -> None:
        """Updates cumulative volume from angle readings.

        Should be called more frequently than every second.
        """
        current_second: int = int(now_ns // 1000000000)
        if current_second > self.previous_second:
            # just crossed the boundary
            self.previous_second = current_second

            delta_cumulative_angle:int = cumulative_angle - self.previous_cumulative_angle
            self.previous_cumulative_angle = cumulative_angle

            delta_volume_ul:int = Volume._volume_ul(delta_cumulative_angle)
            self.cumulative_volume_ul += delta_volume_ul

    def read(self) -> int:
        """Reads the cumulative state"""
        return self.cumulative_volume_ul
