#!/usr/bin/env python
# coding: utf8

# - Clean postgres
# - Initialize postgres

import psycopg2
from sqlalchemy_utils.functions import database_exists, create_database
from utils import wait_for_postgres, mongo_databases_to_map, to_sql_identifier, logger, \
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_ADMIN_USER, POSTGRES_ADMIN_PASSWORD


def main():
    mongo_databases = mongo_databases_to_map()

    wait_for_postgres()
    clean_postgres(mongo_databases)

    # PostgreSQL users are created with a schema to organize data into postgres databases
    postgres_users = [
        'synchro',  # Target of mongoconnector synchronization
        'joined'  # To create denormalize view/tables on 'synchro'
    ]
    init_postgres_users_and_roles(postgres_users)
    init_postgres_databases(mongo_databases, postgres_users)


def clean_postgres(mongo_databases):
    """ Clean Postgres before initialization
    - Stop active connections
    - Drop databases
    - Drop roles in Postgres
    """

    with psycopg2.connect(
            user=POSTGRES_ADMIN_USER,
            password=POSTGRES_ADMIN_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
    ) as con:  # with statement automatically commit changes if no errors occurs
        with con.cursor() as cur:
            con.autocommit = True  # all commands will be immediately committed

            # drop postgres databases
            for mongo_db in mongo_databases:
                postgres_db = to_sql_identifier(mongo_db)
                logger.info("Drop PostgreSQL target database {} if exists".format(postgres_db))

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
                logger.info("Drop role {} ".format(postgres_roles))
                cur.execute("DROP ROLE {};".format(postgres_roles))


def init_postgres_users_and_roles(postgres_users):
    """ Initialize PostgreSQL roles.
    """

    with psycopg2.connect(
        user=POSTGRES_ADMIN_USER,
        password=POSTGRES_ADMIN_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    ) as con:  # with statement automatically commit changes if no errors occurs
        cur = con.cursor()

        logger.info("== Creating PostgreSQL users")
        for user in postgres_users:
            logger.info("  Creating user '{}'".format(user))
            cur.execute("CREATE USER {user};".format(user=user))


def init_postgres_databases(mongo_databases, postgres_users):
    """ Initialize target databases in PostgreSQL
    - Create target database that are not already defined
    - Create postgresql schemas for each non-root user
    """

    for mongo_db in mongo_databases:
        postgres_db = to_sql_identifier(mongo_db)
        target_url = "postgres://{user}:{password}@{host}:{port}/{db}".format(
            user=POSTGRES_ADMIN_USER,
            password=POSTGRES_ADMIN_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            db=postgres_db
        )

        if not database_exists(target_url):
            logger.info("Creating missing target database {}".format(postgres_db))
            create_database(target_url)
            with psycopg2.connect(target_url) as con:  # with statement automatically commit changes if no errors occurs
                cur = con.cursor()

                # Create a schema for every non default user
                cur.execute("DROP SCHEMA public;")
                for user in postgres_users:
                    cur.execute("CREATE SCHEMA IF NOT EXISTS AUTHORIZATION {user};".format(user=user))


if __name__ == "__main__":
    main()
