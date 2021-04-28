"""Decode and log angular data from AMS AS5048A."""
# pylint: disable=fixme, missing-function-docstring
import argparse
import csv
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
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true", help="use fake spidev, for testing")
    parser.add_argument("--verbose", action="store_true", help="read everything, not just angle")
    args: argparse.Namespace = parser.parse_args()
    return args

def data_reader() -> None:
    writers: List[DataWriter] = [DataWriter(DATA_SEC, 1, 1000), DataWriter(DATA_MIN, 60, 0)]
    Reader(spi.make_and_setup_spi(parse()), writers).run()

@app.route('/')
def index() -> Any:
    return app.send_static_file('index.html')

@app.route('/timeseries')
def timeseries() -> Any:
    return app.send_static_file('timeseries.html')

def data(filename: str) -> Any:
    json_payload = data_dataframe(filename)
    #json_payload = data_verbatim(filename)
    return Response(json_payload, mimetype='application/json')

def data_dataframe(filename: str) -> Any:
    """pandas parses the dates and produces ints that javascript can read"""
    dataframe = pd.read_csv(filename, delim_whitespace=True, index_col=0, parse_dates=True,
                            header=None, names=['time', 'angle', 'volume'])
    return json.dumps(dataframe.to_records().tolist())

def data_verbatim(filename: str) -> Any:
    """or we can just pass the strings verbatim"""
    return json.dumps(list(csv.reader(open(filename), delimiter='\t')))

@app.route('/data_by_sec')
def data_by_sec() -> Any:
    """the per-second data is truncated periodically"""
    return data(DATA_SEC)

@app.route('/data_by_min')
def data_by_min() -> Any:
    """the per-minute data is the archival master"""
    return data(DATA_MIN)

def downsampled_data(freq: str) -> Any:
    dataframe = pd.read_csv(DATA_MIN, delim_whitespace=True, index_col=0, parse_dates=True,
                            header=None, names=['time', 'angle', 'volume'])
    df_by_hr = dataframe.resample(freq).sum()
    json_payload = json.dumps(df_by_hr.to_records().tolist())
    return Response(json_payload, mimetype='application/json')

@app.route('/data_by_hr')
def data_by_hr() -> Any:
    return downsampled_data('H')

@app.route('/data_by_day')
def data_by_day() -> Any:
    return downsampled_data('D')

def main() -> None:
    threading.Thread(target=data_reader).start()
    serve(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
