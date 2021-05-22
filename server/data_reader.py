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
    def _duration_s(start: str, end: str) -> int:
        start_ts = pd.to_datetime(start)
        end_ts = pd.to_datetime(end)
        delta = end_ts - start_ts
        return delta.total_seconds()

    def _source(self, start: str, end: str, buckets: int) -> Tuple[str, int, int, str]:
        """returns:

            the input file to use
            the input rows per output bucket (to scale the rate from the sum)
            the input rows per minute (for GPM scaling)
            the resampling frequency string
        """

        duration_s = DataReader._duration_s(start, end)
        bucket_width_s = duration_s / buckets
        if bucket_width_s < 1:
            # bucket is finer than the finest available file, just use what's available
            return self.PATH_SEC, 1, 60, "1S"

        if bucket_width_s < 60:
            actual_bucket_width_s = int(bucket_width_s)
            return self.PATH_SEC, actual_bucket_width_s, 60, str(actual_bucket_width_s) + "S"

        # bucket is at least minute grain, so use that
        bucket_width_min = int(bucket_width_s / 60)
        return self.PATH_MIN, bucket_width_min, 1, str(bucket_width_min) + "T"

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
        if start > end or buckets <= 0:
            return pd.DataFrame()

        (path, rows_per_bucket, rows_per_minute, resample_freq) = self._source(start, end, buckets)
        logging.info("path: %s rows_per_bucket: %d resample_freq: %s", path, rows_per_bucket, resample_freq)

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

                data_frame = rows_per_minute * data_frame.resample(resample_freq).sum() / rows_per_bucket

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
