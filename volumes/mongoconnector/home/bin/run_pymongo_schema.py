#!/usr/bin/env python
# coding: utf8

# - Extract mongo schema
# - Generate mongo to postgres mapping

import logging
import os
from pymongo_schema.__main__ import main as pymongo_schema
from utils import wait_for_mongo, get_mongo_to_posgres_db_names, MONGO_PORT, MONGO_HOST, FILTERING_NAMESPACES_PATH

WORKING_DIR = '/home/generated'
logger = logging.getLogger(__name__)


def main():
    wait_for_mongo()

    initialize_pymongo_schema_logger()
    mongo_to_posgres_db_names = get_mongo_to_posgres_db_names()
    extract_mongo_schemas(mongo_to_posgres_db_names)
    generate_mappings(mongo_to_posgres_db_names)


def initialize_pymongo_schema_logger():
    class WarnDatabaseFilter(logging.Filter):
        """ Do not output warning messages when a database is filtered by namespace but absent"""

        def filter(self, record):
            return not record.getMessage().startswith("WARNING : Database")

    pymongo_schema_logger = logging.getLogger("pymongo_schema")
    pymongo_schema_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.addFilter(WarnDatabaseFilter())
    pymongo_schema_logger.addHandler(handler)


def extract_mongo_schemas(mongo_to_posgres_db_names):
    """ Extract 'schema_{DB}.json' files, if they do not already exists
    """
    logger.info("Extract schema for MongoDB databases, if they do not already exists.")
    for mongo_db in mongo_to_posgres_db_names:
        schema_path = os.path.join(WORKING_DIR, 'schema_{}.json'.format(mongo_db))
        if os.path.isfile(schema_path):
            logger.info("'{}' file already exists. Delete it if you need to update it automatically.".format(mongo_db))
        else:
            logger.info("'{}' does not exists. Let's extract it with pymongo-schema".format(schema_path))
            cmd = ["extract", "-o", schema_path, "--database", mongo_db,
                   "--host", MONGO_HOST, "-f", "json"]
            pymongo_schema(cmd)


def generate_mappings(mongo_to_posgres_db_names):
    """ Generate mappings from Mongo data model to Postgres relational model
    """
    logger.info("Filter schema by namespace, then generate 'mapping_DATABASES.json' files for mongo-connector")

    # Clean directory
    for filename in os.listdir(WORKING_DIR):
        if filename.startswith('schema_filtered_') or filename.startswith('mapping_'):
            os.remove(os.path.join(WORKING_DIR, filename))

    for mongo_db, postgres_db in mongo_to_posgres_db_names.items():
        schema_path = '{}/schema_{}.json'.format(WORKING_DIR, mongo_db)
        filtered_schema_path = '{}/schema_filtered_{}'.format(WORKING_DIR, mongo_db)
        mapping_path = '{}/mapping_{}.json'.format(WORKING_DIR, mongo_db)

        if os.path.isfile(schema_path):  # Only create mapping when schema exists
            # Filter schemas by namespaces
            cmd = ["transform", schema_path, "--filter", FILTERING_NAMESPACES_PATH,
                   "-o", filtered_schema_path, "-f",  "md", "json"]
            pymongo_schema(cmd)

            # Generate mapping from filtered schemas
            cmd = ["tosql", filtered_schema_path + '.json', "-o", mapping_path]
            pymongo_schema(cmd)


if __name__ == "__main__":
    main()
