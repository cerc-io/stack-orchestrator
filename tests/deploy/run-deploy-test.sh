#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
# Dump environment variables for debugging
echo "Environment variables:"
env
# Test basic stack-orchestrator deploy
echo "Running stack-orchestrator deploy test"
# Bit of a hack, test the most recent package
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
# Test bringing the test container up and down
# with and without volume removal
$TEST_TARGET_SO --stack test setup-repositories
$TEST_TARGET_SO --stack test build-containers
$TEST_TARGET_SO --stack test deploy up
$TEST_TARGET_SO --stack test deploy down
# The next time we bring the container up the volume will be old (from the previous run above)
$TEST_TARGET_SO --stack test deploy up
log_output_1=$( $TEST_TARGET_SO --stack test deploy logs )
if [[ "$log_output_1" == *"Filesystem is old"* ]]; then
    echo "Retain volumes test: passed"
else
    echo "Retain volumes test: FAILED"
    exit 1
fi
$TEST_TARGET_SO --stack test deploy down --delete-volumes
# Now when we bring the container up the volume will be new again
$TEST_TARGET_SO --stack test deploy up
log_output_2=$( $TEST_TARGET_SO --stack test deploy logs )
if [[ "$log_output_2" == *"Filesystem is fresh"* ]]; then
    echo "Delete volumes test: passed"
else
    echo "Delete volumes test: FAILED"
    exit 1
fi
$TEST_TARGET_SO --stack test deploy down --delete-volumes
echo "Test passed"
