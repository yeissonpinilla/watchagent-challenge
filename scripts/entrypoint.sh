#!/bin/sh
set -e

mkdir -p /app/data

python -m app.bootstrap

python -m app.services.poller &
POLLER_PID=$!

trap 'kill "$POLLER_PID" 2>/dev/null; exit 0' TERM INT

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
