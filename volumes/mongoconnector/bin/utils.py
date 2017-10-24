#!/usr/bin/env python
# coding: utf8

import os
import json
import sys
import pymongo
import psycopg2
from time import sleep

import logging

logger = logging.getLogger('main')
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)

MONGO_HOST = os.environ.get('MONGO_HOST')
MONGO_PORT = int(os.environ.get('MONGO_PORT'))
POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT'))
POSTGRES_ADMIN_USER = os.environ.get('POSTGRES_ADMIN_USER')
POSTGRES_ADMIN_PASSWORD = os.environ.get('POSTGRES_ADMIN_PASSWORD')


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
        psycopg2.connect(
            user=POSTGRES_ADMIN_USER,
            password=POSTGRES_ADMIN_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
    except psycopg2.OperationalError:
        return False
    else:
        return True


def mongo_databases_to_map():
    """ List databases to map from MongoDB
    
    If namespaces is not empty, only work on databases defined in namespaces
    Otherwise list all non default databases present in MongoDB
    """

    with open("/home/conf/namespaces.json", 'r') as namespaces_file:
        namespaces = json.load(namespaces_file)

    if namespaces:
        mongo_databases = set()
        for key in namespaces.keys():
            db, col = key.split(':', 1)
            mongo_databases.add(db)
        return list(mongo_databases)
    else:
        client = pymongo.MongoClient(host=MONGO_HOST, port=MONGO_PORT)
        mongo_databases = client.database_names()
        mongo_databases.remove('admin')
        mongo_databases.remove('local')
        return mongo_databases


def get_target_url(mongo_db):
    postgres_db = to_sql_identifier(mongo_db)
    target_url = "postgresql://synchro@{host}:{port}/{postgres_db}".format(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        postgres_db=postgres_db
    )
    return target_url


def to_sql_identifier(mongo_identifier):
    return mongo_identifier.replace('-', '_')

