#!/bin/bash

KEY="mykey"
CHAINID="laconic_9000-1"
MONIKER="localtestnet"
KEYRING="test"
LOGLEVEL="${LOGLEVEL:-info}"

if [ "$1" == "clean" ] || [ ! -d "$HOME/.laconic2d/data/blockstore.db" ]; then
  # validate dependencies are installed
  command -v jq > /dev/null 2>&1 || {
    echo >&2 "jq not installed. More info: https://stedolan.github.io/jq/download/"
    exit 1
  }

  # remove existing daemon and client
  rm -rf $HOME/.laconic2d/*
  rm -rf $HOME/.laconic/*

  if [ -n "`which make`" ]; then
    make install
  fi

  laconic2d config set client keyring-backend $KEYRING
  laconic2d config set client chain-id $CHAINID

  # if $KEY exists it should be deleted
  laconic2d keys add $KEY --keyring-backend $KEYRING

  # Set moniker and chain-id for Ethermint (Moniker can be anything, chain-id must be an integer)
  laconic2d init $MONIKER --chain-id $CHAINID --default-denom photon

  update_genesis() {
    jq "$1" $HOME/.laconic2d/config/genesis.json > $HOME/.laconic2d/config/tmp_genesis.json &&
      mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  }

  if [[ "$TEST_REGISTRY_EXPIRY" == "true" ]]; then
    echo "Setting timers for expiry tests."

    update_genesis '.app_state["registry"]["params"]["record_rent_duration"]="60s"'
    update_genesis '.app_state["registry"]["params"]["authority_grace_period"]="60s"'
    update_genesis '.app_state["registry"]["params"]["authority_rent_duration"]="60s"'
  fi

  if [[ "$TEST_AUCTION_ENABLED" == "true" ]]; then
    echo "Enabling auction and setting timers."

    update_genesis '.app_state["registry"]["params"]["authority_auction_enabled"]=true'
    update_genesis '.app_state["registry"]["params"]["authority_rent_duration"]="60s"'
    update_genesis '.app_state["registry"]["params"]["authority_grace_period"]="300s"'
    update_genesis '.app_state["registry"]["params"]["authority_auction_commits_duration"]="60s"'
    update_genesis '.app_state["registry"]["params"]["authority_auction_reveals_duration"]="60s"'
  fi

  # increase block time (?)
  update_genesis '.consensus["params"]["block"]["time_iota_ms"]="1000"'

  # Set gas limit in genesis
  update_genesis '.consensus["params"]["block"]["max_gas"]="10000000"'

  # disable produce empty block
  if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconic2d/config/config.toml
    else
      sed -i 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconic2d/config/config.toml
  fi

  # Allocate genesis accounts (cosmos formatted addresses)
  laconic2d genesis add-genesis-account $KEY 100000000000000000000000000photon --keyring-backend $KEYRING

  # Sign genesis transaction
  laconic2d genesis gentx $KEY 1000000000000000000000photon --keyring-backend $KEYRING --chain-id $CHAINID

  # Collect genesis tx
  laconic2d genesis collect-gentxs

  # Run this to ensure everything worked and that the genesis file is setup correctly
  laconic2d genesis validate
else
  echo "Using existing database at $HOME/.laconic2d.  To replace, run '`basename $0` clean'"
fi

# Start the node (remove the --pruning=nothing flag if historical queries are not needed)
laconic2d start \
  --pruning=nothing \
  --log_level $LOGLEVEL \
  --minimum-gas-prices=0.0001photon \
  --api.enable \
  --rpc.laddr="tcp://0.0.0.0:26657" \
  --gql-server --gql-playground
