#!/usr/bin/env python
# coding: utf8

# - Generate mongo-connector config.json
# -  Delete log and timestamp files to reset mongo-connector

import json
import os
from utils import wait_for_mongo, get_mongo_to_posgres_db_names, MONGO_HOST, MONGO_PORT, FILTERING_NAMESPACES_PATH, get_postgres_url
import logging

WORKING_DIR = '/home/generated'
logger = logging.getLogger(__name__)


def main():
    wait_for_mongo()
    mongo_to_posgres_db_names = get_mongo_to_posgres_db_names()
    generate_mongoconnector_config(mongo_to_posgres_db_names)
    reset_mongo_connector()


def generate_mongoconnector_config(mongo_to_posgres_db_names):
    """ Generate 'config.json'
    """
    logger.info("Generating mongo-connector 'config.json' file")

    output_config = dict()
    output_config["mainAddress"] = "{}:{}".format(MONGO_HOST, MONGO_PORT)
    with open(FILTERING_NAMESPACES_PATH, 'r') as local_config_file:
        output_config["namespaces"] = json.load(local_config_file)["namespaces"]
    output_config["logging.filename"] = "mongo-connector.log"
    output_config["oplogFile"] = "oplog.timestamp"

    output_config["docManagers"] = []
    for postgres_db in mongo_to_posgres_db_names.values():
        doc_manager_config = dict()
        doc_manager_config["docManager"] = "postgresql_manager"
        doc_manager_config["targetURL"] = get_postgres_url('synchro', postgres_db)
        doc_manager_config["args"] = {
            "mongoUrl": "mongodb://{}:{}".format(MONGO_HOST, MONGO_PORT),
            "mappingFile": "mapping_{}.json".format(postgres_db)
        }
        output_config["docManagers"].append(doc_manager_config)


    with open(WORKING_DIR + "/config.json", 'w') as config_file:
        json.dump(output_config, config_file, indent=4)


def reset_mongo_connector():
    """ Delete log and timestamp files to reset mongo-connector
    """
    for filename in [ '/oplog.timestamp', 'mongo-connector.log']:
        if os.path.exists(filename):
            logger.info("Removing {}".format(filename))
            os.remove(filename)

if __name__ == "__main__":
    main()
