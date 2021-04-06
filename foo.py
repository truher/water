import time
#import select
grain = int(5e8)
while True:
    x=time.time_ns()
    y= int(grain - (x % grain))
    #print(f"x: {x} y: {y}")
    time.sleep(y/1e9)
    #select.select([], [], [], 0.1)
    print(int(x))
