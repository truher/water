import logging
import mmap
import time
import timeit
import pandas as pd
from search2 import RangeSearch2
from typing import Any, List

# min file is about 10k rows
# select the middle ~third, so row 3000 to 7000 ish
# sec file is about 633k rows

COLUMNS = ['time','angle','volume_ul']
N = 10
#N = 1

def data_frame(rows: List[List[str]]) -> Any:
    if len(rows) == 0:
        return pd.DataFrame(columns=COLUMNS)
    data_frame = pd.DataFrame(rows, columns=COLUMNS)
    data_frame['time'] = pd.to_datetime(data_frame['time'])
    data_frame['angle'] = data_frame['angle'].astype(int)
    data_frame['volume_ul'] = data_frame['volume_ul'].astype(int)
    data_frame = data_frame.set_index('time')
    return data_frame

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(created).6f %(levelname)s [%(filename)s:%(lineno)d] %(message)    s', datefmt='%Y-%m-%dT%H:%M:%S', level=logging.INFO)

#start_key = "2021-05-04T23:40:00.000131835"
#end_key = "2021-05-20T05:11:00.000136916"
start_key = "2021-05-04T23:40" # 180009 of data_sec
end_key = "2021-05-20T05:11" # 416371 of data_sec
#filename = "data_min"
filename = "data_sec"


print("============= LOWER BOUND AND SCAN WITH COMPARE ============")
def lower_bound_scan_with_compare():
    with open(filename) as file:
        with RangeSearch2(file) as rng:
            result = rng.search(start_key, end_key)
            df = data_frame(result)
            #print(len(df.index))
            #print(df[:1])
            #print(df[-1:])
print(timeit.timeit("lower_bound_scan_with_compare()", globals=globals(), number=N))

print("============= BOTH BOUNDS, SCAN WITHOUT COMPARE ============")
def both_bounds_scan_without_compare():
    with open(filename) as file:
        with RangeSearch2(file) as rng:
            result = rng.search2(start_key, end_key)
            df = data_frame(result)
            #print(len(df.index))
            #print(df[:1])
            #print(df[-1:])
print(timeit.timeit("both_bounds_scan_without_compare()", globals=globals(), number=N))

print("============= BOTH BOUNDS, READ_CSV OVER MMAP ============")
def both_bounds_read_csv_over_mmap():
    with open(filename, "r+") as file:
        with RangeSearch2(file) as rng:
            (lo, hi) = rng.search3(start_key, end_key)
            lo_mm = mmap.ALLOCATIONGRANULARITY * (lo // mmap.ALLOCATIONGRANULARITY)
            lo_diff = lo - lo_mm
            with mmap.mmap(file.fileno(), hi-lo_mm, offset=lo_mm) as mm:
                mm.seek(lo_diff)
                df = pd.read_csv(mm, delim_whitespace=True, index_col=0,
                    parse_dates=True, header=None, names=['time', 'angle', 'volume_ul'],
                    skiprows=0, memory_map=True, engine="c")
                #print(len(df.index))
                #print(df[:1])
                #print(df[-1:])
print(timeit.timeit("both_bounds_read_csv_over_mmap()", globals=globals(), number=N))

exit()
