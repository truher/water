"""Reads data from files."""
# pylint: disable=too-few-public-methods, fixme, missing-function-docstring
import logging
from typing import Any, List
import pandas as pd #type:ignore
from search.search import RangeSearch

class DataReader:
    """Read from one of the data files, depending on bucket size."""

    PATH_MIN = "data/data_min"
    PATH_SEC = "data/data_sec"

    def read_range(self, start: str, end: str, buckets: int) -> Any:
        """Reads a range of rows based on the specified range"""
        logging.info('read_range start: %s end: %s buckets: %d', start, end, buckets)
        start_ts = pd.to_datetime(start)
        end_ts = pd.to_datetime(end)
        if start_ts > end_ts:
            return pd.DataFrame()
        delta = end_ts - start_ts
        delta_s = delta.total_seconds()
        freq_s = max(delta_s // buckets, 1) # prohibit upsampling
        resample_freq = str(int(freq_s)) + "S"
        logging.info("delta_s: %d freq_s: %d", delta_s, freq_s)
        if freq_s > 60:
            # TODO: select sec or min depending on range and grain
            logging.debug("should use minute data here")
        with open(self.PATH_SEC) as file:
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
                # divide by the bucket width, freq_s to maintain units per second.
                # TODO: make this units per minute instead
                # TODO: there's some weird aliasing here.

                data_frame = data_frame.resample(resample_freq).sum() / freq_s
                #logging.info(data_frame)
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
