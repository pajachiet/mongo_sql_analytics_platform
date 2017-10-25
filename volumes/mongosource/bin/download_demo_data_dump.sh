#!/usr/bin/env bash
set -euo pipefail

mkdir -p /home/data/dump/demo
cd /home/data/dump/demo


# The following data dump are not downloaded from ozlerhakan/mongodb-json-files because they create bug
# - restaurant.json contains a key with a space ' ', which create bugs (pymongo-schema and/or mongo-connector-postgresql ?)
# - catalog.books.json create a bug in pymongo-schema because of the '.' in the name.
# TODO : identify where the problem is (probably if we split namespace db.collection ?) and correct it
# - profiles.json create a bug in mongo-connector postgresql because it contains a column named 'user'
# - products.json create a bug in mongo-connector postgresql because it contains a column named 'for'
#TODO : Modify mongo-connector-postgresql to quote identifier and distinguish them from keyworkds
# cf https://www.postgresql.org/docs/current/static/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS
# if this work, we could avoid using to_sql_identifier functions in pymongo-schema and mongoconnector.utils

# The following data dump are not downloaded from ozlerhakan/mongodb-json-files because they are not interesting
# - country.json : the data is in the key names, which makes it difficult to analyze anyway
# - contries.json : very poor, with only one column
for file in \
    city_inspections.json \
    companies.json \
    countries.json \
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



file=primer-dataset.json
if [ ! -e ${file} ]; then
    echo "Downloading file '${file}'"
    wget https://raw.githubusercontent.com/mongodb/docs-assets/primer-dataset/${file} -O restaurant_primer_dataset.json
else
    echo "File '${file}' already exists"
fi