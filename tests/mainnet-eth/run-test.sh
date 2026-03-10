#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Running stack-orchestrator Ethereum mainnet test"
# Bit of a hack, test the most recent package
TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
# Set a new unique repo dir
export CERC_REPO_BASE_DIR=$(mktemp -d stack-orchestrator-mainnet-eth-test.XXXXXXXXXX)
DEPLOYMENT_DIR=mainnet-eth-deployment-test
echo "Testing this package: $TEST_TARGET_SO"
echo "Test version command"
reported_version_string=$( $TEST_TARGET_SO version )
echo "Version reported is: ${reported_version_string}"
echo "Cloning repositories into: $CERC_REPO_BASE_DIR"
$TEST_TARGET_SO --stack mainnet-eth setup-repositories
$TEST_TARGET_SO --stack mainnet-eth build-containers
$TEST_TARGET_SO --stack mainnet-eth deploy init --output mainnet-eth-spec.yml
$TEST_TARGET_SO deploy create --spec-file mainnet-eth-spec.yml --deployment-dir $DEPLOYMENT_DIR
# Start the stack
$TEST_TARGET_SO deployment --dir $DEPLOYMENT_DIR start
# Verify that the stack is up and running
$TEST_TARGET_SO deployment --dir $DEPLOYMENT_DIR ps
#TODO: add a check that the container logs show good startup
$TEST_TARGET_SO deployment --dir $DEPLOYMENT_DIR stop --delete-volumes
echo "Removing deployment directory"
rm -rf $DEPLOYMENT_DIR
echo "Removing cloned repositories"
rm -rf $CERC_REPO_BASE_DIR
exit $test_result
