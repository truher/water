"""
Derive delivered volume from meter readings

This is not the way it will work, but it's a place to start.
"""

class Volume:
    """Calculate volume delivered."""
    def __init__(self) -> None:
        self.previous_second: int = 0
        self.previous_cumulative_angle: int = 0
        self.cumulative_volume_ul: int = 0

    #delivered volume is positive for negative angle increments
    _CONSTANT_UL_PER_ANGLE = -0.0002

    @staticmethod
    def _volume_ul(delta_cumulative_angle: int) -> int:
        """return microliters for a given rotation"""
        return int(delta_cumulative_angle * Volume._CONSTANT_UL_PER_ANGLE)

    def update(self, now_ns: int, cumulative_angle: int) -> None:
        """derive volume periodically"""
        current_second: int = int(now_ns // 1000000000)
        if current_second > self.previous_second:
            # just crossed the boundary
            self.previous_second = current_second

            delta_cumulative_angle:int = cumulative_angle - self.previous_cumulative_angle
            self.previous_cumulative_angle = cumulative_angle

            delta_volume_ul:int = Volume._volume_ul(delta_cumulative_angle)
            self.cumulative_volume_ul += delta_volume_ul

    def read(self) -> int:
        """read the cumulative state"""
        return self.cumulative_volume_ul
