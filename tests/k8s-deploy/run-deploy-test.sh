#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
    # Dump environment variables for debugging
    echo "Environment variables:"
    env
fi

# Helper functions: TODO move into a separate file
wait_for_pods_started () {
    for i in {1..50}
    do
        local ps_output=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir ps )

        if [[ "$ps_output" == *"Running containers:"* ]]; then
            # if ready, return
            return
        else
            # if not ready, wait
            sleep 5
        fi
    done
    # Timed out, error exit
    echo "waiting for pods to start: FAILED"
    delete_cluster_exit
}

wait_for_log_output () {
    for i in {1..50}
    do

        local log_output=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )

        if [[ ! -z "$log_output" ]]; then
            # if ready, return
            return
        else
            # if not ready, wait
            sleep 5
        fi
    done
    # Timed out, error exit
    echo "waiting for pods log content: FAILED"
    delete_cluster_exit
}


delete_cluster_exit () {
    $TEST_TARGET_SO deployment --dir $test_deployment_dir stop --delete-volumes
    exit 1
}

# Note: eventually this test should be folded into ../deploy/
# but keeping it separate for now for convenience
TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
# Set a non-default repo dir
export CERC_REPO_BASE_DIR=~/stack-orchestrator-test/repo-base-dir
echo "Testing this package: $TEST_TARGET_SO"
echo "Test version command"
reported_version_string=$( $TEST_TARGET_SO version )
echo "Version reported is: ${reported_version_string}"
echo "Cloning repositories into: $CERC_REPO_BASE_DIR"
rm -rf $CERC_REPO_BASE_DIR
mkdir -p $CERC_REPO_BASE_DIR
$TEST_TARGET_SO --stack test setup-repositories
$TEST_TARGET_SO --stack test build-containers
# Test basic stack-orchestrator deploy to k8s
test_deployment_dir=$CERC_REPO_BASE_DIR/test-deployment-dir
test_deployment_spec=$CERC_REPO_BASE_DIR/test-deployment-spec.yml
$TEST_TARGET_SO --stack test deploy --deploy-to k8s-kind init --output $test_deployment_spec --config CERC_TEST_PARAM_1=PASSED
# Check the file now exists
if [ ! -f "$test_deployment_spec" ]; then
    echo "deploy init test: spec file not present"
    echo "deploy init test: FAILED"
    exit 1
fi
echo "deploy init test: passed"

# Switch to a full path for bind mount.
sed -i "s|^\(\s*test-data-bind:$\)$|\1 ${test_deployment_dir}/data/test-data-bind|" $test_deployment_spec

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
echo "dbfc7a4d-44a7-416d-b5f3-29842cc47650" > $test_deployment_dir/configmaps/test-config/test_config

echo "deploy create output file test: passed"
# Try to start the deployment
$TEST_TARGET_SO deployment --dir $test_deployment_dir start
wait_for_pods_started
# Check logs command works
wait_for_log_output
sleep 1
log_output_3=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_3" == *"filesystem is fresh"* ]]; then
    echo "deployment logs test: passed"
else
    echo "deployment logs test: FAILED"
    echo $log_output_3
    delete_cluster_exit
fi

# Check the config variable CERC_TEST_PARAM_1 was passed correctly
if [[ "$log_output_3" == *"Test-param-1: PASSED"* ]]; then
    echo "deployment config test: passed"
else
    echo "deployment config test: FAILED"
    delete_cluster_exit
fi

# Check the config variable CERC_TEST_PARAM_2 was passed correctly from the compose file
if [[ "$log_output_3" == *"Test-param-2: CERC_TEST_PARAM_2_VALUE"* ]]; then
    echo "deployment compose config test: passed"
else
    echo "deployment compose config test: FAILED"
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

# Check that the bind-mount volume is mounted.
log_output_5=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_5" == *"/data: MOUNTED"* ]]; then
    echo "deployment bind volumes test: passed"
else
    echo "deployment bind volumes test: FAILED"
    echo $log_output_5
    delete_cluster_exit
fi

# Check that the provisioner managed volume is mounted.
log_output_6=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_6" == *"/data2: MOUNTED"* ]]; then
    echo "deployment provisioner volumes test: passed"
else
    echo "deployment provisioner volumes test: FAILED"
    echo $log_output_6
    delete_cluster_exit
fi

# Stop then start again and check the volume was preserved
$TEST_TARGET_SO deployment --dir $test_deployment_dir stop
# Sleep a bit just in case
# sleep for longer to check if that's why the subsequent create cluster fails
sleep 20
$TEST_TARGET_SO deployment --dir $test_deployment_dir start
wait_for_pods_started
wait_for_log_output
sleep 1

log_output_10=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_10" == *"/data filesystem is old"* ]]; then
    echo "Retain bind volumes test: passed"
else
    echo "Retain bind volumes test: FAILED"
    delete_cluster_exit
fi

# These volumes will be completely destroyed by the kind delete/create, because they lived inside
# the kind container.  So, unlike the bind-mount case, they will appear fresh after the restart.
log_output_11=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_11" == *"/data2 filesystem is fresh"* ]]; then
    echo "Fresh provisioner volumes test: passed"
else
    echo "Fresh provisioner volumes test: FAILED"
    delete_cluster_exit
fi

# Stop and clean up
$TEST_TARGET_SO deployment --dir $test_deployment_dir stop --delete-volumes
echo "Test passed"
