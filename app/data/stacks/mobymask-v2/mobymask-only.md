# MobyMask v2 watcher

Instructions to setup and deploy MobyMask v2 watcher independently

## Setup

Prerequisite: An L2 Optimism RPC endpoint

Clone required repositories:

```bash
laconic-so --stack mobymask-v2 setup-repositories --include cerc-io/MobyMask,cerc-io/watcher-ts,cerc-io/react-peer,cerc-io/mobymask-ui
```

Checkout to the required versions and branches in repos:

```bash
```bash
# watcher-ts
cd ~/cerc/watcher-ts
git checkout v0.2.34

# react-peer
cd ~/cerc/react-peer
git checkout v0.2.31

# mobymask-ui
cd ~/cerc/mobymask-ui
git checkout laconic

# MobyMask
cd ~/cerc/MobyMask
# TODO: Checkout to updated version
git checkout v0.1.1

# Optimism
cd ~/cerc/optimism
git checkout @eth-optimism/sdk@0.0.0-20230329025055
```

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers --include cerc/watcher-mobymask-v2,cerc/react-peer,cerc/mobymask-ui,cerc/mobymask
```

This should create the required docker images in the local image registry

## Deploy

Update the [optimism-params.env](../../config/watcher-mobymask-v2/optimism-params.env) file with Optimism endpoints and other params if running Optimism separately

* NOTE:
  * Stack Orchestrator needs to be run in [`dev`](/docs/CONTRIBUTING.md#install-developer-mode) mode to be able to edit the env file
  * If Optimism is running on the host machine, use `host.docker.internal` as the hostname to access the host port

Deploy the stack:

```bash
laconic-so --stack mobymask-v2 deploy --include watcher-mobymask-v2 up
```

To list down and monitor the running containers:

```bash
laconic-so --stack mobymask-v2 deploy ps
# With status
docker ps
# Check logs for a container
docker logs -f <CONTAINER_ID>
```

## Tests

Find the watcher container's id and export it for later use:

```bash
laconic-so --stack mobymask-v2 deploy-system --include watcher-mobymask-v2 ps | grep "mobymask-watcher-server"

export CONTAINER_ID=<CONTAINER_ID>
```

Example output:

```
id: 5d3aae4b22039fcd1c9b18feeb91318ede1100581e75bb5ac54f9e436066b02c, name: laconic-bfb01caf98b1b8f7c8db4d33f11b905a-mobymask-watcher-server-1, ports: 0.0.0.0:3001->3001/tcp, 0.0.0.0:9001->9001/tcp, 0.0.0.0:9090->9090/tcp
```

In above output the container ID is `5d3aae4b22039fcd1c9b18feeb91318ede1100581e75bb5ac54f9e436066b02c`

Run the peer tests:

```bash
docker exec -w /app/packages/peer $CONTAINER_ID yarn test
```

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack mobymask-v2 deploy down --include watcher-mobymask-v2
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter name=laconic*
# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter name=laconic*)
```
