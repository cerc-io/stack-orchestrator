#!/usr/bin/env bash

# See: https://github.com/sigp/lighthouse/blob/stable/scripts/local_testnet/bootnode.sh
#
# Starts a bootnode from the generated enr.
#

set -Eeuo pipefail

source ./vars.env

DEBUG_LEVEL=${1:-info}

echo "Starting bootnode"

# Clean up existing ENR dir to avoid node connectivity issues on a restart
if [ -d "$DATADIR/bootnode" ]; then
  echo "Removing existing bootnode enr directory"
  rm -r "$DATADIR/bootnode"
fi

echo "Generating bootnode enr"
lcli \
  generate-bootnode-enr \
  --ip $ENR_IP \
  --udp-port $BOOTNODE_PORT \
  --tcp-port $BOOTNODE_PORT \
  --genesis-fork-version $GENESIS_FORK_VERSION \
  --output-dir $DATADIR/bootnode

bootnode_enr=`cat $DATADIR/bootnode/enr.dat`
echo "- $bootnode_enr" > $TESTNET_DIR/boot_enr.yaml

echo "Generated bootnode enr and written to $TESTNET_DIR/boot_enr.yaml"

exec lighthouse boot_node \
    --testnet-dir $TESTNET_DIR \
    --port $BOOTNODE_PORT \
    --listen-address 0.0.0.0 \
    --disable-packet-filter \
    --network-dir $DATADIR/bootnode \
