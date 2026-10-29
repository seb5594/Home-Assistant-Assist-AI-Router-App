#!/usr/bin/env bash
set -Eeuo pipefail

export PYTHONPATH=/opt/router:/tests
cd /opt/router
python -m unittest test_router -v
echo 'PASS: routing, concurrent quota reservations, fallbacks and persistence'
python -m unittest test_settings -v
echo 'PASS: Supervisor writes, secrets and configuration conflicts'
python -m unittest test_http -v
echo 'PASS: HTTP authentication, Assist tools, SSE and actual LiteLLM SDK'
python -m unittest test_discovery -v
echo 'PASS: direct provider model listing, draft credentials, secrets and redirect safety'
