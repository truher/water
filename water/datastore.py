"""Reads data from files."""
# pylint: disable=too-few-public-methods
import logging
from typing import Any, List
import pandas as pd #type:ignore
from search.search import RangeSearch

class DataStore:
    """Read from one of the data files, depending on bucket size."""
    def __init__(self, minfile: str, secfile: str) -> None:
        self.minfile = minfile
        self.secfile = secfile

    @staticmethod
    def _path(filename) -> str:
        return 'data/' + filename

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
            logging.debug("should use minute data here")
        with open(DataStore._path(self.secfile)) as file:
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
