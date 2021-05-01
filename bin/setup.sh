#!/usr/bin/bash

# Setup script for Raspberry Pi 4.0

sudo apt install -y \
  git \
  python3 \
  python3-dev \
  python3-pip \
  libatlas-base-dev
python3 -m pip install \
  waitress \
  flask \
  pandas
