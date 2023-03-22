#!/bin/bash

# TODO: this file is now an unmodified copy of cerc-io/laconicd/init.sh
# so we should have a mechanism to bundle it inside the container rather than link from here
# at deploy time.

KEY="mykey"
CHAINID="laconic_9000-1"
MONIKER="localtestnet"
KEYRING="test"
KEYALGO="eth_secp256k1"
LOGLEVEL="info"
# trace evm
TRACE="--trace"
# TRACE=""

# validate dependencies are installed
command -v jq > /dev/null 2>&1 || { echo >&2 "jq not installed. More info: https://stedolan.github.io/jq/download/"; exit 1; }

# remove existing daemon and client
rm -rf ~/.laconic*

make install

laconicd config keyring-backend $KEYRING
laconicd config chain-id $CHAINID

# if $KEY exists it should be deleted
laconicd keys add $KEY --keyring-backend $KEYRING --algo $KEYALGO

# Set moniker and chain-id for Ethermint (Moniker can be anything, chain-id must be an integer)
laconicd init $MONIKER --chain-id $CHAINID

# Change parameter token denominations to aphoton
cat $HOME/.laconicd/config/genesis.json | jq '.app_state["staking"]["params"]["bond_denom"]="aphoton"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
cat $HOME/.laconicd/config/genesis.json | jq '.app_state["crisis"]["constant_fee"]["denom"]="aphoton"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
cat $HOME/.laconicd/config/genesis.json | jq '.app_state["gov"]["deposit_params"]["min_deposit"][0]["denom"]="aphoton"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
cat $HOME/.laconicd/config/genesis.json | jq '.app_state["mint"]["params"]["mint_denom"]="aphoton"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
# Custom modules
cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["record_rent"]["denom"]="aphoton"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_rent"]["denom"]="aphoton"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_commit_fee"]["denom"]="aphoton"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_reveal_fee"]["denom"]="aphoton"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_minimum_bid"]["denom"]="aphoton"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json

if [[ "$TEST_REGISTRY_EXPIRY" == "true" ]]; then
  echo "Setting timers for expiry tests."

  cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["record_rent_duration"]="60s"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
  cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_grace_period"]="60s"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
  cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_rent_duration"]="60s"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
fi

if [[ "$TEST_AUCTION_ENABLED" == "true" ]]; then
  echo "Enabling auction and setting timers."

  cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_enabled"]=true' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
  cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_rent_duration"]="60s"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
  cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_grace_period"]="300s"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
  cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_commits_duration"]="60s"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
  cat $HOME/.laconicd/config/genesis.json | jq '.app_state["registry"]["params"]["authority_auction_reveals_duration"]="60s"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
fi

# increase block time (?)
cat $HOME/.laconicd/config/genesis.json | jq '.consensus_params["block"]["time_iota_ms"]="1000"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json

# Set gas limit in genesis
cat $HOME/.laconicd/config/genesis.json | jq '.consensus_params["block"]["max_gas"]="10000000"' > $HOME/.laconicd/config/tmp_genesis.json && mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json

# disable produce empty block
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconicd/config/config.toml
  else
    sed -i 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconicd/config/config.toml
fi

if [[ $1 == "pending" ]]; then
  if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' 's/create_empty_blocks_interval = "0s"/create_empty_blocks_interval = "30s"/g' $HOME/.laconicd/config/config.toml
      sed -i '' 's/timeout_propose = "3s"/timeout_propose = "30s"/g' $HOME/.laconicd/config/config.toml
      sed -i '' 's/timeout_propose_delta = "500ms"/timeout_propose_delta = "5s"/g' $HOME/.laconicd/config/config.toml
      sed -i '' 's/timeout_prevote = "1s"/timeout_prevote = "10s"/g' $HOME/.laconicd/config/config.toml
      sed -i '' 's/timeout_prevote_delta = "500ms"/timeout_prevote_delta = "5s"/g' $HOME/.laconicd/config/config.toml
      sed -i '' 's/timeout_precommit = "1s"/timeout_precommit = "10s"/g' $HOME/.laconicd/config/config.toml
      sed -i '' 's/timeout_precommit_delta = "500ms"/timeout_precommit_delta = "5s"/g' $HOME/.laconicd/config/config.toml
      sed -i '' 's/timeout_commit = "5s"/timeout_commit = "150s"/g' $HOME/.laconicd/config/config.toml
      sed -i '' 's/timeout_broadcast_tx_commit = "10s"/timeout_broadcast_tx_commit = "150s"/g' $HOME/.laconicd/config/config.toml
  else
      sed -i 's/create_empty_blocks_interval = "0s"/create_empty_blocks_interval = "30s"/g' $HOME/.laconicd/config/config.toml
      sed -i 's/timeout_propose = "3s"/timeout_propose = "30s"/g' $HOME/.laconicd/config/config.toml
      sed -i 's/timeout_propose_delta = "500ms"/timeout_propose_delta = "5s"/g' $HOME/.laconicd/config/config.toml
      sed -i 's/timeout_prevote = "1s"/timeout_prevote = "10s"/g' $HOME/.laconicd/config/config.toml
      sed -i 's/timeout_prevote_delta = "500ms"/timeout_prevote_delta = "5s"/g' $HOME/.laconicd/config/config.toml
      sed -i 's/timeout_precommit = "1s"/timeout_precommit = "10s"/g' $HOME/.laconicd/config/config.toml
      sed -i 's/timeout_precommit_delta = "500ms"/timeout_precommit_delta = "5s"/g' $HOME/.laconicd/config/config.toml
      sed -i 's/timeout_commit = "5s"/timeout_commit = "150s"/g' $HOME/.laconicd/config/config.toml
      sed -i 's/timeout_broadcast_tx_commit = "10s"/timeout_broadcast_tx_commit = "150s"/g' $HOME/.laconicd/config/config.toml
  fi
fi

# Allocate genesis accounts (cosmos formatted addresses)
laconicd add-genesis-account $KEY 100000000000000000000000000aphoton --keyring-backend $KEYRING

# Sign genesis transaction
laconicd gentx $KEY 1000000000000000000000aphoton --keyring-backend $KEYRING --chain-id $CHAINID

# Collect genesis tx
laconicd collect-gentxs

# Run this to ensure everything worked and that the genesis file is setup correctly
laconicd validate-genesis

if [[ $1 == "pending" ]]; then
  echo "pending mode is on, please wait for the first block committed."
fi

# Start the node (remove the --pruning=nothing flag if historical queries are not needed)
laconicd start --pruning=nothing --evm.tracer=json $TRACE --log_level $LOGLEVEL --minimum-gas-prices=0.0001aphoton --json-rpc.api eth,txpool,personal,net,debug,web3,miner --api.enable --gql-server --gql-playground
