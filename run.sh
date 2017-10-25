#!/usr/bin/env bash
set -euo pipefail

#### USAGE and ARGUMENT CHECKING
usage()
{
  echo "'run.sh' helps you to run the Mongo -> SQL analytics platform

Usage:
  run.sh install
  run.sh restore
  run.sh connector
  run.sh superset
  run.sh schemacrawler
  run.sh stop
  run.sh reset
  run.sh -h|--help

Options:
  -h, --help    Display usage and exit

Commands:
  demo              Run 'install', download demo data, then run 'restore', 'connector' and 'superset'
  install           Initiate '.env' file. Pull / build all Docker images if they have changed.
  restore           Download and restore dump into mongosource. Then run 'connector' and 'superset'
  connector         Launch synchronisatino between mongosource and postgres through mongoconnector. Then run 'superset'
  superset          Start Superset
  sqlschema db      Extract SQL Schema of database 'db'
  stop              Stop services
  reset [service]   Reset all services, or selected service. Ie remove volumes data and containers
"
  exit
}
if [ -z ${1+x} ]
then
  echo "Incorrect usage."; usage
fi

case $1 in
    demo | install | restore | connector | superset | sqlschema | stop  | reset ) ;; #Ok, nothing needs to be done
    -h | --help ) usage;;
    * ) echo "Incorrect usage."; usage ;;
esac


#### DEMO
if [ $1 == "demo" ]
then
   ./run.sh install
   docker-compose up -d mongosource
   docker-compose exec -T mongosource sh -c "/home/bin/download_demo_data_dump.sh"
   ./run.sh restore
   ./run.sh connector
   ./run.sh superset
   docker-compose exec -T superset sh -c  "/etc/superset/bin/import_dashboards.py"
   ./run.sh sqlschema
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

# RESTORE
if [ $1 == "restore" ]
then

    echo "== Restauring data in MongoDB source"

    # Ask if we want to delete existing MongoDB schema, to make mongoconnector automatically extract new ones
    if [ -d volumes/mongoconnector/data ]; then
        cd volumes/mongoconnector/data
        if [ ! -z "$(ls  | grep schema | grep -v schema_filtered)" ]; then
            while true; do
                echo "MongoDB schemas already exists from previous run:"
                echo `ls  | grep schema | grep -v schema_filtered | tr ' ' '\n'`
                echo
                echo "If you restore data with a different schema, we should delete existing schemas."
                echo "This will force mongoconnector to automatically extract new schemas with pymongo-schema."
                read -p  "Do you want to delete existing MongoDB schemas? [y|n] " yn
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
        cd ../../..
    fi

    #TODO: Following commented lines are useless for '.json' files. To be tested with bson dumps
    #docker-compose stop mongosource
    #echo "Delete existing data in MongoDB source"
    #rm -rf volumes/mongosource/data/db

    docker-compose up -d mongosource
    echo "Waiting until MongoDB accepts connexions"
    connectMO="docker-compose exec -T mongosource bash -c \"curl -s -o /dev/null -w '%{http_code}' http://mongosource:27017\" | sed 's/[^0-9]*//g'"
    until [[ $(eval $connectMO) -eq "200" ]] ; do
          printf '.'
          sleep 1
    done

    docker-compose exec -T mongosource sh -c "/home/bin/restore_data_dump.sh"
    exit
fi


### CONNECTOR
if [ $1 == "connector" ]
then
    docker-compose stop mongoconnector
    echo "== Run mongo-connector : "
    echo "generate config.json and mapping_{DB}.json files, destroy and init PostgreSQL target databases, then sync MongoDB source with PostgreSQL"
    docker-compose up -d mongoconnector
    echo "You can follow synchronization logs by running 'docker-compose logs --follow mongoconnector'"
    echo "You can also look at logs in 'volumes/mongoconnector/data/mongo-connector.log'"
    exit
fi

### SUPERSET
if [ $1 == "superset" ]
then
    echo "== Starts and initialize Superset"
    docker-compose up -d superset
    docker-compose exec  superset sh -c "/etc/superset/bin/init_superset.sh" > volumes/superset/data/init_logs
    echo "Superset is up at : http://localhost:8088"
    exit
fi

### SCHEMACRAWLER
if [ $1 == "sqlschema" ]
then
    if [ $# = 1 ]; then
        echo "You should give as additional parameter the name of the database you want to extract"
        exit
    fi
    DATABASE=${2}
    echo "== Starting SchemaCrawler, to extract a relational schema for database ${DATABASE}"
    docker-compose run sqlschema /schemacrawler/bin/extract_sql_schema.sh ${2}
    echo "The SQL schema is available in folder volumes/sqlschema/data."
    exit
fi


#### STOP
if [ $1 == "stop" ]
then
    echo "== Stopping services of the Mongo -> SQL analytics platform..."
    docker-compose stop
    echo "Services are stopped. Goodbye !"
    exit
fi


#### RESET
if [ $1 == "reset" ]
then
    if [ $# = 1 ]; then
        service=all
    else
        service=$2
    fi

    case ${service} in
        all | mongosource | mongoconnector | postgres | superset | redis | sqlschema ) ;; #Ok, nothing needs to be done
        * ) echo "Incorrect usage. We can only reset one of the following service : mongosource, mongoconnector, postgres, sqlschema, superset or redis"; exit;;
    esac

    while true; do
        if [ ${service} == "all" ];
        then
            echo "This WILL DELETE ALL DATA and CONTAINERS of ALL services : mongosource, mongoconnector, postgres, sqlschema, superset & redis."
        else
            echo "This WILL DELETE ALL DATA and CONTAINER of service ${service}."
        fi
        read -p "Are you sure? [y|n] : " yn
        case $yn in
            [Yy]* ) echo "yes"; break;;
            [Nn]* ) echo "Abort"; exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done

    if [ ${service} == "all" ];
    then
        docker-compose stop
        cd volumes
            rm -rf */data
        cd ..
        yes | docker-compose rm
    else
        docker-compose stop ${service}
        rm -rf volumes/${service}/data
        yes | docker-compose rm ${service}
    fi
    exit
fi

