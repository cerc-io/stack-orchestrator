#!/bin/bash

# See: https://github.com/sigp/lighthouse/blob/stable/scripts/local_testnet/reset_genesis_time.sh
#
# Resets the beacon state genesis time to now.
#

set -Eeuo pipefail

source ./vars.env

NOW=${1:-`date +%s`}

lcli \
  change-genesis-time \
  $TESTNET_DIR/genesis.ssz \
  $NOW

echo "Reset genesis time to now ($NOW)"
