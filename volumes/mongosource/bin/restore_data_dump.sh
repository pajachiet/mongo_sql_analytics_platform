#!/usr/bin/env bash
set -euo pipefail

echo "Deleting 'metatadata.json' files from bson dump, as we do not need mongo indexes, indexes may cause errors while restoring, and we assume that '.json' files are collections."
rm -rf /home/dump/*/*.metadata.json


echo "== Restore data into MongoDB"
cd /home/data/dump


for db_folder in */ ; do
    if  [ "${db_folder}" != "*/" ]; then
        echo " - Restore data from '${db_folder}' folder, to a MongoDB database with the same name"
        echo "Restore bson dumps, if present…"
        mongorestore --db "${db_folder%%/}" --drop "$db_folder"

        echo "Restore '.json' collections, if present…"
        for file in ${db_folder}*.json; do
            echo "  -- restore '${file}' file to a MongoDB collection with the same name"
            mongoimport --db "${db_folder%%/}" --collection $(basename "${file}" .json) --drop --file ${file}
        done
    fi
done