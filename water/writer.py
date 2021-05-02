"""Writes and reads data files."""
# pylint: disable=too-few-public-methods
import logging
import os
from collections import deque
from datetime import datetime
from typing import Any, Deque
import pandas as pd #type:ignore

UL_PER_GALLON = 3785411.784

class DataWriter:
    """Writes a line every so often."""
    def __init__(self, filename: str, write_mod_sec: int, trunc_mod_sec: int) -> None:
        self.filename = filename
        self.write_mod_sec = write_mod_sec
        self.trunc_mod_sec = trunc_mod_sec
        os.makedirs('data', exist_ok=True)
        self.sink = open(self._path(), 'ab')
        self.cumulative_angle = 0
        self.cumulative_volume_ul = 0
        self.current_second: int = 0

    def _path(self) -> str:
        return 'data/' + self.filename

    def _trim(self, now_s: int) -> None:
        if self.trunc_mod_sec != 0 and now_s % self.trunc_mod_sec == 0:
            logging.info("trim: %s %s %s", self.trunc_mod_sec, now_s, now_s % self.trunc_mod_sec)
            self.sink.close()
            whole_file: Deque[bytes] = deque(open(self._path(), 'rb'), maxlen=self.trunc_mod_sec)
            self.sink = open(self._path(), 'wb')
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
        delta_volume_gal = delta_volume_ul / UL_PER_GALLON

        output_line = (f"{dts}\t{delta_cumulative_angle}\t{delta_volume_ul}\t{delta_volume_gal}")
        self.sink.write(output_line.encode('ascii'))
        self.sink.write(b'\n')
        self.sink.flush()
        self.cumulative_angle = cumulative_angle
        self.cumulative_volume_ul = cumulative_volume_ul

    def read(self, rows: int) -> Any:
        """Reads the last N rows from the file as a dataframe.

        Zero rows means all rows.
        """
        skiprows: int = 0 if rows == 0 else max(0, sum(1 for l in open(self._path())) - rows)
        return pd.read_csv(self._path(), delim_whitespace=True, index_col=0, parse_dates=True,
                           header=None, names=['time', 'angle', 'volume_ul', 'volume_gal'],
                           skiprows=skiprows)
