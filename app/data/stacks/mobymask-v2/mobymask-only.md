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
git checkout v0.1.2
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
laconic-so --stack mobymask-v2 deploy --include watcher-mobymask-v2 ps
# With status
docker ps
# Check logs for a container
docker logs -f <CONTAINER_ID>
```

See [Tests](./README.md#tests) and [Demo](./README.md#demo) to interact with stack

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack mobymask-v2 deploy down --include watcher-mobymask-v2
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=.*mobymask_watcher_db_data|.*moby_data_server|.*fixturenet_geth_accounts"
# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*mobymask_watcher_db_data|.*moby_data_server|.*fixturenet_geth_accounts")
```
