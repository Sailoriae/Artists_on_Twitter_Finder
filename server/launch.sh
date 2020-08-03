#!/bin/sh
python3 $(dirname "$0")/app.py | tee $(dirname "$0")/latest.log
