#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
set -e
echo "Running stack-orchestrator Ethereum plugeth fixturenet test"
# Bit of a hack, test the most recent package
TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
CERC_STACK_NAME=fixturenet-plugeth-tx
# Set a new unique repo dir
export CERC_REPO_BASE_DIR=$(mktemp -d stack-orchestrator-fixturenet-eth-test.XXXXXXXXXX)
echo "Testing this package: $TEST_TARGET_SO"
echo "Test version command"
reported_version_string=$( $TEST_TARGET_SO version )
echo "Version reported is: ${reported_version_string}"
echo "Cloning repositories into: $CERC_REPO_BASE_DIR"
$TEST_TARGET_SO --stack $CERC_STACK_NAME setup-repositories
echo "Building containers"
$TEST_TARGET_SO  --stack $CERC_STACK_NAME build-containers
echo "Images in registry:"
docker image ls
echo "Deploying the cluster"
$TEST_TARGET_SO --stack $CERC_STACK_NAME deploy up
# Verify that the fixturenet is up and running
$TEST_TARGET_SO --stack $CERC_STACK_NAME deploy ps
$TEST_TARGET_SO --stack $CERC_STACK_NAME deploy exec fixturenet-eth-bootnode-lighthouse /scripts/status-internal.sh
initial_block_number=$($TEST_TARGET_SO --stack fixturenet-plugeth-tx deploy exec foundry "cast block-number")
# Check that the block number increases some time later
sleep 12
subsequent_block_number=$($TEST_TARGET_SO  --stack $CERC_STACK_NAME deploy exec foundry "cast block-number")
block_number_difference=$((subsequent_block_number - initial_block_number))
# Block height difference should be between 1 and some small number
if [[ $block_number_difference -gt 1 && $block_number_difference -lt 10 ]]; then
  echo "Test passed"
  test_result=0
else
  echo "Test failed: block numbers were ${initial_block_number} and ${subsequent_block_number}"
  test_result=1
fi
$TEST_TARGET_SO --stack $CERC_STACK_NAME deploy down
echo "Removing cloned repositories"
rm -rf $CERC_REPO_BASE_DIR
exit $test_result
