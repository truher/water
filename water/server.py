"""Decodes and logs angular data from AMS AS5048A."""
# pylint: disable=fixme, missing-function-docstring, inconsistent-return-statements
import argparse
import json
import logging
import threading
from typing import Any
from flask import abort, Flask, Response
from waitress import serve
from reader import Reader
from writer import DataWriter
import spi

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S', level=logging.INFO)

app = Flask(__name__)

# TODO: hide the multiple-file thing from the server
writer_min = DataWriter("data_min", 60, 0)     # archival, keep forever
writer_sec = DataWriter("data_sec", 1, 604800) # temporary, keep 7 days

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
    logging.debug("index")
    return app.send_static_file('index.html')

@app.route('/timeseries/<freq>')
@app.route('/timeseries/<freq>/<int:window>')
def timeseries(freq: str, window: int = 0) -> Any:
    logging.debug("timeseries %s %d", freq, window)
    return app.send_static_file('timeseries.html')

@app.route('/timeseries2')
def timeseries2() -> Any:
    logging.debug("timeseries2")
    return app.send_static_file('timeseries2.html')

@app.route('/data/<freq>')
@app.route('/data/<freq>/<int:window>')
def data(freq: str, window: int = 0) -> Any:
    logging.debug('data %s %d', freq, window)
    if freq == 'S':
        return json_response(writer_sec.read(window))
    if freq == 'T':
        return json_response(writer_min.read(window))
    if freq == 'H':
        return json_response(downsample(writer_min.read(window), 'H'))
    if freq == 'D':
        return json_response(downsample(writer_min.read(window), 'D'))
    abort(404, 'Bad parameter')

@app.route('/data2/<start>/<end>/<int:buckets>')
def data2(start: str, end: str, buckets: int) -> Any:
    logging.info('data2 %s %s %d', start, end, buckets)
    # TODO: select sec or min depending on range and grain
    # TODO: downsample to fit grain
    # TODO: hide the multiple-file thing from the server
    #return json_response(writer_min.read_range(start, end))
    return json_response(writer_sec.read_range(start, end, buckets))

def main() -> None:
    threading.Thread(target=data_reader).start()
    serve(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
