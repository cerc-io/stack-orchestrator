#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

watcher_keys_dir="./keys"

echo "Watcher index: ${CERC_WATCHER_INDEX}"
echo "Using RPC query endpoint ${CERC_ETH_RPC_QUERY_ENDPOINT}"
echo "Using RPC mutation endpoint ${CERC_ETH_RPC_MUTATION_ENDPOINT}"
echo "Using Nitro chain URL ${CERC_NITRO_CHAIN_URL}"

WATCHER_DB="mobymask-watcher-${CERC_WATCHER_INDEX}"

# Use the docker container's host IP for relay multiaddr in peer config
CERC_RELAY_MULTIADDR="/dns4/mobymask-watcher-${CERC_WATCHER_INDEX}-server/tcp/9090/ws/p2p/$(jq -r '.relayPeerId.id' ${watcher_keys_dir}/watcher-${CERC_WATCHER_INDEX}.json)"

# Assign deployed contract address from server config (created by mobymask container after deploying contract)
CONTRACT_ADDRESS=$(jq -r '.address' /server/config.json | tr -d '"')

nitro_addresses_file="/nitro/nitro-addresses.json"
nitro_addresses_destination_file="./src/nitro-addresses.json"
if [ -f ${nitro_addresses_file} ]; then
  echo "Using Nitro addresses from ${nitro_addresses_file}:"
  cat "$nitro_addresses_file"
  cat "$nitro_addresses_file" > "$nitro_addresses_destination_file"
else
  echo "Nitro addresses not available"
  exit 1
fi

# Build after setting the Nitro addresses
yarn build

PEER_ID_FILE='./peer-id.json'
RELAY_PEER_ID_FILE='./relay-id.json'

# Create watcher party array
watcher_parties=()

# Iterate over each fixture JSON file
for watcher_keys_file in "$watcher_keys_dir"/*.json; do
  # Extract the filename without the path and extension
  filename=$(basename "$watcher_keys_file" .json)

  # Read the consensus keys
  peer_id=$(jq -r '.peerId.id' "$watcher_keys_file")

  # Read the consensus keys
  consensus_public_key=$(jq -r '.consensus.publicKey' "$watcher_keys_file")
  consensus_private_key=$(jq -r '.consensus.privateKey' "$watcher_keys_file")

  # Append watcher party
  watcher_party=$(jq -n \
    --arg peerId "$peer_id" \
    --arg publicKey "$consensus_public_key" \
    '.peerId = $peerId | .publicKey = $publicKey')
  watcher_parties+=("$watcher_party")

  if [ "$filename" = "watcher-${CERC_WATCHER_INDEX}" ]; then
    # Export watcher peer and relay ids
    peer_id_data=$(jq '.peerId' "$watcher_keys_file")
    relay_peer_id_data=$(jq '.relayPeerId' "$watcher_keys_file")
    echo "$peer_id_data" > "${PEER_ID_FILE}"
    echo "$relay_peer_id_data" > "${RELAY_PEER_ID_FILE}"

    # Set peer and nitro account keys
    CERC_PRIVATE_KEY_PEER=$(jq -r '.peer.privateKey' "$watcher_keys_file")
    CERC_WATCHER_NITRO_PK=$(jq -r '.peer.nitroPrivateKey' "$watcher_keys_file")

    # Set consensus keys for this peer
    CONSENSUS_PUBLIC_KEY=${consensus_public_key}
    CONSENSUS_PRIVATE_KEY=${consensus_private_key}
  fi
done

echo "Consensus module enabled"
CONSENSUS_ENABLED=true
WATCHER_PARTY_PEERS_FILE='./watcher-party-peers.json'

# Export watcher party file
watcher_parties_json=$(printf '%s\n' "${watcher_parties[@]}" | jq -s .)
echo "$watcher_parties_json" > "${WATCHER_PARTY_PEERS_FILE}"
echo "Watcher party peers exported to ${WATCHER_PARTY_PEERS_FILE}"

# Configure relay peers for watcher 2 and 3
CERC_RELAY_PEERS=[]
if [ "${CERC_WATCHER_INDEX}" = "2" ]; then
  # 2 -> 1
  CERC_RELAY_PEERS="['/dns4/mobymask-watcher-1-server/tcp/9090/ws/p2p/$(jq -r '.relayPeerId.id' ${watcher_keys_dir}/watcher-1.json)']"
elif [ "${CERC_WATCHER_INDEX}" = "3" ]; then
  # 3 -> 1, 2
  CERC_RELAY_PEERS="['/dns4/mobymask-watcher-1-server/tcp/9090/ws/p2p/$(jq -r '.relayPeerId.id' ${watcher_keys_dir}/watcher-1.json)', '/dns4/mobymask-watcher-2-server/tcp/9090/ws/p2p/$(jq -r '.relayPeerId.id' ${watcher_keys_dir}/watcher-2.json)']"
fi

# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_RELAY_PEERS|${CERC_RELAY_PEERS}|g; \
    s|REPLACE_WITH_CERC_RELAY_MULTIADDR|${CERC_RELAY_MULTIADDR}|g; \
    s/REPLACE_WITH_CERC_PRIVATE_KEY_PEER/${CERC_PRIVATE_KEY_PEER}/g; \
    s/REPLACE_WITH_CERC_WATCHER_NITRO_PK/${CERC_WATCHER_NITRO_PK}/g; \
    s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/g; \
    s|REPLACE_WITH_CERC_NITRO_CHAIN_URL|${CERC_NITRO_CHAIN_URL}|g; \
    s/REPLACE_WITH_CONSENSUS_ENABLED/${CONSENSUS_ENABLED}/g; \
    s/REPLACE_WITH_CONSENSUS_PUBLIC_KEY/${CONSENSUS_PUBLIC_KEY}/g; \
    s/REPLACE_WITH_CONSENSUS_PRIVATE_KEY/${CONSENSUS_PRIVATE_KEY}/g; \
    s|REPLACE_WITH_WATCHER_PARTY_PEERS_FILE|${WATCHER_PARTY_PEERS_FILE}|g; \
    s|REPLACE_WITH_CERC_ETH_RPC_QUERY_ENDPOINT|${CERC_ETH_RPC_QUERY_ENDPOINT}|g; \
    s|REPLACE_WITH_CERC_ETH_RPC_MUTATION_ENDPOINT|${CERC_ETH_RPC_MUTATION_ENDPOINT}|g; \
    s|REPLACE_WITH_WATCHER_DB|${WATCHER_DB}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/local.toml

echo 'Running watcher server'
yarn server
