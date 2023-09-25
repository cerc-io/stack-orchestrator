#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
# Dump environment variables for debugging
echo "Environment variables:"
env
echo "Running gitea test"
# Bit of a hack, test the most recent package
TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
# Set a non-default repo dir
export CERC_REPO_BASE_DIR=~/stack-orchestrator-gitea-test
echo "Testing this package: $TEST_TARGET_SO"
echo "Test version command"
reported_version_string=$( $TEST_TARGET_SO version )
echo "Version reported is: ${reported_version_string}"
echo "Cloning repositories into: $CERC_REPO_BASE_DIR"
rm -rf $CERC_REPO_BASE_DIR
mkdir -p $CERC_REPO_BASE_DIR

$TEST_TARGET_SO --stack build-support build-containers
$TEST_TARGET_SO --stack package-registry setup-repositories
$TEST_TARGET_SO --stack package-registry build-containers
output=$($TEST_TARGET_SO --stack package-registry deploy-system up)
token=$(echo $output | grep -o 'export CERC_NPM_AUTH_TOKEN=[^ ]*' | cut -d '=' -f 2)
export CERC_NPM_AUTH_TOKEN=$token
$TEST_TARGET_SO --stack fixturenet-laconicd setup-repositories 
$TEST_TARGET_SO --stack fixturenet-laconicd build-npms

# Clean up
$TEST_TARGET_SO --stack package-registry deploy-system down
echo "Test passed"
