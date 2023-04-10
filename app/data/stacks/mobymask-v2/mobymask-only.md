# MobyMask v2 watcher

Instructions to setup and deploy MobyMask v2 watcher independently

## Setup

Prerequisite: L2 Optimism Geth and Node RPC endpoints

Clone required repositories:

```bash
laconic-so --stack mobymask-v2 setup-repositories --include cerc-io/MobyMask,cerc-io/watcher-ts
```

Checkout to the required versions and branches in repos:

```bash
# watcher-ts
cd ~/cerc/watcher-ts
git checkout v0.2.35

# MobyMask
cd ~/cerc/MobyMask
git checkout v0.1.2
```

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers --include cerc/watcher-mobymask-v2,cerc/mobymask
```

This should create the required docker images in the local image registry

## Deploy

### Configuration

* In [mobymask-params.env](../../config/watcher-mobymask-v2/mobymask-params.env) file set `DEPLOYED_CONTRACT` to existing deployed mobymask contract address
  * Setting `DEPLOYED_CONTRACT` will skip contract deployment when running stack
  * `ENABLE_PEER_L2_TXS` is used to enable/disable sending txs to L2 chain from watcher peer.
* Update the [optimism-params.env](../../config/watcher-mobymask-v2/optimism-params.env) file with Optimism endpoints and other params for the Optimism running separately
  * `PRIVATE_KEY_PEER` is used by watcher peer to send txs to L2 chain
* NOTE:
  * Stack Orchestrator needs to be run in [`dev`](/docs/CONTRIBUTING.md#install-developer-mode) mode to be able to edit the env file
  * If Optimism is running on the host machine, use `host.docker.internal` as the hostname to access the host port

### Deploy the stack

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

## Tests

See [Tests](./README.md#tests)

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack mobymask-v2 deploy --include watcher-mobymask-v2 down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=.*mobymask_watcher_db_data|.*mobymask_deployment|.*fixturenet_geth_accounts"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*mobymask_watcher_db_data|.*mobymask_deployment|.*fixturenet_geth_accounts")
```
