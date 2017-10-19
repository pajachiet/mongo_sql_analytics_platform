#!/usr/bin/env python
# coding: utf8

# Script to print if databases are synchronized

from utils import wait_for_mongo, wait_for_postgres, logger
import pymongo
import psycopg2
from time import sleep
import json


# Read config file and define connection variables
with open("/home/generated/config.json", 'r') as config_file:
    config = json.load(config_file)
MONGO_URL = config['mainAddress']
if not MONGO_URL.startswith('mongodb://'):
    MONGO_URL = 'mongodb://' + MONGO_URL

POSTGRES_URLS = []
MAPPINGS_NAMES = []
for doc_manager in config['docManagers']:
    doc_manager_mongo_url = doc_manager['args'].get('mongoUrl')
    assert doc_manager_mongo_url == MONGO_URL, \
        "Main Mongo URL '{}' is different from Mongo URL in doc manager '{}'".format(doc_manager_mongo_url, MONGO_URL)
    POSTGRES_URLS.append(doc_manager['targetURL'])
    MAPPINGS_NAMES.append(doc_manager['args'].get('mappingFile', 'mappings.json'))


def main():
    wait_for_mongo()
    wait_for_postgres()

    print_mongodb_collections_infos()
    sleep(5)
    while True:
        logger.info("\nWriting synchronization status between mongo and postgresql every 20 seconds.")
        if test_synchronisation_mongo_postgresql():
            break
        sleep(20)

    print_postgres_tables_infos()


def print_mongodb_collections_infos():
    """Print infos on MongoDB collections : document count, storage size
    """
    client = pymongo.MongoClient(MONGO_URL)
    database_names = client.database_names()
    database_names.remove('admin')
    database_names.remove('local')

    output_str = "  {0:25} {1:>10}  {2}"
    for db_name in database_names:
        db = client[db_name]

        logger.info(u"\nState of MongoDB database '{}'".format(db_name))

        logger.info(output_str.format("Collection", "Count", "Storage"))
        total_size = 0
        for collection_name in sorted(db.collection_names()):
            stat = db.command('collStats', collection_name)
            count = stat['count']
            size = stat['storageSize']
            total_size += size
            logger.info(output_str.format(collection_name, count, sizeof_fmt(size)))

        logger.info("Total size:\t{}".format(sizeof_fmt(total_size)))


def print_postgres_tables_infos():
    """Print infos on PostgreSQL database : document count, storage size
    """
    output_str = "  {0:60} {1:>10}  {2}"
    for postgres_url in POSTGRES_URLS:
        cur = psycopg2.connect(postgres_url).cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'synchro';")
        table_list = [t[0] for t in cur]

        pg_db = postgres_url.split('/')[-1]
        logger.info(u"\nState of PostgreSQL database " + pg_db)

        logger.info(output_str.format("Table", "Count", "Storage"))
        total_size = 0
        for table_name in sorted(table_list):
            query = "SELECT count(*) FROM {}".format(table_name)
            cur.execute(query)
            count = cur.fetchone()[0]

            query = "SELECT pg_table_size('synchro.{}');".format(table_name)
            cur.execute(query)
            size = cur.fetchone()[0]
            total_size += size
            logger.info(output_str.format(table_name, count, sizeof_fmt(size)))

        logger.info("\nTotal size:\t{}".format(sizeof_fmt(total_size)))


def test_synchronisation_mongo_postgresql(verbose=True):
    output_str = "  {0:25} {1:25} {2:>20}  {3:>20}"
    synchronization = True
    client = pymongo.MongoClient(MONGO_URL)
    for postgres_url, mapping_name in zip(POSTGRES_URLS, MAPPINGS_NAMES):

        cur = psycopg2.connect(postgres_url).cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'synchro';")
        table_list = [t[0] for t in cur]

        with open('/home/generated/' + mapping_name, 'r') as mapping_file:
            mapping = json.load(mapping_file)

        for mongo_database_name, db_mapping in mapping.items():
            mongodb = client[mongo_database_name]
            for collection_name in mongodb.collection_names():
                # Do not test synchronization for certain collections
                if collection_name not in db_mapping:
                    if verbose:
                        logger.warning("    collection '{}' present in MongoDB database '{}' is not mapped"\
                              .format(collection_name, mongo_database_name))
                    continue

                namespace = mongo_database_name + '.' + collection_name
                if 'namespaces' in config and not config['namespaces'].get(namespace, True):
                    if verbose:
                        logger.warning("    collection '{}' is ignored in doc_manager namespaces configuration.".format(collection_name))
                    continue

                # MongoDB count
                mongo_count = mongodb[collection_name].count()

                # PostgresSQL count
                query = "SELECT count(*) FROM {}".format(collection_name)
                if collection_name not in table_list:
                    psql_count = 'not defined'
                else:
                    cur.execute(query)
                    psql_count = cur.fetchone()[0]

                # Test synchronization
                if mongo_count != psql_count:
                    if synchronization:
                        synchronization = False
                        if verbose:
                            logger.info("\nPostgreSQL is not synchronized with MongoDB on the following collections:")
                            logger.info(output_str.format("Database", "Collection", "MongoDB_count", "PostgreSQL_count"))
                    if verbose:
                        logger.info(output_str.format(mongo_database_name, collection_name, mongo_count, psql_count))

    if synchronization and verbose:
        logger.info("\nPostgreSQL is synchronized on MongoDB on dabasases and collection definded in the mapping.")
    return synchronization


def sizeof_fmt(num):
    """Format the size of a file from bytes to human readable
    adapted from http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s" % (num, unit)
        num /= 1024.0
    return "%.1f%s" % (num, 'Yi')


if __name__ == "__main__":
    main()
