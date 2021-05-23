"""efficiently select only part of a file"""
import logging
from typing import Any, List, IO

SEP = "\t"
class RangeSearch2:
    """select a range of rows"""

    def __init__(self, text_io: IO[str]) -> None:
        self.text_io = text_io
        self.length = 0

    def __enter__(self) -> Any:
        self.text_io.seek(0, 2)
        self.length = self.text_io.tell()
        logging.debug('length %d', self.length)

        return self

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None: # pylint: disable=W0622
        pass

# THE OLD ONE
    def search(self, query_low: str, query_high: str) -> List[List[str]]:
        """return rows between low and high queries, inclusive"""
        if query_high < query_low:
            logging.debug('high must be higher than low')
            return []
        lower_bound = self._lower_bound(query=query_low, offset_l=0, offset_h=self.length)
        return self._scan(lower_bound, query_high)

# search for the upper bound instead of scanning, to avoid all that splitting and comparing
    def search2(self, query_low: str, query_high: str) -> List[List[str]]:
        """return rows between low and high queries, inclusive"""
        if query_high < query_low:
            logging.debug('high must be higher than low')
            return []
        lower_bound = self._lower_bound(query=query_low, offset_l=0, offset_h=self.length)
        upper_bound = self._upper_bound(query=query_high, offset_l=lower_bound, offset_h=self.length)
        return self._scan_offset(lower_bound, upper_bound)

# just pass back the offsets
    def search3(self, query_low, query_high):
        lower_bound = self._lower_bound(query=query_low, offset_l=0, offset_h=self.length)
        upper_bound = self._upper_bound(query=query_high, offset_l=lower_bound, offset_h=self.length)
        return (lower_bound, upper_bound)
        

    def _scan_offset(self, lower, upper):
        logging.debug('scan offset %d %d', lower, upper)
        self.text_io.seek(lower)
        result = []
        for l in self.text_io.readlines(upper-lower-1):
            result.append(l.strip().split(SEP))
        return result

    def _scan(self, offset: int, query_high: str) -> List[List[str]]:
        """return rows from offset to query_high, inclusive"""
        logging.debug('scan %d %s', offset, query_high)
        self.text_io.seek(offset)
        whole_line = self.text_io.readline()
        logging.debug('whole line %s', whole_line)
        if len(whole_line) == 0:
            logging.debug('zero length line')
            return []
        line = whole_line.strip().split(SEP)
        result = []
        counter = 0
        while line[0] <= query_high:
            result.append(line)
            counter += 1
            whole_line = self.text_io.readline()
            line = whole_line.strip().split(SEP)
            if line == ['']:  # happens only at the last line.
                logging.debug('empty last line')
                break
        logging.debug("row count %d", counter)
        return result

#    def _id_from_line(self, offset: int) -> str:
#        self.text_io.seek(offset)
#        return self.text_io.readline().split(SEP, 1)[0]

# no need to split, just compare the whole thing
    def _get_line(self, offset: int) -> str:
        self.text_io.seek(offset)
        return self.text_io.readline()

    def _seek_to_next_line(self, offset: int) -> int:
        """return offset of next line after offset"""
        self.text_io.seek(offset)
        self.text_io.readline()
        return self.text_io.tell()

    def _seek_back_to_line_start(self, offset: int) -> int:
        """return offset of beginning of the line offset is within"""
        line_start = offset
        while line_start >= 0:
            self.text_io.seek(line_start)
            if self.text_io.read(1) == '\n':
                if line_start <= self.length:
                    line_start += 1
                break
            line_start -= 1
        if line_start < 0:
            line_start = 0
            self.text_io.seek(line_start)
        return line_start

    def _lower_bound(self, query: str, offset_l: int, offset_h: int) -> int:
        """return offset of first row within bounds not less than query"""
        logging.debug('lower bound 2 %s %s %s', query, offset_l, offset_h)
        if offset_l >= offset_h:
            return self._seek_back_to_line_start(offset_l)

        mid = (offset_l + offset_h) // 2

        line_start = self._seek_back_to_line_start(mid)
        #current_id = self._id_from_line(line_start)
        current_line = self._get_line(line_start)
        next_line_start = self._seek_to_next_line(mid)

        #if current_id >= query:
        if current_line >= query:
            return self._lower_bound(query=query, offset_l=offset_l, offset_h=line_start - 1)
        return self._lower_bound(query=query, offset_l=next_line_start, offset_h=offset_h)

    def _upper_bound(self, query: str, offset_l: int, offset_h: int) -> int:
        """return offset of the *end* of the last row within bounds not more than query"""
        logging.debug('upper bound 2 %s %s %s', query, offset_l, offset_h)
        if offset_l >= offset_h:
            return self._seek_back_to_line_start(offset_l)

        mid = (offset_l + offset_h) // 2

        line_start = self._seek_back_to_line_start(mid)
        #current_id = self._id_from_line(line_start)
        current_line = self._get_line(line_start)
        next_line_start = self._seek_to_next_line(mid)

        #if current_id >= query:
        if current_line <= query:
            return self._upper_bound(query=query, offset_l=next_line_start, offset_h=offset_h)
        return self._upper_bound(query=query, offset_l=offset_l, offset_h=line_start - 1)
