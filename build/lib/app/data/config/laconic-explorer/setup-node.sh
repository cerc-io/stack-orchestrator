#!/bin/bash

# TODO: this file configures laconicd as a non-consensus node
# so we should have a mechanism to bundle it inside the container rather than link from here
# at deploy time.

CHAINID=$CHAIN_ID
MONIKER="explorer-node"
LOGLEVEL="info"

# validate dependencies are installed
command -v jq > /dev/null 2>&1 || { echo >&2 "jq not installed. More info: https://stedolan.github.io/jq/download/"; exit 1; }

# remove existing daemon and client
rm -rf ~/.laconic*

laconicd config chain-id $CHAINID

# Set moniker and chain-id
laconicd init $MONIKER --chain-id $CHAINID

# Copy genesis file
cp /laconic-configs/genesis.json $HOME/.laconicd/config/genesis.json

# disable produce empty block
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconicd/config/config.toml
  else
    sed -i 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconicd/config/config.toml
fi

# enable rpc endpoints for explorer (Laconicd REST api on port 1317; Tendermint rpc on port 26657)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's#^laddr = "tcp://127\.0\.0\.1:26657"#laddr = "tcp://0.0.0.0:26657"#' $HOME/.laconicd/config/config.toml
    sed -i '' 's#^cors_allowed_origins = \[\]#cors_allowed_origins = \["laconic-explorer"\]#' $HOME/.laconicd/config/config.toml
    sed -i '' 's#^enable = false#enable = true#' $HOME/.laconicd/config/app.toml
  else
    sed -i 's#^laddr = "tcp://127\.0\.0\.1:26657"#laddr = "tcp://0.0.0.0:26657"#' $HOME/.laconicd/config/config.toml
    sed -i 's#^cors_allowed_origins = \[\]#cors_allowed_origins = \["laconic-explorer"\]#' $HOME/.laconicd/config/config.toml
    sed -i 's#^enable = false#enable = true#' $HOME/.laconicd/config/app.toml
fi

echo $PEERS

# add peers to config
if [[ "$OSTYPE" == "darwin"* ]]; then
    #sed -i '' 's#^laddr = "tcp://0\.0\.0\.0:26656"#laddr = "tcp://0.0.0.0:27656"#' $HOME/.laconicd/config/config.toml
    sed -i '' "s#^persistent_peers = \"\"#persistent_peers = \"$PEERS\"#" $HOME/.laconicd/config/config.toml
  else
    #sed -i 's#^laddr = "tcp://0\.0\.0\.0:26656"#laddr = "tcp://0.0.0.0:27656"#' $HOME/.laconicd/config/config.toml
    sed -i "s#^persistent_peers = \"\"#persistent_peers = \"$PEERS\"#" $HOME/.laconicd/config/config.toml
fi

# Start the node (remove the --pruning=nothing flag if historical queries are not needed)
# laconicd start --pruning=nothing --evm.tracer=json $TRACE --log_level $LOGLEVEL --minimum-gas-prices=0.0001aphoton --json-rpc.api eth,txpool,personal,net,debug,web3,miner --api.enable --gql-server --gql-playground
laconicd start --pruning=nothing --log_level $LOGLEVEL
