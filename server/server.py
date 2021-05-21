"""Decodes and logs angular data from AMS AS5048A."""
# pylint: disable=fixme, missing-function-docstring, inconsistent-return-statements
import json
import logging
import time
from typing import Any
from flask import abort, Flask, Response, request
from waitress import serve
from data_reader import DataReader

app = Flask(__name__)

data_reader = DataReader()

def downsample(dataframe: Any, freq: str) -> Any:
    if dataframe.empty:
        return dataframe
    return dataframe.resample(freq).sum()

def json_response(dataframe: Any) -> Any:
    start_ns = time.time_ns()
    json_payload = json.dumps(dataframe.to_records().tolist())
    end_ns = time.time_ns()
    logging.info("json microsec %d", (end_ns - start_ns) // 1000)
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
        return json_response(data_reader.read_sec(window))
    if freq == 'T':
        return json_response(data_reader.read_min(window))
    if freq == 'H':
        return json_response(downsample(data_reader.read_min(window), 'H'))
    if freq == 'D':
        return json_response(downsample(data_reader.read_min(window), 'D'))
    abort(404, 'Bad parameter')

@app.route('/data2/<start>/<end>/<int:buckets>')
def data2(start: str, end: str, buckets: int) -> Any:
    logging.info('data2 %s %s %d', start, end, buckets)
    return json_response(data_reader.read_range(start, end, buckets))

def start_timer():
    request.start_time_ns = time.time_ns()
    logging.info("start %s %s", request.method, request.path)

def stop_timer(response):
    request.latency_ns = time.time_ns() - request.start_time_ns
    return response

def record_request_data(response):
    logging.info("response %s %s %d %d %d", request.method, request.path, response.status_code,
        response.content_length, request.latency_ns // 1000)
    return response

def setup_metrics(flask_app):
    flask_app.before_request(start_timer)
    flask_app.after_request(record_request_data)
    flask_app.after_request(stop_timer)

def main() -> None:
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(created).6f %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S', level=logging.INFO)
    setup_metrics(app)
    serve(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
