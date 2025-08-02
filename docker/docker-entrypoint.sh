#!/bin/bash -ex

# shellcheck disable=SC2154
echo "pwd: ${PWD}"

# Activate the poetry venv
. "${APP_ROOT_DIR}/.venv/bin/activate"

export PYTHONPATH="${APP_ROOT_DIR}/app"

exec gunicorn -w 4 -k uvicorn.workers.UvicornH11Worker main:app -b 0.0.0.0:${PORT} --log-level info --timeout 60