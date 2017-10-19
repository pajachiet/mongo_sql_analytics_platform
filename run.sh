#!/usr/bin/env bash
set -euo pipefail

#### USAGE and ARGUMENT CHECKING
usage()
{
  echo "'lake.sh' facilite la manipulation du datalake de développement du SI AEF

Usage:
  run.sh install
  run.sh reset
  run.sh restore
  run.sh connector
  run.sh front
  run.sh stop
  lake.sh -h|--help

Options:
  -h, --help    Display usage and exit

Commands:
  install       Initiate '.env' file. Pull / build all Docker images if they have changed.
  reset         Remove all volume data from containers
  init_superset Run superset initialization (create users, databases, roles, import dashboards)
  restore       Download and restore dump into mongosource. Then run 'connector' and 'superset'
  connector     Launch synchronisatino between mongosource and postgres through mongoconnector. Then run 'superset'
  superset      Start Superset
  stop          Stop services  test          Start the entire datalake pipeline and execute non-regression tests
"
  exit
}
if [ -z ${1+x} ]
then
  echo "Incorrect usage."; usage
fi

case $1 in
    install | init_superset | reset | restore | connector | superset | stop ) ;; #Ok, nothing needs to be done
    -h | --help ) usage;;
    * ) echo "Incorrect usage."; usage ;;
esac


#### INSTALL
if [ $1 == "install" ]
then
    if [ ! -f .env ]; then
        echo "Create '.env' file, based on template. You should modify environment values in this file."
        cp env_template .env
    else
        echo "'.env' file already exists. We do not modify it."
    fi

    docker-compose pull
    docker-compose build

    docker-compose up -d superset
    docker-compose exec -T superset sh -c "/etc/superset/bin/init_superset.sh"
   exit
fi


#### RESET
if [ $1 == "reset" ]
then
    while true; do
      echo "RESET WILL DELETE ALL DATA in mongosource, mongoconnector, postgres and superset"
      read -p "Are you sure? You can copy paste code [y|n] : " yn
      case $yn in
          [Yy]* ) echo "yes"; break;;
          [Nn]* ) echo "Abandon"; exit;;
          * ) echo "Please answer yes or no.";;
      esac
    done
    docker-compose stop

    cd volumes
        rm -rf mongosource/data/dump
        rm -rf mongosource/data/db
        rm -rf mongosource/log
        rm -rf mongoconnector/home/generated
        rm -rf postgres/data
        rm -f  superset/home/bin/superset.db
    cd ..
    exit
fi


#### STOP
if [ $1 == "stop" ]
then
    echo "Stopping services of the datalake..."
    docker-compose stop
    echo "Datalake stopped. Goodbye !"
    exit
fi


# RESTORE
if [ $1 == "restore" ]
then
    docker-compose stop

    cd volumes/mongosource
        echo "Deleting data from MongoDB source"
        rm -rf data/db
        rm -rf log

        echo "Deleting 'metatadata.json' files from dump, as we do not need indexes and they may cause errors."
        rm -rf dump/*/*.metadata.json
    cd ../..

    docker-compose up -d mongosource
    docker-compose exec -T mongosource sh -c "/home/bin/download_data_dump.sh"

    echo "Waiting until MongoDB accepts connexions"
    connectMO="docker-compose exec -T mongosource bash -c \"curl -s -o /dev/null -w '%{http_code}' http://mongosource:27017\" | sed 's/[^0-9]*//g'"
    until [[ $(eval $connectMO) -eq "200" ]] ; do
          printf '.'
          sleep 1
    done

    docker-compose exec -T mongosource sh -c "/home/bin/restore_data_dump.sh"
fi



### CONNECTOR
if [ $1 == "connector" ] || [ $1 == "restore" ]
then
  docker-compose stop mongoconnector

  echo "Starting Mongo-connector, sync MongoDB source with PostgreSQL, create additional objects in Postgres"
  docker-compose up -d mongoconnector

fi

### SUPERSET
if [ $1 == "connector" ] || [ $1 == "restore" ] || [ $1 == "superset" ]
then
  docker-compose up -d superset

  echo "Waiting until Superset is up"
  connectSU="curl --no-proxy localhost:8088/health -s -o /dev/null -w '%{http_code}' http://localhost:8088/health | sed 's/[^0-9]*//g'"
  until [[ $(eval $connectSU) -eq "200" ]] ; do
    printf '.'
    sleep 1
  done
  echo "Superset is up at : http://localhost:8088"
  echo
fi