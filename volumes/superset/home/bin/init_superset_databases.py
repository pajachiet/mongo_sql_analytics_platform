#!/usr/bin/env python3
# coding: utf8

from use_superset_api import UseSupersetApi
import os
import psycopg2
import logging

logger = logging.getLogger('main')
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)

SUPERSET_ADMIN_USERNAME = os.environ.get("SUPERSET_ADMIN_USERNAME")
SUPERSET_ADMIN_PASSWD = os.environ.get('SUPERSET_ADMIN_PASSWD')

def create_all_databases():
    cur = psycopg2.connect("postgresql://postgres@postgres:5432").cursor()
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    db_list = [t[0] for t in cur if t[0] != 'postgres']
    for db in db_list:
        logger.info("Create database '{}' in superset".format(db))
        create_superset_database(db)

def create_superset_database(db_name):
    data = {
        "database_name": db_name,
        "sqlalchemy_uri": 'postgres://synchro@postgres/{}'.format(db_name),
        "expose_in_sqllab": 'y',
        # "cache_timeout": ,
        "extra": """{
    "metadata_params": {},
    "engine_params": {}
}""",
        "allow_run_sync": 'y',
        # "force_ctas_schema": ,
    }

    superset = UseSupersetApi(SUPERSET_ADMIN_USERNAME, SUPERSET_ADMIN_PASSWD)
    print(superset.post('databaseview/add', data=data))

if __name__ == "__main__":
    create_all_databases()
