"""Decodes and logs angular data from AMS AS5048A."""
# pylint: disable=fixme, missing-function-docstring
import argparse
import json
import logging
import threading
from typing import Any
from flask import Flask, Response
from waitress import serve
from reader import Reader
from writer import DataWriter
import spi

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S',
                    level=logging.DEBUG)

app = Flask(__name__)

DATA_SEC = "data_sec" # temporary
DATA_MIN = "data_min" # permanent

writer_min = DataWriter(DATA_MIN, 60, 0)     # archival, keep forever
writer_sec = DataWriter(DATA_SEC, 1, 604800) # temporary, keep 7 days

def parse() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true", help="use fake spidev, for testing")
    parser.add_argument("--verbose", action="store_true", help="read everything, not just angle")
    args: argparse.Namespace = parser.parse_args()
    return args

def data_reader() -> None:
    Reader(spi.make_and_setup_spi(parse()), [writer_sec, writer_min]).run()

def downsample(dataframe: Any, freq: str) -> Any:
    if dataframe.empty:
        return dataframe
    return dataframe.resample(freq).sum()

def json_response(dataframe: Any) -> Any:
    json_payload = json.dumps(dataframe.to_records().tolist())
    return Response(json_payload, mimetype='application/json')

@app.route('/')
def index() -> Any:
    logging.info("index")
    return app.send_static_file('index.html')

@app.route('/timeseries')
def timeseries() -> Any:
    logging.info("timeseries")
    return app.send_static_file('timeseries.html')

@app.route('/data_by_sec')
def data_by_sec() -> Any:
    logging.info("data_by_sec")
    return json_response(writer_sec.read())

@app.route('/data_by_min')
def data_by_min() -> Any:
    logging.info("data_by_min")
    return json_response(writer_min.read())

@app.route('/data_by_hr')
def data_by_hr() -> Any:
    logging.info("data_by_hr")
    return json_response(downsample(writer_min.read(), 'H'))

@app.route('/data_by_day')
def data_by_day() -> Any:
    logging.info("data_by_day")
    return json_response(downsample(writer_min.read(), 'D'))

def main() -> None:
    threading.Thread(target=data_reader).start()
    serve(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
