#!/bin/sh
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi

#TODO: pass these in from the caller
TRACE="--trace"
LOGLEVEL="info"

laconicd start \
    --pruning=nothing \
    --evm.tracer=json $TRACE \
    --log_level $LOGLEVEL \
    --minimum-gas-prices=0.0001aphoton \
    --json-rpc.api eth,txpool,personal,net,debug,web3,miner \
    --api.enable \
    --gql-server \
    --gql-playground
