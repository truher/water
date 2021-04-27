"""Decode and log angular data from AMS AS5048A."""
# pylint: disable=import-error, import-outside-toplevel
import argparse
import json
import threading
import time
from typing import Any
import pandas as pd #type:ignore
from flask import Flask, Response
from waitress import serve
import lib
import meter
import volume
import writer

app = Flask(__name__)

DATA_SEC = "data_sec" # temporary
DATA_MIN = "data_min" # permanent

# 5hz full speed
# nyquist would be 10hz sample rate
# let's leave it at 50hz for now
# maybe reduce it later
#sample_period_ns = 2e7 # 0.02s
SAMPLE_PERIOD_NS: int = 5000000 # 0.005s

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

def data_reader() -> None:
    """read input"""

    args: argparse.Namespace = parse()
    spi: Any = make_spi(args)
    setup_spi(spi)

    sensor: lib.Sensor = lib.Sensor(spi)
    meter_state: meter.Meter = meter.Meter()
    volume_state: volume.Volume = volume.Volume()

    sec_writer: writer.DataWriter = writer.DataWriter(DATA_SEC, 1, 10)
    min_writer: writer.DataWriter = writer.DataWriter(DATA_MIN, 60, 0)

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

            meter_state.update(angle)
            volume_state.update(now_ns, meter_state.read())
            sec_writer.write(now_ns, meter_state.read(), volume_state.read())
            min_writer.write(now_ns, meter_state.read(), volume_state.read())

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
