#!/usr/bin/bash
export PYTHONPATH="${PYTHONPATH}:$PWD/water:$PWD/search"
python3 water/reader.py --fake &
python3 water/server.py &
