#!/bin/sh
set -e

if [ "$DEBUG" = "1" ]; then
    echo "Starting app in debug mode..."
    poetry run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m lsu_pilot.main
else
    echo "Starting app in production mode..."
    poetry run python -m lsu_pilot.main
fi