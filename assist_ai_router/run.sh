#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
cd /opt/router
exec python -m app.server --data /data
