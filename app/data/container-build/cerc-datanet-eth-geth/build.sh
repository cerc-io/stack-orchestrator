#!/usr/bin/env bash
#
#Build cerc/datanet-eth-geth

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Make sure the "build" directory is empty.
rm -rf $SCRIPT_DIR/build

# Copy the fixture-net scripts and config.
cp -rp $SCRIPT_DIR/../cerc-fixturenet-eth-geth $SCRIPT_DIR/build

# Then remove terminal_total_difficulty and replace it with capped_maximum_difficulty.
# This has two effects:
#   (1) Disables the Merge (so all we need is geth, not lighthouse).
#   (2) Maintains a fast block rate, since the difficulty will never exceed the capped value.
sed -i '' 's/^terminal_total_difficulty:.*$/capped_maximum_difficulty: 1/' $SCRIPT_DIR/build/genesis/el/el-config.yaml

# Build the image.
docker build -t cerc/datanet-eth-geth:local ${SCRIPT_DIR}/build

# Clean up the "build" directory.
rm -rf $SCRIPT_DIR/build
