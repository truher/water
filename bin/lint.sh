#!/usr/bin/bash
mypy --ignore-missing-imports water search
pylint water search
