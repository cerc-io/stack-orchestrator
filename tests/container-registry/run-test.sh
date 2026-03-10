#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
    # Dump environment variables for debugging
    echo "Environment variables:"
    env
fi

stack="container-registry"

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
$TEST_TARGET_SO --stack ${stack} setup-repositories
$TEST_TARGET_SO --stack ${stack} build-containers
# Test basic stack-orchestrator deploy to k8s
test_deployment_dir=$CERC_REPO_BASE_DIR/${stack}-deployment-dir
test_deployment_spec=$CERC_REPO_BASE_DIR/${stack}-deployment-spec.yml
$TEST_TARGET_SO --stack ${stack} deploy --deploy-to k8s-kind init --output $test_deployment_spec --config CERC_TEST_PARAM_1=PASSED
# Check the file now exists
if [ ! -f "$test_deployment_spec" ]; then
    echo "deploy init test: spec file not present"
    echo "deploy init test: FAILED"
    exit 1
fi
echo "deploy init test: passed"

# Switch to a full path for bind mount.
volume_name="registry-data"
sed -i "s|^\(\s*${volume_name}:$\)$|\1 ${test_deployment_dir}/data/${volume_name}|" $test_deployment_spec

# Add ingress config to the spec file
ed $test_deployment_spec <<IngressSpec
/network:/
a
  http-proxy:
    - host-name: localhost
      routes:
        - path: /
          proxy-to: registry:5000
.
w
q
IngressSpec

$TEST_TARGET_SO --stack ${stack} deploy create --spec-file $test_deployment_spec --deployment-dir $test_deployment_dir
# Check the deployment dir exists
if [ ! -d "$test_deployment_dir" ]; then
    echo "deploy create test: deployment directory not present"
    echo "deploy create test: FAILED"
    exit 1
fi
echo "deploy create test: passed"

# Note: this isn't strictly necessary, except we end up trying to push the image into
# the kind cluster then fails because it can't be found locally
docker pull registry:2.8

# Try to start the deployment
$TEST_TARGET_SO deployment --dir $test_deployment_dir start
wait_for_pods_started
# Check logs command works
wait_for_log_output
sleep 1
log_output_3=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_3" == *"listening on"* ]]; then
    echo "deployment logs test: passed"
else
    echo "deployment logs test: FAILED"
    echo $log_output_3
    delete_cluster_exit
fi

# Check that we can use the registry
# Note: since this pulls from the DockerCo registry without auth it's possible it'll run into rate limiting issues
docker pull hello-world
docker tag hello-world localhost:80/hello-world
docker push localhost:80/hello-world
# Then do a quick check that we actually pushed something there
# See: https://stackoverflow.com/questions/31251356/how-to-get-a-list-of-images-on-docker-registry-v2
registry_response=$(curl -s -X GET http://localhost:80/v2/_catalog)
if [[ "$registry_response" == *"{\"repositories\":[\"hello-world\"]}"* ]]; then
    echo "registry content test: passed"
else
    echo "registry content test: FAILED"
    echo $registry_response
    delete_cluster_exit
fi

# Stop and clean up
$TEST_TARGET_SO deployment --dir $test_deployment_dir stop --delete-volumes
echo "Test passed"
