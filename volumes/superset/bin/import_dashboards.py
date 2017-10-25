#!/usr/bin/env python3
# coding: utf8

# Import dashboards pickle files in Superset

import os
from use_superset_api import UseSupersetApi

DASHBOARDS_DIR = "/etc/superset/dashboards/"


def main():
    import_superset_dashboards()


def import_superset_dashboards():
    """ Import latest dashboard.
    """
    superset = UseSupersetApi()  # superset/import_dashboards is accessible to anyone without authentification
    for dashboard_filename in os.listdir(DASHBOARDS_DIR):
        if not dashboard_filename.endswith('.pickle'):
            continue

        print("Importing dashboard from file {}".format(dashboard_filename))
        files = [('file', open(DASHBOARDS_DIR + dashboard_filename, 'rb'))]
        superset.post('superset/import_dashboards', files=files)

if __name__ == "__main__":
    main()
