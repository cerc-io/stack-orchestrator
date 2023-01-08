#!/usr/bin/env bash

# See: https://github.com/sigp/lighthouse/blob/stable/scripts/local_testnet/validator_client.sh
#
# Usage: ./validator_client.sh <DATADIR> <BEACON-NODE-HTTP> <OPTIONAL-DEBUG-LEVEL>

set -Eeuo pipefail

source ./vars.env

DEBUG_LEVEL=info

BUILDER_PROPOSALS=

# Get options
while getopts "pd:" flag; do
  case "${flag}" in
    p) BUILDER_PROPOSALS="--builder-proposals";;
    d) DEBUG_LEVEL=${OPTARG};;
  esac
done

exec lighthouse \
  --debug-level $DEBUG_LEVEL \
  vc \
  $BUILDER_PROPOSALS \
  --validators-dir $DATADIR/node_$NODE_NUMBER/validators \
  --secrets-dir $DATADIR/node_$NODE_NUMBER/secrets \
  --testnet-dir $TESTNET_DIR \
  --init-slashing-protection \
  --beacon-nodes http://localhost:8001 \
  --suggested-fee-recipient $SUGGESTED_FEE_RECIPIENT \
  $VC_ARGS
