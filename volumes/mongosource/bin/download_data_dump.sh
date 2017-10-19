#!/usr/bin/env bash
set -euo pipefail

mkdir -p /home/data/dump
cd /home/data/dump

for file in \
    catalog.books.json \
    city_inspections.json \
    companies.json \
    countries.json \
    country.json \
    covers.json \
    grades.json \
    products.json \
    profiles.json \
    restaurant.json \
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
    wget https://raw.githubusercontent.com/mongodb/docs-assets/primer-dataset/${file}
else
    echo "File '${file}' already exists"
fi