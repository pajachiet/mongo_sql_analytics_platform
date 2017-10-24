#!/usr/bin/env bash
set -euo pipefail

mkdir -p /home/data/dump/demo
cd /home/data/dump/demo

#TODO: Add back catalog.books.json when bug in pymongo-schema will be identified (no mapping)
#TODO : Modify pymongo-schema to quote / change special keywords
#TODO: Add back profiles.json when bug in sql syntax will be resolved
# psycopg2.ProgrammingError: syntax error at or near "user"
# LINE 1: ...student_id INT ,responseLength INT ,ts TIMESTAMP ,user TEXT ...
#TODO: Add back products.json when bug in sql syntax will be resolved
#LINE 1: ...es SERIAL CONSTRAINT PRODUCTS__FOR_PK PRIMARY KEY,for TEXT ,...
#TODO: Add back restaurant.json with new pymongo-schema correction on ' '

for file in \
    city_inspections.json \
    companies.json \
    countries.json \
    country.json \
    covers.json \
    grades.json \
    students.json
do
    if [ ! -e ${file} ]; then
        echo "Downloading file '${file}'"
        wget https://github.com/ozlerhakan/mongodb-json-files/raw/master/datasets/${file}
    else
        echo "File '${file}' already exists"
    fi
done

#TODO: Add back with new pymongo-schema correction on '-'

#file=primer-dataset.json
#if [ ! -e ${file} ]; then
#    echo "Downloading file '${file}'"
#    wget https://raw.githubusercontent.com/mongodb/docs-assets/primer-dataset/${file}
#else
#    echo "File '${file}' already exists"
#fi