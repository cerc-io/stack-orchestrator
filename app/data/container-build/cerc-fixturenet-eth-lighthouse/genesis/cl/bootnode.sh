#!/usr/bin/env bash

# See: https://github.com/sigp/lighthouse/blob/stable/scripts/local_testnet/bootnode.sh
#
# Starts a bootnode from the generated enr.
#

set -Eeuo pipefail

source ./vars.env

DEBUG_LEVEL=${1:-info}

echo "Starting bootnode"

if [ ! -f "$DATADIR/bootnode/enr.dat" ]; then
  echo "Generating bootnode enr"
  lcli \
    generate-bootnode-enr \
    --ip $ENR_IP \
    --udp-port $BOOTNODE_PORT \
    --tcp-port $BOOTNODE_PORT \
    --genesis-fork-version $GENESIS_FORK_VERSION \
    --output-dir $DATADIR/bootnode-temp

  # Output ENR to a temp dir and mv as "lcli generate-bootnode-enr" will not overwrite an empty dir (mounted volume)
  mkdir -p $DATADIR/bootnode
  mv $DATADIR/bootnode-temp/* $DATADIR/bootnode
  rm -r $DATADIR/bootnode-temp

  echo "Generated bootnode enr"
else
  echo "Found existing bootnode enr"
fi

bootnode_enr=`cat $DATADIR/bootnode/enr.dat`
echo "- $bootnode_enr" > $TESTNET_DIR/boot_enr.yaml
echo "Written bootnode enr to $TESTNET_DIR/boot_enr.yaml"

exec lighthouse boot_node \
    --testnet-dir $TESTNET_DIR \
    --port $BOOTNODE_PORT \
    --listen-address 0.0.0.0 \
    --disable-packet-filter \
    --network-dir $DATADIR/bootnode \
