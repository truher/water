"""Decode and log angular data from AMS AS5048A."""
# pylint: disable=import-error, import-outside-toplevel
import argparse
import json
import threading
import time
from datetime import datetime
from typing import Any
import pandas as pd #type:ignore
from flask import Flask, Response
from waitress import serve
import lib

app = Flask(__name__)

DATA_SEC = "data_sec" # temporary
DATA_MIN = "data_min" # permanent

# 5hz full speed
# nyquist would be 10hz sample rate
# let's leave it at 50hz for now
# maybe reduce it later
#sample_period_ns = 2e7 # 0.02s
SAMPLE_PERIOD_NS: int = 5000000 # 0.005s

# 5hz full speed
# 50hz sample rate
# = 10 samples per revolution
# so make threshold double that
ZERO_CROSSING_THRESHOLD: int = 7168

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

def setup_spi(spi: Any) -> None:
    """set speed etc"""
    spi.open(0, 0)
    #spi.max_speed_hz = 1000000
    spi.max_speed_hz = 4000
    spi.mode = 1


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
# note delivered volume is positive for negative angle increments
CONSTANT_UL_PER_ANGLE = -0.0002

def volume_ul(delta_cumulative_angle: int) -> int:
    """return microliters"""
    return int(delta_cumulative_angle * CONSTANT_UL_PER_ANGLE)

class DataWriter:
    """write a line every so often"""
    def __init__(self, filename: str, write_mod_sec: int, trunc_mod_sec: int) -> None:
        self.filename = filename
        self.write_mod_sec = write_mod_sec
        self.trunc_mod_sec = trunc_mod_sec
        self.sink = open(filename, 'ab')
        self.cumulative_angle = 0
        self.cumulative_volume_ul = 0
        self.current_second: int = 0

    def write(self, now_ns: int, cumulative_angle: int, cumulative_volume_ul:int) -> None:
        """handle a datum"""
        now_s = int(now_ns // 1000000000)
        if now_s <= self.current_second:
            return
        self.current_second = now_s

        if self.trunc_mod_sec != 0 and now_s % self.trunc_mod_sec == 0:
            self.sink.close()
            with open(self.filename, 'w') as trunc_sink:
                trunc_sink.truncate()
            self.sink = open(self.filename, 'ab')

        if now_s % self.write_mod_sec != 0:
            return

        dt_now: datetime = datetime.utcfromtimestamp(now_s)
        dts: str = dt_now.isoformat() + '.' + str(int(now_ns % 1000000000)).zfill(9)
        delta_cumulative_angle = cumulative_angle - self.cumulative_angle
        delta_volume_ul = cumulative_volume_ul - self.cumulative_volume_ul

        output_line = (f"{dts}\t{delta_cumulative_angle}\t{delta_volume_ul}")
        self.sink.write(output_line.encode('ascii'))
        self.sink.write(b'\n')
        self.sink.flush()
        self.cumulative_angle = cumulative_angle
        self.cumulative_volume_ul = cumulative_volume_ul

class Meter:
    """keep the state of the meter"""
    def __init__(self) -> None:
        self.previous_cumulative_angle: int = 0
        self.cumulative_volume_ul: int = 0
        self.previous_second: int = 0

    def update_volume(self, now_ns: int, cumulative_angle: int) -> None:
        """handle an observation, note this must be called frequently enough"""
        current_second: int = int(now_ns // 1000000000)
        if current_second > self.previous_second:
            # just crossed the boundary
            delta_cumulative_angle:int = cumulative_angle - self.previous_cumulative_angle
            delta_volume_ul:int = volume_ul(delta_cumulative_angle)
            self.cumulative_volume_ul += delta_volume_ul
            self.previous_second = current_second
            self.previous_cumulative_angle = cumulative_angle

    def read_angle(self) -> int:
        """read the cumulative state"""
        pass
    def read_volume_ul(self) -> int:
        """read the cumulative state"""
        return self.cumulative_volume_ul


def data_reader() -> None:
    """read input"""

    args: argparse.Namespace = parse()
    spi: Any = make_spi(args)
    setup_spi(spi)

    sensor: lib.Sensor = lib.Sensor(spi)

    cumulative_turns: int = 0
    previous_angle: int = 0

    # write every second, truncate every 10 seconds
    sec_writer: DataWriter = DataWriter(DATA_SEC, 1, 10)

    # write every 60 seconds, never truncate
    min_writer: DataWriter = DataWriter(DATA_MIN, 60, 0)

    meter: Meter = Meter()

    while True:
        try:
            if args.verbose:
                verbose(sensor)
                continue

            now_ns: int = time.time_ns()
            waiting_ns: int = int(SAMPLE_PERIOD_NS - (now_ns % SAMPLE_PERIOD_NS))
            time.sleep(waiting_ns / 1e9)
            now_ns = time.time_ns()

            # TODO: hide this spi-specific stuff
            angle = sensor.transfer(lib.ANGLE_READ_REQUEST) & lib.RESPONSE_MASK

            if angle == 0:
                # TODO: zero is not *always* an error.  fix this.
                print("skipping zero result")
                continue

            # TODO: pull this stateful angle calculation into a class
            if previous_angle == 0:
                previous_angle = angle
            d_angle: int = angle - previous_angle
            if d_angle < (-1 * ZERO_CROSSING_THRESHOLD):
                cumulative_turns += 1
            if d_angle > ZERO_CROSSING_THRESHOLD:
                cumulative_turns -= 1
            cumulative_angle = cumulative_turns * 16384 + angle
            previous_angle = angle

            meter.update_volume(now_ns, cumulative_angle)

            sec_writer.write(now_ns, cumulative_angle, meter.read_volume_ul())
            min_writer.write(now_ns, cumulative_angle, meter.read_volume_ul())

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
    df_sec = pd.read_csv(DATA_SEC, delim_whitespace=True, index_col=0,
                     parse_dates=True, header=None,
                     names=['time', 'angle', 'volume'])
    # TODO: use the by-minute file instead
    df_min = df_sec.resample('T').sum()
    json_payload = json.dumps(df_min.to_records().tolist())
    return Response(json_payload, mimetype='application/json')

def main() -> None:
    """main"""
    threading.Thread(target=data_reader).start()
    serve(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
