#!/bin/bash
# Run a test suite locally in an isolated venv.
#
# Usage:
#   ./tests/scripts/run-test-local.sh <test-script>
#
# Examples:
#   ./tests/scripts/run-test-local.sh tests/webapp-test/run-webapp-test.sh
#   ./tests/scripts/run-test-local.sh tests/smoke-test/run-smoke-test.sh
#   ./tests/scripts/run-test-local.sh tests/k8s-deploy/run-deploy-test.sh
#
# The script creates a temporary venv, installs shiv, builds the laconic-so
# package, runs the requested test, then cleans up.

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <test-script> [args...]"
  exit 1
fi

TEST_SCRIPT="$1"
shift

if [ ! -f "$TEST_SCRIPT" ]; then
  echo "Error: $TEST_SCRIPT not found"
  exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR=$(mktemp -d /tmp/so-test-XXXXXX)

cleanup() {
  echo "Cleaning up venv: $VENV_DIR"
  rm -rf "$VENV_DIR"
}
trap cleanup EXIT

cd "$REPO_DIR"

echo "==> Creating venv in $VENV_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "==> Installing shiv"
pip install -q shiv

echo "==> Building laconic-so package"
./scripts/create_build_tag_file.sh
./scripts/build_shiv_package.sh

echo "==> Running: $TEST_SCRIPT $*"
exec "./$TEST_SCRIPT" "$@"
