"""Write data files"""
# pylint: disable=too-few-public-methods
from datetime import datetime

class DataWriter:
    """write a line every so often"""
    def __init__(self, filename: str, write_mod_sec: int, trunc_mod_sec: int) -> None:
        self.filename = filename
        self.write_mod_sec = write_mod_sec
        self.trunc_mod_sec = trunc_mod_sec
        self.sink = open(filename, 'ab')
        self.cumulative_angle = 0
        self.cumulative_volume_ul = 0
        self.current_second: int = 0

    def write(self, now_ns: int, cumulative_angle: int, cumulative_volume_ul:int) -> None:
        """write the delta corresponding to the mod"""
        now_s = int(now_ns // 1000000000)
        if now_s <= self.current_second:
            return
        self.current_second = now_s

        if self.trunc_mod_sec != 0 and now_s % self.trunc_mod_sec == 0:
            self.sink.close()
            with open(self.filename, 'w') as trunc_sink:
                trunc_sink.truncate()
            self.sink = open(self.filename, 'ab')

        if now_s % self.write_mod_sec != 0:
            return

        dt_now: datetime = datetime.utcfromtimestamp(now_s)
        dts: str = dt_now.isoformat() + '.' + str(int(now_ns % 1000000000)).zfill(9)
        delta_cumulative_angle = cumulative_angle - self.cumulative_angle
        delta_volume_ul = cumulative_volume_ul - self.cumulative_volume_ul

        output_line = (f"{dts}\t{delta_cumulative_angle}\t{delta_volume_ul}")
        self.sink.write(output_line.encode('ascii'))
        self.sink.write(b'\n')
        self.sink.flush()
        self.cumulative_angle = cumulative_angle
        self.cumulative_volume_ul = cumulative_volume_ul
