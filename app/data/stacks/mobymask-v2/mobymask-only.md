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

Create an env file to be used in the next step:

  ```bash
  # External L2 endpoints
  L2_GETH_RPC=
  L2_GETH_HOST=
  L2_GETH_PORT=

  L2_NODE_HOST=
  L2_NODE_PORT=

  # Credentials for accounts to perform txs on L2
  PRIVATE_KEY_DEPLOYER=
  PRIVATE_KEY_PEER=

  # Base URI for mobymask-app (used for generating invite)
  MOBYMASK_APP_BASE_URI="http://127.0.0.1:3002/#"

  # Set to false for disabling watcher peer to send txs to L2
  ENABLE_PEER_L2_TXS=true

  # Set deployed MobyMask contract address to avoid deploying contract in the stack
  # mobymask-app will use this contract address in config if run separately
  DEPLOYED_CONTRACT=
  ```

* NOTE: If Optimism is running on the host machine, use `host.docker.internal` as the hostname to access the host port

### Deploy the stack

```bash
laconic-so --stack mobymask-v2 deploy --include watcher-mobymask-v2 --env-file <PATH_TO_ENV_FILE> up
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
