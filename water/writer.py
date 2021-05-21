"""Writes and reads data files."""
# pylint: disable=too-few-public-methods
import logging
from collections import deque
from datetime import datetime
from typing import Deque

class DataWriter:
    """Writes a line every so often."""
    def __init__(self, path: str, write_mod_sec: int, trunc_mod_sec: int) -> None:
        self.path = path
        self.write_mod_sec = write_mod_sec
        self.trunc_mod_sec = trunc_mod_sec
        self.sink = open(self.path, 'ab')
        self.cumulative_angle = 0
        self.cumulative_volume_ul = 0
        self.current_second: int = 0

    def _trim(self, now_s: int) -> None:
        if self.trunc_mod_sec != 0 and now_s % self.trunc_mod_sec == 0:
            logging.debug("trim: %s %s %s", self.trunc_mod_sec, now_s, now_s % self.trunc_mod_sec)
            self.sink.close()
            whole_file: Deque[bytes] = deque(open(self.path, 'rb'), maxlen=self.trunc_mod_sec)
            self.sink = open(self.path, 'wb')
            self.sink.writelines(whole_file)
            self.sink.flush()

    def write(self, now_ns: int, cumulative_angle: int, cumulative_volume_ul:int) -> None:
        """Writes the delta corresponding to the mod"""
        now_s = int(now_ns // 1000000000)
        if self.current_second == 0:
            self.current_second = now_s
            self.cumulative_angle = cumulative_angle
            self.cumulative_volume_ul = cumulative_volume_ul
            return

        if now_s <= self.current_second:
            return
        self.current_second = now_s

        self._trim(now_s)

        if now_s % self.write_mod_sec != 0:
            return

        dt_now: datetime = datetime.utcfromtimestamp(now_s)
        dts: str = (dt_now.strftime('%Y-%m-%dT%H:%M:%S') + '.'
                    + str(int(now_ns % 1000000000)).zfill(9))
        delta_cumulative_angle = cumulative_angle - self.cumulative_angle
        delta_volume_ul = cumulative_volume_ul - self.cumulative_volume_ul

        output_line = (f"{dts}\t{delta_cumulative_angle}\t{delta_volume_ul}")
        self.sink.write(output_line.encode('ascii'))
        self.sink.write(b'\n')
        self.sink.flush()
        self.cumulative_angle = cumulative_angle
        self.cumulative_volume_ul = cumulative_volume_ul
