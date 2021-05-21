"""Reads data from files."""
# pylint: disable=too-few-public-methods, fixme, missing-function-docstring
import logging
import time
from typing import Any, List, Tuple
import pandas as pd #type:ignore
from search.search import RangeSearch

class DataReader:
    """Read from one of the data files, depending on bucket size."""

    PATH_MIN = "data/data_min"
    PATH_SEC = "data/data_sec"
    COLUMNS = ['time','angle','volume_ul']

    @staticmethod
    def _freq_s(start: str, end: str, buckets: int) -> int:
        start_ts = pd.to_datetime(start)
        end_ts = pd.to_datetime(end)
        delta = end_ts - start_ts
        delta_s = delta.total_seconds()
        freq_s = max(delta_s // buckets, 1) # prohibit upsampling
        logging.info("delta_s: %d freq_s: %d", delta_s, freq_s)
        return freq_s

    def _source(self, freq_s: int) -> Tuple[str, str]:
        if freq_s < 60:
            return self.PATH_SEC, str(int(freq_s)) + "S"
        return self.PATH_MIN, str(int(freq_s//60)) + "T"

    def _data_frame(self, rows: List[List[str]]) -> Any:
        if len(rows) == 0:
            return pd.DataFrame(columns=self.COLUMNS)
        data_frame = pd.DataFrame(rows, columns=self.COLUMNS)
        data_frame['time'] = pd.to_datetime(data_frame['time'])
        data_frame['angle'] = data_frame['angle'].astype(int)
        data_frame['volume_ul'] = data_frame['volume_ul'].astype(int)
        data_frame = data_frame.set_index('time')
        return data_frame

    def read_range(self, start: str, end: str, buckets: int) -> Any:
        """Reads a range of rows based on the specified range"""
        logging.info('read_range start: %s end: %s buckets: %d', start, end, buckets)
        if start > end:
            return pd.DataFrame()

        freq_s = DataReader._freq_s(start, end, buckets)

        (path, resample_freq) = self._source(freq_s)
        logging.info("path: %s resample_freq: %s", path, resample_freq)

        start_ns = time.time_ns()
        with open(path) as file:
            with RangeSearch(file) as rng:
                mid1_ns = time.time_ns()
                logging.info("open microsec %d", (mid1_ns - start_ns) // 1000)

                rows: List[List[str]] = rng.search(start, end)

                mid2_ns = time.time_ns()
                logging.info("search microsec %d", (mid2_ns - mid1_ns) // 1000)

                data_frame = self._data_frame(rows)

                mid3_ns = time.time_ns()
                logging.info("dataframe microsec %d", (mid3_ns - mid2_ns) // 1000)

                # divide by the bucket width, freq_s * 60 to maintain units per minute
                data_frame = data_frame.resample(resample_freq).sum() / (60 * freq_s)

                end_ns = time.time_ns()
                logging.info("resample microsec %d", (end_ns - mid3_ns) // 1000)
                return data_frame

    # TODO: remove this
    @staticmethod
    def _read(path: str, rows: int) -> Any:
        """Reads the last N rows from the file as a dataframe.

        Zero rows means all rows.
        """
        skiprows: int = 0 if rows == 0 else max(0, sum(1 for l in open(path)) - rows)
        logging.debug('skiprows %d', skiprows)
        data_frame = pd.read_csv(path, delim_whitespace=True, index_col=0, parse_dates=True,
                                 header=None, names=['time', 'angle', 'volume_ul'],
                                 skiprows=skiprows)
        logging.debug('data_frame rows %d', len(data_frame.index))
        return data_frame

    # TODO: remove this
    def read_min(self, rows: int) -> Any:
        return DataReader._read(self.PATH_MIN, rows)

    # TODO: remove this
    def read_sec(self, rows: int) -> Any:
        return DataReader._read(self.PATH_SEC, rows)
