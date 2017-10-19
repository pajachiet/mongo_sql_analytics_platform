#!/usr/bin/env bash
set -euo pipefail

echo "Start Mongo with a replicat set"
mkdir -p /home/data/db
/usr/bin/mongod --port 27017 --dbpath /home/data/db --replSet rs0 &

echo "Waiting until MongoDB accepts connexions"
connectMO="curl -s -o /dev/null -w '%{http_code}' http://localhost:27017 | sed 's/[^0-9]*//g'"
until [[ $(eval $connectMO) -eq "200" ]] ; do
  printf '.'
  sleep 1
done

echo "Initialisation of replicat set in mongosource"
echo 'rs.initiate();' | mongo

tail -F -n0 /etc/hosts