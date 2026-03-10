#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
# Dump environment variables for debugging
echo "Environment variables:"
env

if [ "$1" == "from-path" ]; then
    TEST_TARGET_SO="laconic-so"
else
    TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
fi

delete_cluster_exit () {
    $TEST_TARGET_SO deployment --dir $test_deployment_dir stop --delete-volumes
    exit 1
}

# Test basic stack-orchestrator deploy
echo "Running stack-orchestrator external stack deploy test"
# Set a non-default repo dir
export CERC_REPO_BASE_DIR=~/stack-orchestrator-test/repo-base-dir
echo "Testing this package: $TEST_TARGET_SO"
echo "Test version command"
reported_version_string=$( $TEST_TARGET_SO version )
echo "Version reported is: ${reported_version_string}"
echo "Cloning repositories into: $CERC_REPO_BASE_DIR"
rm -rf $CERC_REPO_BASE_DIR
mkdir -p $CERC_REPO_BASE_DIR
# Clone the external test stack
$TEST_TARGET_SO fetch-stack git.vdb.to/cerc-io/test-external-stack
stack_name="$CERC_REPO_BASE_DIR/test-external-stack/stack-orchestrator/stacks/test-external-stack"
TEST_TARGET_SO_STACK="$TEST_TARGET_SO --stack ${stack_name}"
# Test bringing the test container up and down
# with and without volume removal
$TEST_TARGET_SO_STACK setup-repositories
$TEST_TARGET_SO_STACK build-containers
# Test deploy command execution
$TEST_TARGET_SO_STACK deploy setup $CERC_REPO_BASE_DIR
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
$TEST_TARGET_SO_STACK deploy up
# Test deploy port command
deploy_port_output=$( $TEST_TARGET_SO_STACK deploy port test 80 )
if [[ "$deploy_port_output" =~ ^0.0.0.0:[1-9][0-9]* ]]; then
    echo "Deploy port test: passed"
else
    echo "Deploy port test: FAILED"
    exit 1
fi
$TEST_TARGET_SO_STACK deploy down
# The next time we bring the container up the volume will be old (from the previous run above)
$TEST_TARGET_SO_STACK deploy up
log_output_1=$( $TEST_TARGET_SO_STACK deploy logs )
if [[ "$log_output_1" == *"filesystem is old"* ]]; then
    echo "Retain volumes test: passed"
else
    echo "Retain volumes test: FAILED"
    exit 1
fi
$TEST_TARGET_SO_STACK deploy down --delete-volumes
# Now when we bring the container up the volume will be new again
$TEST_TARGET_SO_STACK deploy up
log_output_2=$( $TEST_TARGET_SO_STACK deploy logs )
if [[ "$log_output_2" == *"filesystem is fresh"* ]]; then
    echo "Delete volumes test: passed"
else
    echo "Delete volumes test: FAILED"
    exit 1
fi
$TEST_TARGET_SO_STACK deploy down --delete-volumes
# Basic test of creating a deployment
test_deployment_dir=$CERC_REPO_BASE_DIR/test-deployment-dir
test_deployment_spec=$CERC_REPO_BASE_DIR/test-deployment-spec.yml
$TEST_TARGET_SO_STACK deploy init --output $test_deployment_spec --config CERC_TEST_PARAM_1=PASSED,CERC_TEST_PARAM_3=FAST
# Check the file now exists
if [ ! -f "$test_deployment_spec" ]; then
    echo "deploy init test: spec file not present"
    echo "deploy init test: FAILED"
    exit 1
fi
echo "deploy init test: passed"
$TEST_TARGET_SO_STACK deploy create --spec-file $test_deployment_spec --deployment-dir $test_deployment_dir
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
test_data_marker="$test_deployment_dir/data/test-data/sync-test-marker.txt"
mkdir -p "$test_deployment_dir/data/test-data"
echo "external-stack-data-$(date +%s)" > "$test_data_marker"
original_marker_content=$(<$test_data_marker)
# Verify deployment file exists and preserve its cluster ID
original_cluster_id=$(grep "cluster-id:" "$test_deployment_dir/deployment.yml" 2>/dev/null || echo "")
# Modify spec file to simulate an update
sed -i.bak 's/CERC_TEST_PARAM_1=PASSED/CERC_TEST_PARAM_1=UPDATED/' $test_deployment_spec
# Run sync to update deployment files without destroying data
$TEST_TARGET_SO_STACK deploy create --spec-file $test_deployment_spec --deployment-dir $test_deployment_dir --update
# Verify the spec file was updated in deployment dir
updated_deployed_spec=$(<$test_deployment_dir/spec.yml)
if [[ "$updated_deployed_spec" == *"UPDATED"* ]]; then
    echo "deploy sync test: spec file updated"
else
    echo "deploy sync test: spec file not updated - FAILED"
    exit 1
fi
# Verify the data marker file still exists with original content
if [ ! -f "$test_data_marker" ]; then
    echo "deploy sync test: data file deleted - FAILED"
    exit 1
fi
synced_marker_content=$(<$test_data_marker)
if [ "$synced_marker_content" == "$original_marker_content" ]; then
    echo "deploy sync test: data preserved - passed"
else
    echo "deploy sync test: data corrupted - FAILED"
    exit 1
fi
# Verify cluster ID was preserved (not regenerated)
new_cluster_id=$(grep "cluster-id:" "$test_deployment_dir/deployment.yml" 2>/dev/null || echo "")
if [ -n "$original_cluster_id" ] && [ "$original_cluster_id" == "$new_cluster_id" ]; then
    echo "deploy sync test: cluster ID preserved - passed"
else
    echo "deploy sync test: cluster ID not preserved - FAILED"
    exit 1
fi
echo "deploy sync test: passed"

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
