#!/usr/bin/env bash
set -euo pipefail

# Entry script for mongoconnector container
# - wait for databases connections to be open
# - generate config.json
# - generate missing target database and users in postgres
# - start the synchro
# - create additional objects in postgres


mkdir -p /home/generated
cd /home/bin
python reset_mongoconnector.py
python run_pymongo_schema.py
python reset_postgres.py
python synchro_status.py &

# Starting mongo-connector
cd /home/generated
echo "ok. Starting mongo-connector..."
mongo-connector -c config.json


