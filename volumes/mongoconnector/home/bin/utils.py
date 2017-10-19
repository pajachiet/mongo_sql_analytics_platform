#!/usr/bin/env python
# coding: utf8

import sys
import pymongo
import psycopg2
from time import sleep

import logging

MONGO_HOST = "mongosource"
MONGO_PORT = 27017
FILTERING_NAMESPACES_PATH = '/home/filtering_namespaces.json'
POSTGRES_USERS = ['postgres', 'synchro', 'joined']

logger = logging.getLogger('main')
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)


def test_connection_to_mongo():
    """ Test if the source MongoDB database accept connexions
    """
    try:
        client = pymongo.MongoClient(host=MONGO_HOST, port=MONGO_PORT, serverSelectionTimeoutMS=1000)
        client.server_info()
    except pymongo.errors.ServerSelectionTimeoutError:
        return False
    else:
        return True


def wait_for_mongo():
    if test_connection_to_mongo():
        return

    logger.info("\nWaiting until MongoDB accept connexions")
    while not test_connection_to_mongo():
        sys.stdout.write('.')
        sys.stdout.flush()
        sleep(1)
    logger.info('ok')


def wait_for_postgres():
    if test_connection_to_postgresql():
        return
    logger.info("\nWaiting until PostgreSQL accept connexions")
    while not test_connection_to_postgresql():
        sys.stdout.write('.')
        sys.stdout.flush()
        sleep(1)
    logger.info('ok')


def test_connection_to_postgresql():
    """ Test if the target PostgreSQL database accept connexions
    """
    try:
        psycopg2.connect(get_postgres_url('postgres', 'postgres'))
    except psycopg2.OperationalError:
        return False
    else:
        return True


def get_mongo_to_posgres_db_names():
    """ Generate the mapping of mongo databases names to postgres databases names
    """
    client = pymongo.MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    mongo_databases = client.database_names()
    mongo_databases.remove('admin')
    mongo_databases.remove('local')

    mongo_to_posgres_db_names = dict()
    for mongo_db in mongo_databases:
        mongo_to_posgres_db_names[mongo_db] = mongo_db.replace('-', '_')

    return mongo_to_posgres_db_names


def get_postgres_url(user, database):
    """ Return url to connect to PostgreSQL

    :param user:
    :param database:
    :return: postgres_url
    """
    postgres_url = "postgresql://{}@postgres:5432/{}".format(user, database)
    return postgres_url
