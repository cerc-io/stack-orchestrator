#!/bin/sh
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

#TODO: pass these in from the caller
LOGLEVEL="info"

laconicd start \
    --pruning=nothing \
    --log_level $LOGLEVEL \
    --minimum-gas-prices=1alnt \
    --api.enable \
    --gql-server \
    --gql-playground
