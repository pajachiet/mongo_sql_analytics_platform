#!/usr/bin/env python
# coding: utf8

# - Clean postgres
# - Initialize postgres

import psycopg2
from sqlalchemy_utils.functions import database_exists, create_database
from utils import wait_for_mongo, wait_for_postgres, get_mongo_to_posgres_db_names, logger,\
    MONGO_HOST, MONGO_PORT, FILTERING_NAMESPACES_PATH, get_postgres_url, POSTGRES_USERS



def main():
    mongo_to_posgres_db_names = get_mongo_to_posgres_db_names()

    wait_for_mongo()
    wait_for_postgres()
    clean_postgres(mongo_to_posgres_db_names)
    init_postgres_users_and_roles()
    init_postgres_databases(mongo_to_posgres_db_names)


def clean_postgres(mongo_to_posgres_db_names):
    """ Clean Postgres before initialization
    - Stop active connections
    - Drop databases
    - Drop roles in Postgres
    """
    target_url = get_postgres_url("postgres", '')

    with psycopg2.connect(target_url) as con:  # with statement automatically commit changes if no errors occurs
        with con.cursor() as cur:
            con.autocommit = True  # all the commands executed will be immediately committed

            # drop databases
            for postgres_db in mongo_to_posgres_db_names.values():
                logger.info("Drop target database {} if exists at url {}".format(postgres_db, target_url))

                # terminate active connections to database
                cur.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{}'
                AND pid <> pg_backend_pid();
                """.format(postgres_db))

                cur.execute("DROP DATABASE IF EXISTS {};".format(postgres_db))

            # drop users and roles
            cur.execute("SELECT rolname FROM pg_roles;")
            list_roles = [role for (role,) in cur.fetchall() if not role.startswith('pg_')]
            list_roles.remove("postgres")  # keep default role postgres

            for postgres_roles in list_roles:
                logger.info("Drop role {} at url {}".format(postgres_roles, target_url))
                cur.execute("DROP ROLE {};".format(postgres_roles))


def init_postgres_users_and_roles():
    """ Initialize PostgreSQL roles."""
    postgres_url = get_postgres_url('postgres', 'postgres')

    with psycopg2.connect(postgres_url) as con:  # with statement automatically commit changes if no errors occurs
        cur = con.cursor()

        logger.info("== Creating PostgreSQL users")
        for user in POSTGRES_USERS:
            if user == "postgres":
                pass
            else:
                logger.info("  Creating user '{}'".format(user))
                cur.execute("CREATE USER {user};".format(user=user))


def init_postgres_databases(mongo_to_posgres_db_names):
    """ Initialize target databases in PostgreSQL
    - Create target database that are not already defined
    - Create postgresql schemas for each non-root user
    """

    for postgres_db in mongo_to_posgres_db_names.values():
        target_url = get_postgres_url('postgres', postgres_db)

        if not database_exists(target_url):
            logger.info("Creating missing target database at url {}".format(target_url))
            create_database(target_url)
            with psycopg2.connect(target_url) as con:  # with statement automatically commit changes if no errors occurs
                cur = con.cursor()

                # Create a schema for every non default user
                cur.execute("DROP SCHEMA public;")
                for user in POSTGRES_USERS:
                    if user == 'postgres':
                        continue
                    cur.execute("CREATE SCHEMA IF NOT EXISTS AUTHORIZATION {user};".format(user=user))


if __name__ == "__main__":
    main()
