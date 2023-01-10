# Basic simple test of stack-orchestrator functionality
echo "Running stack-orchestrator smoke test"
TEST_TARGET_SO=package/laconic-so
# Set a non-default repo dir
export CERC_REPO_BASE_DIR=~/stack-orchestrator-test/repo-base-dir
echo "Testing this package: $TEST_TARGET_SO"
echo "Cloning repositories into: $CERC_REPO_BASE_DIR"
rm -rf $CERC_REPO_BASE_DIR
mkdir -p $CERC_REPO_BASE_DIR
# Pull an example small public repo to test we can pull a repo
$TEST_TARGET_SO setup-repositories --include cerc-io/laconic-sdk
# TODO: test building the repo into a container
# Build two example containers
# TODO: 
$TEST_TARGET_SO build-containers --include cerc/builder-js,cerc/test-container
# Deploy the test container
$TEST_TARGET_SO deploy-system --include test up
# TODO: test that we can use the deployed container somehow
# Clean up
$TEST_TARGET_SO deploy-system --include test down
echo "Test passed"
