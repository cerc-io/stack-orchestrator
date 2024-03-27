#!/bin/bash

# TODO: this file is now an unmodified copy of cerc-io/laconic2d/init.sh
# so we should have a mechanism to bundle it inside the container rather than link from here
# at deploy time.

KEY="mykey"
CHAINID="laconic_9000-1"
MONIKER="localtestnet"
KEYRING="test"
KEYALGO="eth_secp256k1"
LOGLEVEL="info"

if [ "$1" == "clean" ] || [ ! -d "$HOME/.laconic2d/data/blockstore.db" ]; then
  # validate dependencies are installed
  command -v jq > /dev/null 2>&1 || { echo >&2 "jq not installed. More info: https://stedolan.github.io/jq/download/"; exit 1; }

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

  # Change parameter token denominations to aphoton
  cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["staking"]["params"]["bond_denom"]="aphoton"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["crisis"]["constant_fee"]["denom"]="aphoton"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["gov"]["deposit_params"]["min_deposit"][0]["denom"]="aphoton"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["mint"]["params"]["mint_denom"]="aphoton"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  # Custom modules
  cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["record_rent"]["denom"]="aphoton"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_rent"]["denom"]="aphoton"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_commit_fee"]["denom"]="aphoton"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_reveal_fee"]["denom"]="aphoton"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_minimum_bid"]["denom"]="aphoton"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json

  if [[ "$TEST_REGISTRY_EXPIRY" == "true" ]]; then
    echo "Setting timers for expiry tests."

    cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["record_rent_duration"]="60s"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
    cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_grace_period"]="60s"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
    cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_rent_duration"]="60s"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  fi

  if [[ "$TEST_AUCTION_ENABLED" == "true" ]]; then
    echo "Enabling auction and setting timers."

    cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_enabled"]=true' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
    cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_rent_duration"]="60s"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
    cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_grace_period"]="300s"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
    cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_commits_duration"]="60s"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
    cat $HOME/.laconic2d/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_reveals_duration"]="60s"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json
  fi

  # increase block time (?)
  cat $HOME/.laconic2d/config/genesis.json | jq '.consensus_params["block"]["time_iota_ms"]="1000"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json

  # Set gas limit in genesis
  cat $HOME/.laconic2d/config/genesis.json | jq '.consensus_params["block"]["max_gas"]="10000000"' > $HOME/.laconic2d/config/tmp_genesis.json && mv $HOME/.laconic2d/config/tmp_genesis.json $HOME/.laconic2d/config/genesis.json

  # disable produce empty block
  if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconic2d/config/config.toml
    else
      sed -i 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconic2d/config/config.toml
  fi

  if [[ $1 == "pending" ]]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' 's/create_empty_blocks_interval = "0s"/create_empty_blocks_interval = "30s"/g' $HOME/.laconic2d/config/config.toml
        sed -i '' 's/timeout_propose = "3s"/timeout_propose = "30s"/g' $HOME/.laconic2d/config/config.toml
        sed -i '' 's/timeout_propose_delta = "500ms"/timeout_propose_delta = "5s"/g' $HOME/.laconic2d/config/config.toml
        sed -i '' 's/timeout_prevote = "1s"/timeout_prevote = "10s"/g' $HOME/.laconic2d/config/config.toml
        sed -i '' 's/timeout_prevote_delta = "500ms"/timeout_prevote_delta = "5s"/g' $HOME/.laconic2d/config/config.toml
        sed -i '' 's/timeout_precommit = "1s"/timeout_precommit = "10s"/g' $HOME/.laconic2d/config/config.toml
        sed -i '' 's/timeout_precommit_delta = "500ms"/timeout_precommit_delta = "5s"/g' $HOME/.laconic2d/config/config.toml
        sed -i '' 's/timeout_commit = "5s"/timeout_commit = "150s"/g' $HOME/.laconic2d/config/config.toml
        sed -i '' 's/timeout_broadcast_tx_commit = "10s"/timeout_broadcast_tx_commit = "150s"/g' $HOME/.laconic2d/config/config.toml
    else
        sed -i 's/create_empty_blocks_interval = "0s"/create_empty_blocks_interval = "30s"/g' $HOME/.laconic2d/config/config.toml
        sed -i 's/timeout_propose = "3s"/timeout_propose = "30s"/g' $HOME/.laconic2d/config/config.toml
        sed -i 's/timeout_propose_delta = "500ms"/timeout_propose_delta = "5s"/g' $HOME/.laconic2d/config/config.toml
        sed -i 's/timeout_prevote = "1s"/timeout_prevote = "10s"/g' $HOME/.laconic2d/config/config.toml
        sed -i 's/timeout_prevote_delta = "500ms"/timeout_prevote_delta = "5s"/g' $HOME/.laconic2d/config/config.toml
        sed -i 's/timeout_precommit = "1s"/timeout_precommit = "10s"/g' $HOME/.laconic2d/config/config.toml
        sed -i 's/timeout_precommit_delta = "500ms"/timeout_precommit_delta = "5s"/g' $HOME/.laconic2d/config/config.toml
        sed -i 's/timeout_commit = "5s"/timeout_commit = "150s"/g' $HOME/.laconic2d/config/config.toml
        sed -i 's/timeout_broadcast_tx_commit = "10s"/timeout_broadcast_tx_commit = "150s"/g' $HOME/.laconic2d/config/config.toml
    fi
  fi

  # Allocate genesis accounts (cosmos formatted addresses)
  laconic2d add-genesis-account $KEY 100000000000000000000000000aphoton --keyring-backend $KEYRING

  # Sign genesis transaction
  laconic2d gentx $KEY 1000000000000000000000aphoton --keyring-backend $KEYRING --chain-id $CHAINID

  # Collect genesis tx
  laconic2d collect-gentxs

  # Run this to ensure everything worked and that the genesis file is setup correctly
  laconic2d validate-genesis

  if [[ $1 == "pending" ]]; then
    echo "pending mode is on, please wait for the first block committed."
  fi
else
  echo "Using existing database at $HOME/.laconic2d.  To replace, run '`basename $0` clean'"
fi

# Start the node (remove the --pruning=nothing flag if historical queries are not needed)
laconic2d start --pruning=nothing --log_level $LOGLEVEL --minimum-gas-prices=0.0001aphoton --json-rpc.api eth,txpool,personal,net,debug,web3,miner --api.enable --gql-server --gql-playground
