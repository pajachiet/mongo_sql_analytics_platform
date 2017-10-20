#!/usr/bin/env bash
set -eo pipefail

# Script to initialize Superset
# This script is idempotent, and can be run several times
# - Initialize docker admin

echo "Waiting until Superset starts"
until $(curl --output /dev/null --silent --head --fail http://localhost:8088); do
    printf '.'
    sleep 2
done

echo "
Create Superset admin account.
A normal error will occur if it already exists.
"

superset-init --username=${SUPERSET_ADMIN_USERNAME} --firstname='admin' --lastname='user' --email='admin@fab.org' --password=${SUPERSET_ADMIN_PASSWD}

cd /etc/superset/bin
python3 init_superset_databases.py
