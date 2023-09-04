#!/usr/bin/env python3

import argparse
import os
import sys

import psycopg
import random

from subprocess import Popen
from fabric import Connection


def dump_src_db_to_file(db_host, db_port, db_user, db_password, db_name, file_name):
    command = f"pg_dump -h {db_host} -p {db_port} -U {db_user} -d {db_name} -c --inserts -f {file_name}"
    my_env = os.environ.copy()
    my_env["PGPASSWORD"] = db_password
    print(f"Exporting from {db_host}:{db_port}/{db_name} to {file_name}... ", end="")
    ret = Popen(command, shell=True, env=my_env).wait()
    print("DONE")
    return ret


def establish_ssh_tunnel(ssh_host, ssh_port, ssh_user, db_host, db_port):
    local_port = random.randint(11000, 12000)
    conn = Connection(host=ssh_host, port=ssh_port, user=ssh_user)
    fw = conn.forward_local(
        local_port=local_port, remote_port=db_port, remote_host=db_host
    )
    return conn, fw, local_port


def load_db_from_file(db_host, db_port, db_user, db_password, db_name, file_name):
    connstr = "host=%s port=%s user=%s password=%s sslmode=disable dbname=%s" % (
        db_host,
        db_port,
        db_user,
        db_password,
        db_name,
    )
    with psycopg.connect(connstr) as conn:
        with conn.cursor() as cur:
            print(
                f"Importing from {file_name} to {db_host}:{db_port}/{db_name}... ",
                end="",
            )
            cur.execute(open(file_name, "rt").read())
            print("DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--src-dbhost", help="DB hostname", default="localhost")
    parser.add_argument("--src-dbport", help="DB port", default=5432, type=int)
    parser.add_argument("--src-dbuser", help="DB username", default="keycloak")
    parser.add_argument("--src-dbpw", help="DB password", required=True)
    parser.add_argument("--src-dbname", help="dbname", default="keycloak")

    parser.add_argument(
        "--dst-file", help="Destination filename", default="keycloak-mirror.sql"
    )

    parser.add_argument("--live-import", help="run the import", action="store_true")

    parser.add_argument("--dst-dbhost", help="DB hostname", default="localhost")
    parser.add_argument("--dst-dbport", help="DB port", default=5432, type=int)
    parser.add_argument("--dst-dbuser", help="DB username", default="keycloak")
    parser.add_argument("--dst-dbpw", help="DB password")
    parser.add_argument("--dst-dbname", help="dbname", default="keycloak")

    parser.add_argument("--ssh-host", help="SSH hostname")
    parser.add_argument("--ssh-port", help="SSH port", default=22, type=int)
    parser.add_argument("--ssh-user", help="SSH user")

    args = parser.parse_args()

    if args.live_import and not args.dst_dbpw:
        print("--dst-dbpw is required if importing", file=sys.stderr)
        sys.exit(2)

    remove_sql_file = False
    if args.dst_dbhost and not args.dst_file:
        remove_sql_file = True

    dst_file = args.dst_file
    if not dst_file:
        dst_file = "keycloak-mirror.sql"

    dump_src_db_to_file(
        args.src_dbhost,
        args.src_dbport,
        args.src_dbuser,
        args.src_dbpw,
        args.src_dbname,
        dst_file,
    )

    if args.live_import:
        try:
            if args.ssh_host:
                dst_dbport = random.randint(11000, 12000)
                print(
                    f"Establishing SSH tunnel from 127.0.0.1:{dst_dbport} to "
                    "{args.ssh_host}->{args.dst_dbhost}:{args.dst_dbport}... ",
                    end="",
                )
                with Connection(
                    host=args.ssh_host, port=args.ssh_port, user=args.ssh_user
                ).forward_local(
                    local_port=dst_dbport,
                    remote_port=args.dst_dbport,
                    remote_host=args.dst_dbhost,
                ):
                    print("DONE")

                    load_db_from_file(
                        args.dst_dbhost,
                        args.dst_dbport,
                        args.dst_dbuser,
                        args.dst_dbpw,
                        args.dst_dbname,
                        dst_file,
                    )
            else:
                load_db_from_file(
                    args.dst_dbhost,
                    args.dst_dbport,
                    args.dst_dbuser,
                    args.dst_dbpw,
                    args.dst_dbname,
                    dst_file,
                )

        finally:
            if args.live_import:
                print(f"Removing {dst_file}... ", end="")
                os.remove(dst_file)
                print("DONE")
