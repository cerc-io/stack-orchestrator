#!/usr/bin/env bash

# See: https://github.com/sigp/lighthouse/blob/stable/scripts/local_testnet/beacon_node.sh
#
# Starts a beacon node based upon a genesis state created by `./setup.sh`.
#

set -Eeuo pipefail

source ./vars.env

SUBSCRIBE_ALL_SUBNETS=
DEBUG_LEVEL=${DEBUG_LEVEL:-info}

# Get positional arguments
data_dir=$DATADIR/node_${NODE_NUMBER}
network_port=9001
http_port=8001
authrpc_port=8551

ENR=`cat $DATADIR/bootnode/enr.dat`
ENR_IP=`ip addr | grep 172 | awk '{print $2}' | cut -d '/' -f1`

exec lighthouse \
  --debug-level $DEBUG_LEVEL \
  bn \
  $SUBSCRIBE_ALL_SUBNETS \
  --boot-nodes "$ENR" \
  --datadir $data_dir \
  --testnet-dir $TESTNET_DIR \
  --enable-private-discovery \
  --staking \
  --enr-address $ENR_IP \
  --enr-udp-port $network_port \
  --enr-tcp-port $network_port \
  --port $network_port \
  --http-address 0.0.0.0 \
  --http-port $http_port \
  --disable-packet-filter \
  --execution-endpoint $EXECUTION_ENDPOINT \
  --execution-jwt $JWTSECRET \
  --terminal-total-difficulty-override $ETH1_TTD \
  --suggested-fee-recipient $SUGGESTED_FEE_RECIPIENT \
  --target-peers $((BN_COUNT - 1))
