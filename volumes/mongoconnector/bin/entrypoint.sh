#!/usr/bin/env bash
set -euo pipefail

# Entry script for mongoconnector container
# - wait for databases connections to be open
# - generate config.json
# - generate missing target database and users in postgres
# - start the synchro
# - create additional objects in postgres

cd /home/bin
python prepare_mongoconnector.py
python reset_postgres.py
python synchro_status.py &

# Starting mongo-connector
cd /home/data
echo "ok. Starting mongo-connector..."
mongo-connector -c config.json


