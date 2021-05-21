"""Writes and reads data files."""
# pylint: disable=too-few-public-methods
import logging
import os
from collections import deque
from datetime import datetime
from typing import Any, Deque, List
import pandas as pd #type:ignore
from search.search import RangeSearch

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
            logging.debug("trim: %s %s %s", self.trunc_mod_sec, now_s, now_s % self.trunc_mod_sec)
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

        output_line = (f"{dts}\t{delta_cumulative_angle}\t{delta_volume_ul}")
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
        logging.debug('skiprows %d', skiprows)
        data_frame = pd.read_csv(self._path(), delim_whitespace=True, index_col=0, parse_dates=True,
                                 header=None, names=['time', 'angle', 'volume_ul'],
                                 skiprows=skiprows)
        logging.debug('data_frame rows %d', len(data_frame.index))
        return data_frame

    def read_range(self, start: str, end: str, buckets: int) -> Any:
        """Reads a range of rows based on the specified range"""
        logging.debug('read_range start: %s end: %s buckets: %d', start, end, buckets)
        start_ts = pd.to_datetime(start)
        end_ts = pd.to_datetime(end)
        if start_ts > end_ts:
            return pd.DataFrame()
        delta = end_ts - start_ts
        delta_s = delta.total_seconds()
        freq_s = max(delta_s // buckets, 1) # prohibit upsampling
        resample_freq = str(int(freq_s)) + "S"
        logging.debug("delta_s: %d freq_s: %d", delta_s, freq_s)
        if freq_s > 60:
            logging.debug("should use minute data here")
        with open(self._path()) as file:
            with RangeSearch(file) as rng:
                rows: List[List[str]] = rng.search(start, end)
                logging.debug('len(rows) %d', len(rows))
                if len(rows) == 0:
                    return pd.DataFrame(columns=['time','angle','volume_ul'])
                data_frame = pd.DataFrame(rows, columns=['time','angle','volume_ul'])
                data_frame['time'] = pd.to_datetime(data_frame['time'])
                data_frame['angle'] = data_frame['angle'].astype(int)
                data_frame['volume_ul'] = data_frame['volume_ul'].astype(int)
                data_frame = data_frame.set_index('time')
                #logging.info(data_frame)
                logging.debug("resample %s", resample_freq)
                # divide by the bucket width, freq_s to maintain units per second, like peter scott said.
                # TODO: make this units per minute instead
                # TODO: there's some weird aliasing here.
                data_frame = data_frame.resample(resample_freq).sum() / freq_s
                #logging.info(data_frame)
                return data_frame
