#!/usr/bin/bash
export PYTHONPATH="${PYTHONPATH}:$PWD/search:$PWD/server:$PWD/water"
python3 water/reader.py --fake &
python3 server/server.py &
