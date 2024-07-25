#!/bin/bash

# TODO: this file is now an unmodified copy of cerc-io/laconicd/init.sh
# so we should have a mechanism to bundle it inside the container rather than link from here
# at deploy time.

KEY="mykey"
CHAINID="laconic_9000-1"
MONIKER="localtestnet"
KEYRING="test"
KEYALGO="secp256k1"
LOGLEVEL="${LOGLEVEL:-info}"


if [ "$1" == "clean" ] || [ ! -d "$HOME/.laconicd/data/blockstore.db" ]; then
  # validate dependencies are installed
  command -v jq > /dev/null 2>&1 || {
    echo >&2 "jq not installed. More info: https://stedolan.github.io/jq/download/"
    exit 1
  }

  # remove existing daemon and client
  rm -rf $HOME/.laconicd/*

  if [ -n "`which make`" ]; then
    make install
  fi

  laconicd config set client chain-id $CHAINID
  laconicd config set client keyring-backend $KEYRING

  # if $KEY exists it should be deleted
  laconicd keys add $KEY --keyring-backend $KEYRING --algo $KEYALGO

  # Set moniker and chain-id for Ethermint (Moniker can be anything, chain-id must be an integer)
  laconicd init $MONIKER --chain-id $CHAINID --default-denom photon

  update_genesis() {
    jq "$1" $HOME/.laconicd/config/genesis.json > $HOME/.laconicd/config/tmp_genesis.json &&
      mv $HOME/.laconicd/config/tmp_genesis.json $HOME/.laconicd/config/genesis.json
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

  if [[ "$ONBOARDING_ENABLED" == "true" ]]; then
    echo "Enabling validator onboarding."

    update_genesis '.app_state["onboarding"]["params"]["onboarding_enabled"]=true'
  fi

  # increase block time (?)
  update_genesis '.consensus["params"]["block"]["time_iota_ms"]="1000"'

  # Set gas limit in genesis
  update_genesis '.consensus["params"]["block"]["max_gas"]="10000000"'

  # disable produce empty block
  if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconicd/config/config.toml
    else
      sed -i 's/create_empty_blocks = true/create_empty_blocks = false/g' $HOME/.laconicd/config/config.toml
  fi

  # Enable telemetry (prometheus metrics: http://localhost:1317/metrics?format=prometheus)
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/enabled = false/enabled = true/g' $HOME/.laconicd/config/app.toml
    sed -i '' 's/prometheus-retention-time = 0/prometheus-retention-time = 60/g' $HOME/.laconicd/config/app.toml
    sed -i '' 's/prometheus = false/prometheus = true/g' $HOME/.laconicd/config/config.toml
  else
    sed -i 's/enabled = false/enabled = true/g' $HOME/.laconicd/config/app.toml
    sed -i 's/prometheus-retention-time = 0/prometheus-retention-time = 60/g' $HOME/.laconicd/config/app.toml
    sed -i 's/prometheus = false/prometheus = true/g' $HOME/.laconicd/config/config.toml
  fi

  # Allocate genesis accounts (cosmos formatted addresses)
  laconicd genesis add-genesis-account $KEY 100000000000000000000000000photon --keyring-backend $KEYRING

  # Sign genesis transaction
  laconicd genesis gentx $KEY 1000000000000000000000photon --keyring-backend $KEYRING --chain-id $CHAINID

  # Collect genesis tx
  laconicd genesis collect-gentxs

  # Run this to ensure everything worked and that the genesis file is setup correctly
  laconicd genesis validate
else
  echo "Using existing database at $HOME/.laconicd.  To replace, run '`basename $0` clean'"
fi

# Start the node (remove the --pruning=nothing flag if historical queries are not needed)
laconicd start \
  --pruning=nothing \
  --log_level $LOGLEVEL \
  --minimum-gas-prices=0.0001photon \
  --api.enable \
  --rpc.laddr="tcp://0.0.0.0:26657" \
  --gql-server --gql-playground
