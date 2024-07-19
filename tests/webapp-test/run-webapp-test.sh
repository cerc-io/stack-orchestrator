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
if [ "$1" == "from-path" ]; then
    TEST_TARGET_SO="laconic-so"
else
    TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
fi
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

CHECK="SPECIAL_01234567890_TEST_STRING"

set +e

app_image_name="cerc/test-progressive-web-app:local"

CONTAINER_ID=$(docker run -p 3000:80 -d -e CERC_SCRIPT_DEBUG=$CERC_SCRIPT_DEBUG ${app_image_name})
sleep 3
wget --tries 20 --retry-connrefused --waitretry=3 -O test.before -m http://localhost:3000

docker logs $CONTAINER_ID
docker remove -f $CONTAINER_ID

echo "Running app container test"
CONTAINER_ID=$(docker run -p 3000:80 -e CERC_WEBAPP_DEBUG=$CHECK -e CERC_SCRIPT_DEBUG=$CERC_SCRIPT_DEBUG -d ${app_image_name})
sleep 3
wget --tries 20 --retry-connrefused --waitretry=3 -O test.after -m http://localhost:3000

docker logs $CONTAINER_ID
docker remove -f $CONTAINER_ID

echo "###########################################################################"
echo ""

grep "$CHECK" test.before > /dev/null
if [ $? -ne 1 ]; then
  echo "BEFORE: FAILED"
  exit 1
else
  echo "BEFORE: PASSED"
fi

grep "$CHECK" test.after > /dev/null
if [ $? -ne 0 ]; then
  echo "AFTER: FAILED"
  exit 1
else
  echo "AFTER: PASSED"
fi

echo "Running deployment create test"
# Note: this is not a full test -- all we're testing here is that the deploy-webapp create command doesn't crash
test_deployment_dir=$CERC_REPO_BASE_DIR/test-deployment-dir
fake_k8s_config_file=$CERC_REPO_BASE_DIR/kube-config.yml
touch ${fake_k8s_config_file}

$TEST_TARGET_SO deploy-webapp create --kube-config ${fake_k8s_config_file} --deployment-dir ${test_deployment_dir} --image ${app_image_name} --url https://my-test-app.example.com
if [ -d ${test_deployment_dir} ]; then
  echo "PASSED"
else
  echo "FAILED"
  exit 1
fi

exit 0
