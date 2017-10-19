#!/usr/bin/env bash
set -euo pipefail

echo "Restore data into MongoDB"
cd /home/data/dump

# - restore .json file as collections in test database
for file in *.json; do
    echo "  - restore ${file} to MongoDB"
    mongoimport --host localhost --port 27017 --db test --collection $(basename "${file}" .json) --drop --file ${file}
done

# - restore database dumps (bson format) in their own database
for database in */ ; do
    if  [ "${database}" != "*/" ]; then
        echo "  - restore ${database} to MongoDB"
        mongorestore --port 27017 --db "${database%%/}" --drop "$database"
    fi
done