# Web Apps

Instructions to setup and deploy MobyMask and Peer Test web apps

## Setup

Prerequisite: Watcher with GQL and relay node endpoints

Clone required repositories:

```bash
laconic-so --stack mobymask-v2 setup-repositories --include cerc-io/react-peer,cerc-io/mobymask-ui

# If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the repositories mentioned below and re-run the command
```

Checkout to the required versions and branches in repos:

```bash
# react-peer
cd ~/cerc/react-peer
git checkout v0.2.31

# mobymask-ui
cd ~/cerc/mobymask-ui
git checkout laconic
```

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers --include cerc/react-peer-v2,cerc/mobymask-ui
```

This should create the required docker images in the local image registry

## Deploy

### Configuration

Create and update an env file to be used in the next step ([defaults](../../config/watcher-mobymask-v2/mobymask-params.env)):

  ```bash
  # Set relay nodes to be used by the web-app
  RELAY_NODES=["/ip4/127.0.0.1/tcp/9090/ws/p2p/12D3KooWSPCsVkHVyLQoCqhu2YRPvvM7o6r6NRYyLM5zeA6Uig5t"]

  # Also add if running MobyMask app:

  # External watcher endpoint (to check if watcher is up)
  WATCHER_HOST=
  WATCHER_PORT=

  # Watcher endpoint used by the app for GQL queries
  APP_WATCHER_URL="http://127.0.0.1:3001"

  # Set deployed MobyMask contract address to be used in MobyMask app's config
  DEPLOYED_CONTRACT=

  # L2 Chain ID used by mobymask web-app for L2 txs
  CHAIN_ID=42069
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
docker volume ls -q --filter "name=.*mobymask_deployment"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*mobymask_deployment")
```
