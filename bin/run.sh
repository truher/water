#!/usr/bin/bash
export PYTHONPATH="${PYTHONPATH}:$PWD/server:$PWD/search:$PWD/water"
python3 water/reader.py &
python3 server/server.py &
