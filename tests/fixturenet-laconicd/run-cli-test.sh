#!/usr/bin/env bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "$(date +"%Y-%m-%d %T"): Running stack-orchestrator Laconic registry CLI tests"
env
cat /etc/hosts
# Bit of a hack, test the most recent package
TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )

echo "$(date +"%Y-%m-%d %T"): Starting stack"
TEST_AUCTION_ENABLED=true BASE_DIR=~/cerc $TEST_TARGET_SO --stack fixturenet-laconicd deploy --cluster laconicd up
echo "$(date +"%Y-%m-%d %T"): Stack started"

# Verify that the fixturenet is up and running
$TEST_TARGET_SO --stack fixturenet-laconicd deploy --cluster laconicd ps

# Get the fixturenet account address
laconicd_account_address=$(docker exec laconicd-laconicd-1 laconicd keys list | awk '/- address:/ {print $3}')

# Copy over config
docker exec laconicd-cli-1 cp config.yml laconic-registry-cli/

# Wait for the laconid endpoint to come up
echo "Waiting for the RPC endpoint to come up"
docker exec laconicd-laconicd-1 sh -c "curl --retry 20 --retry-delay 3 --retry-connrefused http://127.0.0.1:9473/api"

# Run the tests
echo "Running the tests"
docker exec -e TEST_ACCOUNT=$laconicd_account_address laconicd-cli-1 sh -c 'cd laconic-registry-cli && yarn && yarn test'

# Clean up
$TEST_TARGET_SO --stack fixturenet-laconicd deploy --cluster laconicd down --delete-volumes
echo "$(date +"%Y-%m-%d %T"): Test finished"
