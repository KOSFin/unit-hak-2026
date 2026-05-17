#!/bin/sh
set -eu

UPLOADS_DIR="${UPLOADS_PATH:-${UPLOADS_DIR:-uploads}}"

case "$UPLOADS_DIR" in
    /*) uploads_path="$UPLOADS_DIR" ;;
    *) uploads_path="/app/$UPLOADS_DIR" ;;
esac

mkdir -p "$uploads_path"
chown -R appuser:appgroup "$uploads_path"

exec gosu appuser "$@"
