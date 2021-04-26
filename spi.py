"""Decode and log angular data from AMS AS5048A."""
# pylint: disable=import-error, import-outside-toplevel
import argparse
import json
import pandas as pd
import threading
import time
from datetime import datetime
from flask import Flask, Response
from typing import Any
from waitress import serve #type:ignore
import collections
import lib


app = Flask(__name__)

#raw_data = collections.deque(maxlen=5000)

#sampled_data = collections.deque(maxlen=5000)

FILENAME = "datafile"

def parse() -> argparse.Namespace:
    """define and parse command line args"""
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true",
                        help="use fake spidev, for testing/calibration")
    parser.add_argument("--verbose", action="store_true",
                        help="read everything, not just angle")
    args: argparse.Namespace = parser.parse_args()
    return args

def make_spi(args: argparse.Namespace) -> Any:
    """poor man's DI"""
    if args.fake:
        print("using fake spidev")
        import sim
        return sim.SimulatorSpiDev()
    print("using real spidev")
    import spidev # type: ignore
    return spidev.SpiDev()

def verbose(sensor: Any) -> None:
    """log extra"""
    sensor.transfer(lib.ANGLE_READ_REQUEST)
    angle: int = sensor.transfer(lib.NOP_REQUEST) & lib.RESPONSE_MASK

    sensor.transfer(lib.MAGNITUDE_REQUEST)
    magnitude: int = sensor.transfer(lib.NOP_REQUEST) & lib.RESPONSE_MASK

    sensor.transfer(lib.DIAGNOSTIC_REQUEST)
    diagnostic: int = sensor.transfer(lib.NOP_REQUEST)
    #                               5432109876543210
    comp_high: int = diagnostic & 0b0000100000000000
    comp_low: int  = diagnostic & 0b0000010000000000
    cof: int       = diagnostic & 0b0000001000000000
    ocf: int       = diagnostic & 0b0000000100000000
    agc: int       = diagnostic & 0b0000000011111111

    lib.log(angle, magnitude, comp_high, comp_low, cof, ocf, agc)


# this is not the way it will work, but it's a place to start
CONSTANT_UL_PER_ANGLE = 0.0002

def volume_ul(delta_cumulative_angle: int) -> int:
    """return microliters"""
    return int(delta_cumulative_angle * CONSTANT_UL_PER_ANGLE)

def data_reader() -> None:
    """read input"""

    args: argparse.Namespace = parse()
    spi: Any = make_spi(args)

    spi.open(0, 0)
    #spi.max_speed_hz = 1000000
    spi.max_speed_hz = 4000
    spi.mode = 1
    # 5hz full speed
    # nyquist would be 10hz sample rate
    # let's leave it at 50hz for now
    # maybe reduce it later
    #sample_period_ns = 2e7 # 0.02s
    sample_period_ns: int = 5000000 # 0.005s
    # 5hz full speed
    # 50hz sample rate
    # = 10 samples per revolution
    # so make threshold double that
    zero_crossing_threshold: int = 7168

    sensor: lib.Sensor = lib.Sensor(spi)

    cumulative_turns: int = 0
    previous_angle: int = 0
    previous_cumulative_angle: int = 0
    current_second: int = time.time_ns() // 1e9
    previous_second: int = current_second
    cumulative_volume_ul: int = 0

    with open(FILENAME, 'ab') as sink:

        while True:
            try:
                if args.verbose:
                    verbose(sensor)
                    continue

                now_ns: int = time.time_ns()
                waiting_ns: int = int(sample_period_ns - (now_ns % sample_period_ns))
                time.sleep(waiting_ns / 1e9)
                now_ns = time.time_ns()

                angle = sensor.transfer(lib.ANGLE_READ_REQUEST) & lib.RESPONSE_MASK

                if angle == 0:
                    # TODO: zero is not *always* an error.  fix this.
                    print("skipping zero result")
                    continue

                dt_now: datetime = datetime.utcfromtimestamp(now_ns // 1e9)
                dts: str = dt_now.isoformat() + '.' + str(int(now_ns % 1e9)).zfill(9)

                if previous_angle == 0:
                    previous_angle = angle

                d_angle: int = angle - previous_angle

                if d_angle < (-1 * zero_crossing_threshold):
                    cumulative_turns += 1

                if d_angle > zero_crossing_threshold:
                    cumulative_turns -= 1

                cumulative_angle = cumulative_turns * 16384 + angle

                #print(f"{dts} {angle:5} {cumulative_angle:6} {cumulative_turns:5}")
                #raw_data.append({'dts':dts,
                #             'angle':angle,
                #             'cumulative_angle':cumulative_angle,
                #             'cumulative_turns':cumulative_turns})

                current_second = int(now_ns // 1e9)
                if current_second > previous_second:
                    # just crossed the boundary
                    delta_cumulative_angle:int = cumulative_angle - previous_cumulative_angle
                    delta_volume_ul:int = volume_ul(delta_cumulative_angle)
                    cumulative_volume_ul += delta_volume_ul

                    print(f"new second, cumulative angle: {cumulative_angle} "
                          f"delta cumulative angle: {delta_cumulative_angle} "
                          f"cumulative volume ul: {cumulative_volume_ul}")
                    #sampled_data.append({'dts':dts, 'angle':cumulative_angle})
                    #output_line = f"{dts}\t{cumulative_angle}\t{cumulative_volume_ul}"
                    output_line = f"{dts}\t{delta_cumulative_angle}\t{delta_volume_ul}"
                    sink.write(output_line.encode('ascii'))
                    sink.write(b'\n')
                    sink.flush()

                    previous_second = current_second
                    previous_cumulative_angle = cumulative_angle

                previous_angle = angle

            except lib.ResponseLengthException as err:
                print(f"Response Length Exception {err}")
            except lib.ResponseParityException as err:
                print(f"Response Parity Exception {err}")
            except lib.ResponseErrorRegisterException as err:
                print(f"Response Error Register {err}")


@app.route('/')
def index() -> Any:
    """index"""
    print('index')
    return app.send_static_file('index.html')

@app.route('/timeseries')
def timeseries() -> Any:
    """timeseries"""
    print('timeseries')
    return app.send_static_file('timeseries.html')

@app.route('/data')
def data() -> Any:
    """data"""
    print('data')

    #json_payload = json.dumps(list(raw_data))
    #json_payload = json.dumps(list(sampled_data))
    #print(json_payload)

    df = pd.read_csv(FILENAME, delim_whitespace=True, index_col=0,
                     parse_dates=True, header=None,
                     names=['time', 'angle', 'volume'])
    by_min = df.resample('T').sum()
    json_payload = json.dumps(by_min.to_records().tolist())
    return Response(json_payload, mimetype='application/json')

def main() -> None:
    """main"""
    threading.Thread(target=data_reader).start()
    serve(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
