#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# TODO derive this from config
database_url="postgresql://test-user:password@localhost:5432/test-db"
psql_command="psql ${database_url}"

does_test_data_exist () {
    query_result=$(${psql_command} -t -c "select count(*) from test_table_1 where key_column = 'test_key_1';" | head -1 | tr -d ' ')
    if [[ "${query_result}" == "1" ]]; then
        return 0
    else
        return 1
    fi
}

create_test_data () {
    ${psql_command} -c "create table test_table_1 (key_column text, value_column text, primary key(key_column));"
    ${psql_command} -c "insert into test_table_1 values ('test_key_1', 'test_value_1');"
}

wait_forever() {
    # Loop to keep docker/k8s happy since this is the container entrypoint
    while :; do sleep 600; done
}

# Check if the test database content exists already
if does_test_data_exist; then
    # If so, log saying so. Test harness will look for this log output
    echo "Database test client: test data already exists"
else
    # Otherwise log saying the content was not present
    echo "Database test client: test data does not exist"
    echo "Database test client: creating test data"
    # then create it
    create_test_data
fi

wait_forever
