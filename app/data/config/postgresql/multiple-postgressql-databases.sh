#!/bin/bash

set -e
set -u

function create_user_and_database() {
	local database=$1
	echo "  Creating user and database '$database'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE DATABASE "$database";
	    GRANT ALL PRIVILEGES ON DATABASE "$database" TO $POSTGRES_USER;
EOSQL
}

function create_extension() {
	local database=$(echo $1 | tr ':' ' ' | awk  '{print $1}')
	local extension=$(echo $1 | tr ':' ' ' | awk  '{print $2}')
	echo "  Creating database '$database' extension '$extension'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" "$database" <<-EOSQL
	    CREATE EXTENSION "$extension";
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
		create_user_and_database $db
	done
	echo "Multiple databases created"
fi

if [ -n "$POSTGRES_EXTENSION" ]; then
	echo "Extension database creation requested: $POSTGRES_EXTENSION"
	for db in $(echo $POSTGRES_EXTENSION | tr ',' ' '); do
		create_extension $db
	done
	echo "Extensions created"
fi
