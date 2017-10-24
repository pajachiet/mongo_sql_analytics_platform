#!/usr/bin/env python
# coding: utf8

# - Extract mongo schema
# - Generate mongo to postgres mapping

import logging
import os
from pymongo_schema.__main__ import main as pymongo_schema
from utils import wait_for_mongo, logger, MONGO_HOST, MONGO_PORT

WORKING_DIR = '/home/data'


# Initialize pymongo_schema logger
class WarnDatabaseFilter(logging.Filter):
    """ Do not output warning messages when a database is filtered by namespace but absent"""

    def filter(self, record):
        return not record.getMessage().startswith("WARNING : Database")

pymongo_schema_logger = logging.getLogger("pymongo_schema")
pymongo_schema_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.addFilter(WarnDatabaseFilter())
pymongo_schema_logger.addHandler(handler)


def extract_mongo_schemas(mongo_databases):
    """ Extract 'schema_{DB}.json' files, if they do not already exists
    """
    logger.info("== Extract schema for MongoDB databases, if they do not already exists.")
    for mongo_db in mongo_databases:
        schema_path = os.path.join(WORKING_DIR, 'schema_{}'.format(mongo_db))
        schema_path_ext = schema_path + '.json'
        if os.path.isfile(schema_path_ext):
            logger.info("'{}' file already exists. Delete it if you need to update it automatically."
                        .format(schema_path_ext))
        else:
            logger.info("'{}' does not exists. Let's extract it with pymongo-schema".format(schema_path))
            cmd = ["extract", "-o", schema_path, "--database", mongo_db,
                   "--host", MONGO_HOST, "--port", str(MONGO_PORT), "-f", "json", "md"]
            pymongo_schema(cmd)


def generate_mappings(mongo_databases):
    """ Generate mappings from Mongo data model to Postgres relational model
    """
    logger.info("== Filter schema by namespace, then generate 'mapping_DATABASES.json' files for mongo-connector")

    # Clean directory
    for filename in os.listdir(WORKING_DIR):
        if filename.startswith('schema_filtered_') or filename.startswith('mapping_'):
            os.remove(os.path.join(WORKING_DIR, filename))

    for mongo_db in mongo_databases:
        schema_path = '{}/schema_{}.json'.format(WORKING_DIR, mongo_db)
        filtered_schema_path = '{}/schema_filtered_{}'.format(WORKING_DIR, mongo_db)
        mapping_path = '{}/mapping_{}.json'.format(WORKING_DIR, mongo_db)
        filtering_namespace_path = '{}/config.json'.format(WORKING_DIR)

        if os.path.isfile(schema_path):  # Only create mapping when schema exists
            # Filter schemas by namespaces
            cmd = ["transform", schema_path, "--filter", filtering_namespace_path,
                   "-o", filtered_schema_path, "-f",  "md", "json"]
            pymongo_schema(cmd)

            # Generate mapping from filtered schemas
            cmd = ["tosql", filtered_schema_path + '.json', "-o", mapping_path]
            pymongo_schema(cmd)
