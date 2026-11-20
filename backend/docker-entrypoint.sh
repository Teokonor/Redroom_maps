#!/bin/sh
set -eu

python -m app.migrate

exec "$@"
