# Web Apps

Instructions to setup and deploy MobyMask and Peer Test web apps

## Setup

Prerequisite: Watcher with GQL and relay node endpoints

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers --include cerc/react-peer,cerc/mobymask-ui
```

This should create the required docker images in the local image registry

## Deploy

### Configuration

Create and update an env file to be used in the next step ([defaults](../../config/watcher-mobymask-v2/mobymask-params.env)):

  ```bash
  # Set of relay nodes to be used by the web-app
  # (use double quotes " for strings)
  # Eg. CERC_RELAY_NODES=["/dns4/example.com/tcp/443/wss/p2p/12D3KooWGHmDDCc93XUWL16FMcTPCGu2zFaMkf67k8HZ4gdQbRDr"]
  CERC_RELAY_NODES=[]

  # Also add if running MobyMask app:

  # External watcher endpoint (to check if watcher is up)
  CERC_WATCHER_HOST=
  CERC_WATCHER_PORT=

  # Watcher endpoint used by the app for GQL queries
  CERC_APP_WATCHER_URL="http://127.0.0.1:3001"

  # Set deployed MobyMask contract address to be used in MobyMask app's config
  CERC_DEPLOYED_CONTRACT=

  # L2 Chain ID used by mobymask web-app for L2 txs
  CERC_CHAIN_ID=42069
  ```

* NOTE: If watcher is running on the host machine, use `host.docker.internal` as the hostname to access the host port

### Deploy the stack

For running mobymask-app
```bash
laconic-so --stack mobymask-v2 deploy --include mobymask-app --env-file <PATH_TO_ENV_FILE> up

# Runs on host port 3002
```

For running peer-test-app
```bash
laconic-so --stack mobymask-v2 deploy --include peer-test-app --env-file <PATH_TO_ENV_FILE> up

# Runs on host port 3003
```

To list down and monitor the running containers:

```bash
laconic-so --stack mobymask-v2 deploy --include [mobymask-app | peer-test-app] ps

docker ps

# Check logs for a container
docker logs -f <CONTAINER_ID>
```

## Demo

Follow the [demo](./demo.md) to try out the MobyMask app with L2 chain

## Clean up

Stop all services running in the background:

For mobymask-app
```bash
laconic-so --stack mobymask-v2 deploy --include mobymask-app down
```

For peer-test-app
```bash
laconic-so --stack mobymask-v2 deploy --include peer-test-app down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=.*mobymask_deployment|.*peers_ids"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*mobymask_deployment|.*peers_ids")
```
