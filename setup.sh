#!/usr/bin/bash
sudo apt install -y \
  git \
  python3 \
  python3-dev \
  python3-pip
python3 -m pip install \
  waitress \
  flask \
  pandas
