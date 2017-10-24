#!/usr/bin/env python
# coding: utf8

# - Generate mongo-connector config.json
# -  Delete log and timestamp files to reset mongo-connector

import json
import os
from utils import logger, wait_for_mongo, get_target_url, mongo_databases_to_map, MONGO_HOST, MONGO_PORT
from pymongo_schema_utils import extract_mongo_schemas, generate_mappings


def main():
    wait_for_mongo()
    mongo_databases = mongo_databases_to_map()

    generate_mongoconnector_config(mongo_databases)
    extract_mongo_schemas(mongo_databases)
    generate_mappings(mongo_databases)
    reset_mongo_connector()



def generate_mongoconnector_config(mongo_databases):
    """ Generate 'config.json'
    """
    logger.info("== Generating mongo-connector 'config.json' file")

    output_config = dict()
    output_config["logging.filename"] = "mongo-connector.log"
    output_config["oplogFile"] = "oplog.timestamp"
    output_config["mainAddress"] = "{}:{}".format(MONGO_HOST, MONGO_PORT)
    output_config["namespaces"] = get_or_generate_namespaces(mongo_databases)
    output_config["docManagers"] = []
    for mongo_db in mongo_databases:
        output_config["docManagers"].append(generate_doc_manager_config(mongo_db))

    with open("/home/data/config.json", 'w') as config_file:
        json.dump(output_config, config_file, indent=2)

    return output_config


def get_or_generate_namespaces(mongo_databases):
    with open("/home/conf/namespaces.json", 'r') as namespaces_file:
        namespaces = json.load(namespaces_file)

    # If namespaces is empty, take all collections of every database
    if not namespaces:
        namespaces = dict()
        for db in mongo_databases:
            namespaces['{}.*'.format(db)] = True

    return namespaces


def generate_doc_manager_config(mongo_db):
    doc_manager_config = dict()
    doc_manager_config["docManager"] = "postgresql_manager"

    doc_manager_config["targetURL"] = get_target_url(mongo_db)
    doc_manager_config["args"] = {
        "mongoUrl": "mongodb://{}:{}".format(MONGO_HOST, MONGO_PORT),
        "mappingFile": "mapping_{}.json".format(mongo_db)
    }
    return doc_manager_config


def reset_mongo_connector():
    """ Delete log and timestamp files to reset mongo-connector
    """
    for filename in ['oplog.timestamp', 'mongo-connector.log']:
        file_path = '/home/data/' + filename
        if os.path.exists(file_path):
            logger.info("Removing {}".format(filename))
            os.remove(file_path)

if __name__ == "__main__":
    main()
