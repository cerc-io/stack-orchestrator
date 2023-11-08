#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
# Dump environment variables for debugging
echo "Environment variables:"
env
# Test basic stack-orchestrator webapp
echo "Running stack-orchestrator webapp test"
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
git clone https://git.vdb.to/cerc-io/test-progressive-web-app.git $CERC_REPO_BASE_DIR/test-progressive-web-app

# Test webapp command execution
$TEST_TARGET_SO build-webapp --source-repo $CERC_REPO_BASE_DIR/test-progressive-web-app

UUID=`uuidgen`

CONTAINER_ID=$(docker run -p 3000:3000 -d cerc/test-progressive-web-app:local)
sleep 3
wget -O test.before -m http://localhost:3000

docker remove -f $CONTAINER_ID

CONTAINER_ID=$(docker run -p 3000:3000 -e CERC_WEBAPP_DEBUG=$UUID -d cerc/test-progressive-web-app:local)
sleep 3
wget -O test.after -m http://localhost:3000

set +e
grep "$UUID" test.before > /dev/null
if [ $? -ne 1 ]; then
  echo "Found $UUID in before ouput."
  exit 1
fi

grep "$UUID" test.after > /dev/null
if [ $? -ne 1 ]; then
  echo "Found $UUID in before ouput."
  exit 1
fi


