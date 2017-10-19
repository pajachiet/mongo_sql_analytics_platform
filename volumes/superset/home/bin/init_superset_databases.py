#!/usr/bin/env python3
# coding: utf8

from use_superset_api import UseSupersetApi
import os

SUPERSET_ADMIN_PASSWD = os.environ.get('SUPERSET_ADMIN_PASSWD')


def init_databases():
    data = {
        "database_name": 'postgres',
        "sqlalchemy_uri": 'postgres://postgres@postgres',
        "expose_in_sqllab": 'y',
        # "cache_timeout": ,
        "extra": """{
    "metadata_params": {},
    "engine_params": {}
}""",
        "allow_run_sync": 'y',
        # "force_ctas_schema": ,
    }

    superset = UseSupersetApi('admin', SUPERSET_ADMIN_PASSWD)
    print(superset.post('databaseview/add', data=data))

if __name__ == "__main__":
    init_databases()
