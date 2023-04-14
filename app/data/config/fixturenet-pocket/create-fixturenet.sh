#!/bin/bash

# TODO: we should have a mechanism to bundle it inside the container rather than link from here
# at deploy time.

CHAINID="pocketlocal-1"
MONIKER="localtestnet"
SERVICE_URL="http://127.0.0.1:8081"
PASSWORD="mypassword" # wallet password, required by cli

# validate dependencies are installed
command -v jq > /dev/null 2>&1 || { echo >&2 "jq not installed. More info: https://stedolan.github.io/jq/download/"; exit 1; }

# remove existing daemon and client
rm -rf ~/.pocket*

# create a wallet with password "mypassword" and save the address for later
address=$(pocket accounts create --pwd $PASSWORD | awk '/Address:/ {print $2}')

# set this address as the validator address for the node
pocket accounts set-validator $address --pwd $PASSWORD

# save the public key for later
pubkey=$(pocket accounts show $address | awk '/Public Key:/ {print $3}')

# set node's moniker
echo $(pocket util print-configs) | jq '.tendermint_config.Moniker = "'"$MONIKER"'"' | jq . > $HOME/.pocket/config/config.json

# pocket mainnet has block time of 15 minutes, set closer to 1 minute instead
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.TimeoutPropose = 8000000000' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.TimeoutProposeDelta = 600000000' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.TimeoutPrevote = 4000000000' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.TimeoutPrevoteDelta = 600000000' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.TimeoutPrecommit = 4000000000' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.TimeoutPrecommitDelta = 6000000006' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.TimeoutCommit = 52000000000' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.CreateEmptyBlocksInterval = 60000000000' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.PeerGossipSleepDuration = 2000000000' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json
cat $HOME/.pocket/config/config.json | jq '.tendermint_config.Consensus.PeerQueryMaj23SleepDuration = 1200000000' | jq . > $HOME/.pocket/config/tmp_config.json && mv $HOME/.pocket/config/tmp_config.json $HOME/.pocket/config/config.json

# include genesis.json and chains.json
cp $HOME/pocket-configs/genesis.json $HOME/.pocket/config/genesis.json
cp $HOME/pocket-configs/chains.json $HOME/.pocket/config/chains.json

# set chain-id and add node to genesis.json as a validator
cat $HOME/.pocket/config/genesis.json | jq '.chain_id="'"$CHAINID"'"' > $HOME/.pocket/config/tmp_genesis.json && mv $HOME/.pocket/config/tmp_genesis.json $HOME/.pocket/config/genesis.json
cat $HOME/.pocket/config/genesis.json | jq '.app_state.auth.accounts[0].value.address="'"$address"'"' > $HOME/.pocket/config/tmp_genesis.json && mv $HOME/.pocket/config/tmp_genesis.json $HOME/.pocket/config/genesis.json
cat $HOME/.pocket/config/genesis.json | jq '.app_state.auth.accounts[0].value.public_key.value="'"$pubkey"'"' > $HOME/.pocket/config/tmp_genesis.json && mv $HOME/.pocket/config/tmp_genesis.json $HOME/.pocket/config/genesis.json
cat $HOME/.pocket/config/genesis.json | jq '.app_state.pos.validators[0].address="'"$address"'"' > $HOME/.pocket/config/tmp_genesis.json && mv $HOME/.pocket/config/tmp_genesis.json $HOME/.pocket/config/genesis.json
cat $HOME/.pocket/config/genesis.json | jq '.app_state.pos.validators[0].public_key="'"$pubkey"'"' > $HOME/.pocket/config/tmp_genesis.json && mv $HOME/.pocket/config/tmp_genesis.json $HOME/.pocket/config/genesis.json
cat $HOME/.pocket/config/genesis.json | jq '.app_state.pos.validators[0].service_url="'"$SERVICE_URL"'"' > $HOME/.pocket/config/tmp_genesis.json && mv $HOME/.pocket/config/tmp_genesis.json $HOME/.pocket/config/genesis.json

# if [[ $1 == "pending" ]]; then
#   echo "pending mode is on, please wait for the first block committed."
# fi

# Start the node
pocket start --simulateRelay
