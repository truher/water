"""efficiently select only part of a file"""
from io import TextIOBase
from typing import Any, List

SEP = "\t"
class RangeSearch:
    """select a range of rows"""

    def __init__(self, iobase: TextIOBase) -> None:
        self.iobase = iobase
        self.length = 0

    def __enter__(self) -> Any:
        self.iobase.seek(0, 2)
        self.length = self.iobase.tell()
        return self

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None: # pylint: disable=W0622
        pass

    def search(self, query_low: str, query_high: str) -> List[List[str]]:
        """return rows between low and high queries, inclusive"""
        if query_high < query_low:
            return []
        offset = self._lower_bound(query=query_low, offset_l=0, offset_h=self.length)
        return self._scan(offset, query_high)

    def _scan(self, offset: int, query_high: str) -> List[List[str]]:
        """return rows from offset to query_high, inclusive"""
        self.iobase.seek(offset)
        whole_line = self.iobase.readline()
        if len(whole_line) == 0:
            return []
        line = whole_line.strip().split(SEP)
        result = []
        while line[0] <= query_high:
            result.append(line)
            whole_line = self.iobase.readline()
            line = whole_line.strip().split(SEP)
            if line == ['']:  # happens only at the last line.
                break
        return result

    def _id_from_line(self, offset: int) -> str:
        self.iobase.seek(offset)
        return self.iobase.readline().split(SEP, 1)[0]

    def _seek_to_next_line(self, offset: int) -> int:
        """return offset of next line after offset"""
        self.iobase.seek(offset)
        self.iobase.readline()
        return self.iobase.tell()

    def _seek_back_to_line_start(self, offset: int) -> int:
        """return offset of beginning of the line offset is within"""
        line_start = offset
        while line_start >= 0:
            self.iobase.seek(line_start)
            if self.iobase.read(1) == '\n':
                if line_start <= self.length:
                    line_start += 1
                break
            line_start -= 1
        if line_start < 0:
            line_start = 0
            self.iobase.seek(line_start)
        return line_start

    def _lower_bound(self, query: str, offset_l: int, offset_h: int) -> int:
        """return offset of first row within bounds not less than query"""
        if offset_l >= offset_h:
            return self._seek_back_to_line_start(offset_l)

        mid = (offset_l + offset_h) // 2

        line_start = self._seek_back_to_line_start(mid)
        current_id = self._id_from_line(line_start)
        next_line_start = self._seek_to_next_line(mid)

        if current_id >= query:
            return self._lower_bound(query=query, offset_l=offset_l, offset_h=line_start - 1)
        return self._lower_bound(query=query, offset_l=next_line_start, offset_h=offset_h)
