"""Decode and log angular data from AMS AS5048A."""
# pylint: disable=fixme
import argparse
import json
import threading
from typing import Any, List
import pandas as pd #type:ignore
from flask import Flask, Response
from waitress import serve
from reader import Reader
from writer import DataWriter
import spi

app = Flask(__name__)

DATA_SEC = "data_sec" # temporary
DATA_MIN = "data_min" # permanent

def parse() -> argparse.Namespace:
    """define and parse command line args"""
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true",
                        help="use fake spidev, for testing/calibration")
    parser.add_argument("--verbose", action="store_true",
                        help="read everything, not just angle")
    args: argparse.Namespace = parser.parse_args()
    return args

def data_reader() -> None:
    """read input"""
    writers: List[DataWriter] = [DataWriter(DATA_SEC, 1, 10), DataWriter(DATA_MIN, 60, 0)]
    Reader(spi.make_and_setup_spi(parse()), writers).run()

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
