#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
# Dump environment variables for debugging
echo "Environment variables:"
env

delete_cluster_exit () {
    $TEST_TARGET_SO deployment --dir $test_deployment_dir stop --delete-volumes
    exit 1
}

# Test basic stack-orchestrator deploy
echo "Running stack-orchestrator deploy test"

if [ "$1" == "from-path" ]; then
    TEST_TARGET_SO="laconic-so"
else
    TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
fi

# Set a non-default repo dir
export CERC_REPO_BASE_DIR=~/stack-orchestrator-test/repo-base-dir
echo "Testing this package: $TEST_TARGET_SO"
echo "Test version command"
reported_version_string=$( $TEST_TARGET_SO version )
echo "Version reported is: ${reported_version_string}"
echo "Cloning repositories into: $CERC_REPO_BASE_DIR"
rm -rf $CERC_REPO_BASE_DIR
mkdir -p $CERC_REPO_BASE_DIR
# Test bringing the test container up and down
# with and without volume removal
$TEST_TARGET_SO --stack test setup-repositories
$TEST_TARGET_SO --stack test build-containers

# Test deploy command execution
$TEST_TARGET_SO --stack test deploy setup $CERC_REPO_BASE_DIR
# Check that we now have the expected output directory
container_output_dir=$CERC_REPO_BASE_DIR/container-output-dir
if [ ! -d "$container_output_dir" ]; then
    echo "deploy setup test: output directory not present"
    echo "deploy setup test: FAILED"
    exit 1
fi
if [ ! -f "$container_output_dir/output-file" ]; then
    echo "deploy setup test: output file not present"
    echo "deploy setup test: FAILED"
    exit 1
fi
output_file_content=$(<$container_output_dir/output-file)
if [ ! "$output_file_content" == "output-data"  ]; then
    echo "deploy setup test: output file contents not correct"
    echo "deploy setup test: FAILED"
    exit 1
fi
# Check that we now have the expected output file
$TEST_TARGET_SO --stack test deploy up
# Test deploy port command
deploy_port_output=$( $TEST_TARGET_SO --stack test deploy port test 80 )
if [[ "$deploy_port_output" =~ ^0.0.0.0:[1-9][0-9]* ]]; then
    echo "Deploy port test: passed"
else
    echo "Deploy port test: FAILED"
    exit 1
fi
$TEST_TARGET_SO --stack test deploy down
# The next time we bring the container up the volume will be old (from the previous run above)
$TEST_TARGET_SO --stack test deploy up
log_output_1=$( $TEST_TARGET_SO --stack test deploy logs )
if [[ "$log_output_1" == *"filesystem is old"* ]]; then
    echo "Retain volumes test: passed"
else
    echo "Retain volumes test: FAILED"
    exit 1
fi
$TEST_TARGET_SO --stack test deploy down --delete-volumes
# Now when we bring the container up the volume will be new again
$TEST_TARGET_SO --stack test deploy up
log_output_2=$( $TEST_TARGET_SO --stack test deploy logs )
if [[ "$log_output_2" == *"filesystem is fresh"* ]]; then
    echo "Delete volumes test: passed"
else
    echo "Delete volumes test: FAILED"
    exit 1
fi
$TEST_TARGET_SO --stack test deploy down --delete-volumes

# Basic test of creating a deployment
test_deployment_dir=$CERC_REPO_BASE_DIR/test-deployment-dir
test_deployment_spec=$CERC_REPO_BASE_DIR/test-deployment-spec.yml
$TEST_TARGET_SO --stack test deploy init --output $test_deployment_spec --config CERC_TEST_PARAM_1=PASSED,CERC_TEST_PARAM_3=FAST
# Check the file now exists
if [ ! -f "$test_deployment_spec" ]; then
    echo "deploy init test: spec file not present"
    echo "deploy init test: FAILED"
    exit 1
fi
echo "deploy init test: passed"
$TEST_TARGET_SO --stack test deploy create --spec-file $test_deployment_spec --deployment-dir $test_deployment_dir
# Check the deployment dir exists
if [ ! -d "$test_deployment_dir" ]; then
    echo "deploy create test: deployment directory not present"
    echo "deploy create test: FAILED"
    exit 1
fi
echo "deploy create test: passed"
# Check the file writted by the create command in the stack now exists
if [ ! -f "$test_deployment_dir/create-file" ]; then
    echo "deploy create test: create output file not present"
    echo "deploy create test: FAILED"
    exit 1
fi
# And has the right content
create_file_content=$(<$test_deployment_dir/create-file)
if [ ! "$create_file_content" == "create-command-output-data"  ]; then
    echo "deploy create test: create output file contents not correct"
    echo "deploy create test: FAILED"
    exit 1
fi

# Add a config file to be picked up by the ConfigMap before starting.
echo "dbfc7a4d-44a7-416d-b5f3-29842cc47650" > $test_deployment_dir/data/test-config/test_config

echo "deploy create output file test: passed"

# Test sync functionality: update deployment without destroying data
# First, create a marker file in the data directory to verify it's preserved
test_data_marker="$test_deployment_dir/data/test-data-bind/sync-test-marker.txt"
echo "original-data-$(date +%s)" > "$test_data_marker"
original_marker_content=$(<$test_data_marker)

# Modify a config file in the deployment to differ from source (to test backup)
test_config_file="$test_deployment_dir/config/test/settings.env"
test_config_file_original_content=$(<$test_config_file)
test_config_file_changed_content="ANSWER=69"
echo "$test_config_file_changed_content" > "$test_config_file"

# Check a config file that matches the source (to test no backup for unchanged files)
test_unchanged_config="$test_deployment_dir/config/test/script.sh"

# Modify spec file to simulate an update
sed -i.bak 's/CERC_TEST_PARAM_3:/CERC_TEST_PARAM_3: FASTER/' $test_deployment_spec

# Create/modify config.env to test it isn't overwritten during sync
config_env_file="$test_deployment_dir/config.env"
config_env_persistent_content="PERSISTENT_VALUE=should-not-be-overwritten-$(date +%s)"
echo "$config_env_persistent_content" >> "$config_env_file"
original_config_env_content=$(<$config_env_file)

# Run sync to update deployment files without destroying data
$TEST_TARGET_SO --stack test deploy create --spec-file $test_deployment_spec --deployment-dir $test_deployment_dir --update

# Verify config.env was not overwritten
synced_config_env_content=$(<$config_env_file)
if [ "$synced_config_env_content" == "$original_config_env_content" ]; then
    echo "deployment update test: config.env preserved - passed"
else
    echo "deployment update test: config.env was overwritten - FAILED"
    echo "Expected: $original_config_env_content"
    echo "Got: $synced_config_env_content"
    exit 1
fi

# Verify the spec file was updated in deployment dir
updated_deployed_spec=$(<$test_deployment_dir/spec.yml)
if [[ "$updated_deployed_spec" == *"FASTER"* ]]; then
    echo "deployment update test: spec file updated"
else
    echo "deployment update test: spec file not updated - FAILED"
    exit 1
fi

# Verify changed config file was backed up
test_config_backup="${test_config_file}.bak"
if [ -f "$test_config_backup" ]; then
    backup_content=$(<$test_config_backup)
    if [ "$backup_content" == "$test_config_file_changed_content" ]; then
        echo "deployment update test: changed config file backed up - passed"
    else
        echo "deployment update test: backup content incorrect - FAILED"
        exit 1
    fi
else
    echo "deployment update test: backup file not created for changed file - FAILED"
    exit 1
fi

# Verify unchanged config file was NOT backed up
test_unchanged_backup="$test_unchanged_config.bak"
if [ -f "$test_unchanged_backup" ]; then
    echo "deployment update test: backup created for unchanged file - FAILED"
    exit 1
else
    echo "deployment update test: no backup for unchanged file - passed"
fi

# Verify the config file was updated from source
updated_config_content=$(<$test_config_file)
if [ "$updated_config_content" == "$test_config_file_original_content" ]; then
    echo "deployment update test: config file updated from source - passed"
else
    echo "deployment update test: config file not updated correctly - FAILED"
    exit 1
fi

# Verify the data marker file still exists with original content
if [ ! -f "$test_data_marker" ]; then
    echo "deployment update test: data file deleted - FAILED"
    exit 1
fi
synced_marker_content=$(<$test_data_marker)
if [ "$synced_marker_content" == "$original_marker_content" ]; then
    echo "deployment update test: data preserved - passed"
else
    echo "deployment update test: data corrupted - FAILED"
    exit 1
fi
echo "deployment update test: passed"

# Try to start the deployment
$TEST_TARGET_SO deployment --dir $test_deployment_dir start
# Check logs command works
log_output_3=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_3" == *"filesystem is fresh"* ]]; then
    echo "deployment logs test: passed"
else
    echo "deployment logs test: FAILED"
    exit 1
fi
# Check the config variable CERC_TEST_PARAM_1 was passed correctly
if [[ "$log_output_3" == *"Test-param-1: PASSED"* ]]; then
    echo "deployment config test: passed"
else
    echo "deployment config test: FAILED"
    exit 1
fi
# Check the config variable CERC_TEST_PARAM_2 was passed correctly from the compose file
if [[ "$log_output_3" == *"Test-param-2: CERC_TEST_PARAM_2_VALUE"* ]]; then
    echo "deployment compose config test: passed"
else
    echo "deployment compose config test: FAILED"
    exit 1
fi
# Check the config variable CERC_TEST_PARAM_3 was passed correctly
if [[ "$log_output_3" == *"Test-param-3: FAST"* ]]; then
    echo "deployment config test: passed"
else
    echo "deployment config test: FAILED"
    exit 1
fi

# Check that the ConfigMap is mounted and contains the expected content.
log_output_4=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_4" == *"/config/test_config:"* ]] && [[ "$log_output_4" == *"dbfc7a4d-44a7-416d-b5f3-29842cc47650"* ]]; then
    echo "deployment ConfigMap test: passed"
else
    echo "deployment ConfigMap test: FAILED"
    delete_cluster_exit
fi

# Stop then start again and check the volume was preserved
$TEST_TARGET_SO deployment --dir $test_deployment_dir stop
# Sleep a bit just in case
# sleep for longer to check if that's why the subsequent create cluster fails
sleep 20
$TEST_TARGET_SO deployment --dir $test_deployment_dir start
log_output_5=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_5" == *"filesystem is old"* ]]; then
    echo "Retain volumes test: passed"
else
    echo "Retain volumes test: FAILED"
    delete_cluster_exit
fi

# Stop and clean up
$TEST_TARGET_SO deployment --dir $test_deployment_dir stop --delete-volumes
echo "Test passed"
