#!/usr/bin/env bash
# Local / VPS run. First time: pip install -r web/requirements.txt
set -e
export APP_DATA_DIR="${APP_DATA_DIR:-$(pwd)/data}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-changeme}"
exec uvicorn web.app:app --host 0.0.0.0 --port "${PORT:-8000}"
