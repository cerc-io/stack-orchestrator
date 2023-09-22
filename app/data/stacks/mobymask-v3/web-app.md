# MobyMask v3 App

## Setup

Prerequisite: Watcher with GQL and relay node endpoints

Clone required repositories:

```bash
laconic-so --stack mobymask-v3 setup-repositories --pull --include github.com/cerc-io/mobymask-ui
```

Build the container images:

```bash
laconic-so --stack mobymask-v3 build-containers --include cerc/mobymask-ui
```

## Deploy

### Configuration

Create and update an env file to be used in the next step ([defaults](../../config/watcher-mobymask-v3/mobymask-params.env)):

  ```bash
  # Set of relay nodes to be used by the web-app
  # (use double quotes " for strings, avoid space after commas)
  # Eg. CERC_RELAY_NODES=["/dns4/example.com/tcp/443/wss/p2p/12D3KooWGHmDDCc93XUWL16FMcTPCGu2zFaMkf67k8HZ4gdQbRDr"]
  CERC_RELAY_NODES=[]

  # Set of multiaddrs to be avoided while dialling
  CERC_DENY_MULTIADDRS=[]

  # Also add if running MobyMask app:

  # Watcher endpoint used by the app for GQL queries
  CERC_APP_WATCHER_URL="http://127.0.0.1:3001"

  # Set deployed MobyMask contract address to be used in MobyMask app's config
  CERC_DEPLOYED_CONTRACT=

  # L2 Chain ID used by mobymask web-app for L2 txs
  CERC_CHAIN_ID=42069

  # (Optional) Type of pubsub to be used ("floodsub" | "gossipsub")
  CERC_PUBSUB=""

  # (Optional) Set of direct peers to be used when pubsub is set to gossipsub
  CERC_GOSSIPSUB_DIRECT_PEERS=[]

  # Set Nitro addresses
  CERC_NA_ADDRESS=
  CERC_VPA_ADDRESS=
  CERC_CA_ADDRESS=

  # Nitro account address to make the query and mutation payments to
  CERC_PAYMENT_NITRO_ADDRESS=

  # Endpoint for Mobymask snap installation
  CERC_SNAP_URL=
  ```

### Deploy the stack

```bash
laconic-so --stack mobymask-v3 deploy --cluster mobymask_v3 --include mobymask-app-v3 --env-file <PATH_TO_ENV_FILE> up

# Runs the MobyMask v3 app on host port 3004
```

To list down and monitor the running containers:

```bash
laconic-so --stack mobymask-v3 deploy --cluster mobymask_v3 --include mobymask-app-v3 ps

# With status
docker ps -a

# Check logs for a container
docker logs -f <CONTAINER_ID>
```

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack mobymask-v3 deploy --cluster mobymask_v3 --include mobymask-app-v3 down
```
