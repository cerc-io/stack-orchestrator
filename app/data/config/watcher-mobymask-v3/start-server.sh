#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_ETH_RPC_QUERY_ENDPOINT="${CERC_ETH_RPC_QUERY_ENDPOINT:-${DEFAULT_CERC_ETH_RPC_QUERY_ENDPOINT}}"
CERC_ETH_RPC_MUTATION_ENDPOINT="${CERC_ETH_RPC_MUTATION_ENDPOINT:-${DEFAULT_CERC_ETH_RPC_MUTATION_ENDPOINT}}"
CERC_RELAY_PEERS="${CERC_RELAY_PEERS:-${DEFAULT_CERC_RELAY_PEERS}}"
CERC_DENY_MULTIADDRS="${CERC_DENY_MULTIADDRS:-${DEFAULT_CERC_DENY_MULTIADDRS}}"
CERC_PUBSUB="${CERC_PUBSUB:-${DEFAULT_CERC_PUBSUB}}"
CERC_RELAY_ANNOUNCE_DOMAIN="${CERC_RELAY_ANNOUNCE_DOMAIN:-${DEFAULT_CERC_RELAY_ANNOUNCE_DOMAIN}}"
CERC_ENABLE_PEER_L2_TXS="${CERC_ENABLE_PEER_L2_TXS:-${DEFAULT_CERC_ENABLE_PEER_L2_TXS}}"
CERC_DEPLOYED_CONTRACT="${CERC_DEPLOYED_CONTRACT:-${DEFAULT_CERC_DEPLOYED_CONTRACT}}"

CERC_UPSTREAM_NITRO_ADDRESS="${CERC_UPSTREAM_NITRO_ADDRESS:-${DEFAULT_CERC_UPSTREAM_NITRO_ADDRESS}}"
CERC_UPSTREAM_NITRO_MULTIADDR="${CERC_UPSTREAM_NITRO_MULTIADDR:-${DEFAULT_CERC_UPSTREAM_NITRO_MULTIADDR}}"
CERC_UPSTREAM_NITRO_PAY_AMOUNT="${CERC_UPSTREAM_NITRO_PAY_AMOUNT:-${DEFAULT_CERC_UPSTREAM_NITRO_PAY_AMOUNT}}"

watcher_keys_dir="./keys"

echo "Using RPC query endpoint ${CERC_ETH_RPC_QUERY_ENDPOINT}"
echo "Using RPC mutation endpoint ${CERC_ETH_RPC_MUTATION_ENDPOINT}"

# Use public domain for relay multiaddr in peer config if specified
# Otherwise, use the docker container's host IP
if [ -n "$CERC_RELAY_ANNOUNCE_DOMAIN" ]; then
  CERC_RELAY_MULTIADDR="/dns4/${CERC_RELAY_ANNOUNCE_DOMAIN}/tcp/443/wss/p2p/$(jq -r '.id' /app/peers/relay-id.json)"
else
  CERC_RELAY_MULTIADDR="/dns4/mobymask-watcher-server/tcp/9090/ws/p2p/$(jq -r '.id' /app/peers/relay-id.json)"
fi

# Use contract address from environment variable or set from config.json in mounted volume
if [ -n "$CERC_DEPLOYED_CONTRACT" ]; then
  CONTRACT_ADDRESS="${CERC_DEPLOYED_CONTRACT}"
else
  # Assign deployed contract address from server config (created by mobymask container after deploying contract)
  CONTRACT_ADDRESS=$(jq -r '.address' /server/config.json | tr -d '"')
fi

nitro_addresses_file="/nitro/nitro-addresses.json"
nitro_addresses_destination_file="./src/nitro-addresses.json"

# Check if CERC_NA_ADDRESS environment variable is set
if [ -n "$CERC_NA_ADDRESS" ]; then
  echo "CERC_NA_ADDRESS is set to '$CERC_NA_ADDRESS'"
  echo "CERC_VPA_ADDRESS is set to '$CERC_VPA_ADDRESS'"
  echo "CERC_CA_ADDRESS is set to '$CERC_CA_ADDRESS'"
  echo "Using the above Nitro addresses"

  # Create the required JSON and write it to a file
  nitro_addresses_json=$(jq -n \
    --arg na "$CERC_NA_ADDRESS" \
    --arg vpa "$CERC_VPA_ADDRESS" \
    --arg ca "$CERC_CA_ADDRESS" \
    '.nitroAdjudicatorAddress = $na | .virtualPaymentAppAddress = $vpa | .consensusAppAddress = $ca')
  echo "$nitro_addresses_json" > "${nitro_addresses_destination_file}"
elif [ -f ${nitro_addresses_file} ]; then
  echo "Using Nitro addresses from ${nitro_addresses_file}:"
  cat "$nitro_addresses_file"
  cat "$nitro_addresses_file" > "$nitro_addresses_destination_file"
else
  echo "Nitro addresses not available"
  exit 1
fi

# Build after setting the Nitro addresses
yarn build

echo "Using CERC_PRIVATE_KEY_PEER (account with funds) from env for sending txs to L2"
echo "Using CERC_PRIVATE_KEY_NITRO from env for Nitro account"

if [ -n "$CERC_PEER_ID" ]; then
  echo "Using CERC_PEER_ID ${CERC_PEER_ID} from env for watcher fixture"
  echo "Consensus module enabled"

  # Set corresponding variables
  PEER_ID_FILE='./peer-id.json'
  CONSENSUS_ENABLED=true
  WATCHER_PARTY_PEERS_FILE='./watcher-party-peers.json'

  # Create watcher party array
  watcher_parties=()

  # Iterate over each fixture JSON file
  for peer_data_file in "$watcher_keys_dir"/*.json; do
    # Extract the filename without the path and extension
    peer_id=$(basename "$peer_data_file" .json)

    # Read the consensus keys
    consensus_public_key=$(jq -r '.consensus.publicKey' "$peer_data_file")
    consensus_private_key=$(jq -r '.consensus.privateKey' "$peer_data_file")

    # Append watcher party
    watcher_party=$(jq -n \
      --arg peerId "$peer_id" \
      --arg publicKey "$consensus_public_key" \
      '.peerId = $peerId | .publicKey = $publicKey')
    watcher_parties+=("$watcher_party")

    if [ "$peer_id" = "$CERC_PEER_ID" ]; then
      # Export peer id
      peer_id_data=$(jq '.peerId' "$peer_data_file")
      echo "$peer_id_data" > "${PEER_ID_FILE}"

      # Set consensus keys for this peer
      CONSENSUS_PUBLIC_KEY=${consensus_public_key}
      CONSENSUS_PRIVATE_KEY=${consensus_private_key}
    fi
  done

  # Export watcher party file
  watcher_parties_json=$(printf '%s\n' "${watcher_parties[@]}" | jq -s .)
  echo "$watcher_parties_json" > "${WATCHER_PARTY_PEERS_FILE}"
  echo "Watcher party peers exported to ${WATCHER_PARTY_PEERS_FILE}"
else
  echo "Using generated peer id"
  echo "Consensus module disabled"

  # Set corresponding variables
  PEER_ID_FILE='./peers/peer-id.json'
  CONSENSUS_ENABLED=false
  WATCHER_PARTY_PEERS_FILE=''
  CONSENSUS_PUBLIC_KEY=''
  CONSENSUS_PRIVATE_KEY=''
fi

# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_RELAY_PEERS|${CERC_RELAY_PEERS}|g; \
    s|REPLACE_WITH_CERC_DENY_MULTIADDRS|${CERC_DENY_MULTIADDRS}|g; \
    s/REPLACE_WITH_CERC_PUBSUB/${CERC_PUBSUB}/g; \
    s/REPLACE_WITH_CERC_RELAY_ANNOUNCE_DOMAIN/${CERC_RELAY_ANNOUNCE_DOMAIN}/g; \
    s|REPLACE_WITH_CERC_RELAY_MULTIADDR|${CERC_RELAY_MULTIADDR}|g; \
    s|REPLACE_WITH_PEER_ID_FILE|${PEER_ID_FILE}|g; \
    s/REPLACE_WITH_CERC_ENABLE_PEER_L2_TXS/${CERC_ENABLE_PEER_L2_TXS}/g; \
    s/REPLACE_WITH_CERC_PRIVATE_KEY_PEER/${CERC_PRIVATE_KEY_PEER}/g; \
    s/REPLACE_WITH_CERC_PRIVATE_KEY_NITRO/${CERC_PRIVATE_KEY_NITRO}/g; \
    s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/g; \
    s/REPLACE_WITH_CONSENSUS_ENABLED/${CONSENSUS_ENABLED}/g; \
    s/REPLACE_WITH_CONSENSUS_PUBLIC_KEY/${CONSENSUS_PUBLIC_KEY}/g; \
    s/REPLACE_WITH_CONSENSUS_PRIVATE_KEY/${CONSENSUS_PRIVATE_KEY}/g; \
    s|REPLACE_WITH_WATCHER_PARTY_PEERS_FILE|${WATCHER_PARTY_PEERS_FILE}|g; \
    s|REPLACE_WITH_CERC_ETH_RPC_QUERY_ENDPOINT|${CERC_ETH_RPC_QUERY_ENDPOINT}|g; \
    s|REPLACE_WITH_CERC_ETH_RPC_MUTATION_ENDPOINT|${CERC_ETH_RPC_MUTATION_ENDPOINT}|g; \
    s/REPLACE_WITH_CERC_UPSTREAM_NITRO_ADDRESS/${CERC_UPSTREAM_NITRO_ADDRESS}/g; \
    s|REPLACE_WITH_CERC_UPSTREAM_NITRO_MULTIADDR|${CERC_UPSTREAM_NITRO_MULTIADDR}|g; \
    s/REPLACE_WITH_CERC_UPSTREAM_NITRO_PAY_AMOUNT/${CERC_UPSTREAM_NITRO_PAY_AMOUNT}/ ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/local.toml

echo 'yarn server'
yarn server
