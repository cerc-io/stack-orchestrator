#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "$(date +"%Y-%m-%d %T"): Running stack-orchestrator Ethereum fixturenet test"
# Bit of a hack, test the most recent package
TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
# Set a new unique repo dir
export CERC_REPO_BASE_DIR=$(mktemp -d stack-orchestrator-fixturenet-eth-test.XXXXXXXXXX)
echo "$(date +"%Y-%m-%d %T"): Testing this package: $TEST_TARGET_SO"
echo "$(date +"%Y-%m-%d %T"): Test version command"
reported_version_string=$( $TEST_TARGET_SO version )
echo "$(date +"%Y-%m-%d %T"): Version reported is: ${reported_version_string}"
echo "$(date +"%Y-%m-%d %T"): Cloning repositories into: $CERC_REPO_BASE_DIR"
$TEST_TARGET_SO --stack fixturenet-eth setup-repositories
echo "$(date +"%Y-%m-%d %T"): Building containers"
$TEST_TARGET_SO --stack fixturenet-eth build-containers
echo "$(date +"%Y-%m-%d %T"): Starting stack"
$TEST_TARGET_SO --stack fixturenet-eth deploy up
echo "$(date +"%Y-%m-%d %T"): Stack started"
# Verify that the fixturenet is up and running
$TEST_TARGET_SO --stack fixturenet-eth deploy ps
# echo "$(date +"%Y-%m-%d %T"): Getting stack status"
# $TEST_TARGET_SO --stack fixturenet-eth deploy exec fixturenet-eth-bootnode-lighthouse /scripts/status-internal.sh

timeout=900 # 15 minutes
echo "$(date +"%Y-%m-%d %T"): Getting initial block number. Timeout set to $timeout seconds"
start_time=$(date +%s)
elapsed_time=0
initial_block_number=0
while [ "$initial_block_number" -eq 0 ]  && [ $elapsed_time -lt $timeout ]; do
  sleep 10
  echo "$(date +"%Y-%m-%d %T"): Waiting for initial block..."
  initial_block_number=$($TEST_TARGET_SO --stack fixturenet-eth deploy exec foundry "cast block-number")
  current_time=$(date +%s)
  elapsed_time=$((current_time - start_time))
done

subsequent_block_number=$initial_block_number

# if initial block was 0 after timeout, assume chain did not start successfully and skip finding subsequent block
if [[ $initial_block_number -gt 0 ]]; then
  timeout=300
  echo "$(date +"%Y-%m-%d %T"): Getting subsequent block number. Timeout set to $timeout seconds"
  start_time=$(date +%s)
  elapsed_time=0
  # wait for 5 blocks or timeout
  while [ "$subsequent_block_number" -le $((initial_block_number + 5)) ]  && [ $elapsed_time -lt $timeout ]; do
    sleep 10
    echo "$(date +"%Y-%m-%d %T"): Waiting for five blocks or $timeout seconds..."
    subsequent_block_number=$($TEST_TARGET_SO --stack fixturenet-eth deploy exec foundry "cast block-number")
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
  done
fi

# will return 0 if either of the above loops timed out
block_number_difference=$((subsequent_block_number - initial_block_number))

echo "$(date +"%Y-%m-%d %T"): Results of block height queries:"
echo "Initial block height: $initial_block_number"
echo "Subsequent block height: $subsequent_block_number"

# Block height difference should be between 1 and some small number
if [[ $block_number_difference -gt 1 && $block_number_difference -lt 100 ]]; then
  echo "Test passed"
  test_result=0
else
  echo "Test failed: block numbers were ${initial_block_number} and ${subsequent_block_number}"
  echo "Logs from stack:"
  $TEST_TARGET_SO --stack fixturenet-eth deploy logs
  test_result=1
fi
$TEST_TARGET_SO --stack fixturenet-eth deploy down --delete-volumes
echo "$(date +"%Y-%m-%d %T"): Removing cloned repositories"
rm -rf $CERC_REPO_BASE_DIR
echo "$(date +"%Y-%m-%d %T"): Test finished"
exit $test_result
