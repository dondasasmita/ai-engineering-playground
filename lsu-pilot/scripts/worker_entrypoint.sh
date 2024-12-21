#!/bin/sh
set -e

if [ "$DEBUG_WORKER" = "1" ]; then
    echo "Starting worker in debug mode..."
    poetry run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m celery -A workers.celery_app worker --loglevel=info
else
    echo "Starting worker in production mode..."
    poetry run celery -A workers.celery_app worker --loglevel=info
fi