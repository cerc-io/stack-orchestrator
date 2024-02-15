#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# TODO derive this from config
database_url="postgresql://test-user:password@localhost:5432/test-db"
psql_command="psql ${database_url}"
program_name="Database test client:"

wait_for_database_up () {
    for i in {1..50}
    do
        ${psql_command} -c "select 1;"
        psql_succeeded=$?
        if [[ ${psql_succeeded} == 0 ]]; then
            # if ready, return
            echo "${program_name} database up"
            return
        else
            # if not ready, wait
            echo "${program_name} waiting for database: ${i}"
            sleep 5
        fi
    done
    # Timed out, error exit
    echo "${program_name} waiting for database: FAILED"
    exit 1
}

# Used to synchronize with the test runner
notify_test_complete () {
    echo "${program_name} test complete"
}

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

wait_for_database_up

# Check if the test database content exists already
if does_test_data_exist; then
    # If so, log saying so. Test harness will look for this log output
    echo "${program_name} test data already exists"
else
    # Otherwise log saying the content was not present
    echo "${program_name} test data does not exist"
    echo "${program_name} creating test data"
    # then create it
    create_test_data
fi

notify_test_complete
wait_forever
