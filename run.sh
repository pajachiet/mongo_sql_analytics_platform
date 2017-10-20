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
  demo          Run successively 'install', 'init_superset' and 'restore'
  install       Initiate '.env' file. Pull / build all Docker images if they have changed.
  reset         Remove all volume data from containers
  restore       Download and restore dump into mongosource. Then run 'connector' and 'superset'
  connector     Launch synchronisatino between mongosource and postgres through mongoconnector. Then run 'superset'
  superset      Start Superset
  stop          Stop services
"
  exit
}
if [ -z ${1+x} ]
then
  echo "Incorrect usage."; usage
fi

case $1 in
    demo | install | reset | restore | connector | superset | stop ) ;; #Ok, nothing needs to be done
    -h | --help ) usage;;
    * ) echo "Incorrect usage."; usage ;;
esac


#### DEMO
if [ $1 == "demo" ]
then
   ./run.sh install
   ./run.sh restore
   exit
fi


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
        rm -f  superset/home/superset.db
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

    cd volumes/mongosource
        echo "Deleting data from MongoDB source"
        rm -rf data/db
        rm -rf log

        echo "Deleting 'metatadata.json' files from dump, as we do not need indexes and they may cause errors."
        rm -rf dump/*/*.metadata.json
    cd ../..

    if [ -d volumes/mongoconnector/home/generated ]; then
        cd volumes/mongoconnector/home/generated
        if [ ! -z "$(ls  | grep schema | grep -v schema_filtered)" ]; then
            while true; do
                echo "MongoDB schemas already exists from previous run:"
                echo `ls  | grep schema | grep -v schema_filtered | tr ' ' '\n'`
                echo
                echo "Extracting schema from MongoDB takes times, but must be done if your MongoDB data changes."
                read -p  "Do you want to delete existing MongoDB schemas and extract new ones ? [y|n] " yn
                case $yn in
                    [Yy]* )
                      echo "Delete existing schemas : ";
                      echo
                      ls  | grep schema | grep -v schema_filtered
                      rm -rf schema_*
                      break;;
                    [Nn]* )
                      echo "Going on with existing schemas :";
                      break;;
                    * ) echo "Please answer yes or no.";;
                esac
            done
        fi
        cd ../../../..
    fi

    docker-compose stop mongosource
    docker-compose up -d mongosource
    docker-compose exec -T mongosource sh -c "/home/bin/download_data_dump.sh"

    echo "Waiting until MongoDB accepts connexions"
    connectMO="docker-compose exec -T mongosource bash -c \"curl -s -o /dev/null -w '%{http_code}' http://mongosource:27017\" | sed 's/[^0-9]*//g'"
    until [[ $(eval $connectMO) -eq "200" ]] ; do
          printf '.'
          sleep 1
    done

    docker-compose exec -T mongosource sh -c "/home/bin/restore_data_dump.sh"
    ./run.sh connector
    exit
fi


### CONNECTOR
if [ $1 == "connector" ]
then
    docker-compose stop mongoconnector

    echo "Starting Mongo-connector, sync MongoDB source with PostgreSQL, create additional objects in Postgres"
    docker-compose up -d mongoconnector
    ./run.sh superset
    exit
fi

### SUPERSET
if [ $1 == "superset" ]
then
    docker-compose up -d superset
    docker-compose exec  superset sh -c "/etc/superset/bin/init_superset.sh" > volumes/superset/init_logs
    echo "Superset is up at : http://localhost:8088"
    exit
fi