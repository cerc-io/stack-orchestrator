# MobyMask v2 watcher

Instructions to setup and deploy MobyMask v2 watcher independently

## Setup

Prerequisite: L2 Optimism Geth and Node RPC endpoints

Clone required repositories:

```bash
laconic-so --stack mobymask-v2 setup-repositories --include github.com/cerc-io/MobyMask,github.com/cerc-io/watcher-ts,github.com/cerc-io/mobymask-v2-watcher-ts

# If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the repositories mentioned below and re-run the command
```

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers --include cerc/watcher-ts,cerc/watcher-mobymask-v2,cerc/mobymask
```

This should create the required docker images in the local image registry

## Deploy

### Configuration

Create and update an env file to be used in the next step ([defaults](../../config/watcher-mobymask-v2/)):

  ```bash
  # External L2 endpoints
  CERC_L2_GETH_RPC=

  # Endpoints waited on before contract deployment
  CERC_L2_GETH_HOST=
  CERC_L2_GETH_PORT=

  CERC_L2_NODE_HOST=
  CERC_L2_NODE_PORT=

  # URL (fixturenet-eth-bootnode-lighthouse) to get CSV with credentials for accounts on L1 to perform txs on L2
  CERC_L1_ACCOUNTS_CSV_URL=

  # OR
  # Specify the required account credentials
  CERC_PRIVATE_KEY_DEPLOYER=
  CERC_PRIVATE_KEY_PEER=

  # Base URI for mobymask-app
  # (used for generating a root invite link after deploying the contract)
  CERC_MOBYMASK_APP_BASE_URI="http://127.0.0.1:3004/#"

  # (Optional) Domain to be used in the relay node's announce address
  CERC_RELAY_ANNOUNCE_DOMAIN=

  # (Optional) Set of relay peers to connect to from the relay node
  CERC_RELAY_PEERS=[]

  # (Optional) Set of multiaddrs to be avoided while dialling
  CERC_DENY_MULTIADDRS=[]

  # Set to false for disabling watcher peer to send txs to L2
  CERC_ENABLE_PEER_L2_TXS=true

  # (Optional) Set already deployed MobyMask contract address to avoid deploying contract in the stack
  CERC_DEPLOYED_CONTRACT=
  ```

* NOTE: If Optimism is running on the host machine, use `host.docker.internal` as the hostname to access the host port

### Deploy the stack

```bash
laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 --include watcher-mobymask-v2 --env-file <PATH_TO_ENV_FILE> up
```

To list down and monitor the running containers:

```bash
laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 --include watcher-mobymask-v2 ps

# With status
docker ps -a

# Check logs for a container
docker logs -f <CONTAINER_ID>
```

The watcher endpoint is exposed on host port `3001` and the relay node endpoint is exposed on host port `9090`

Check the logs of the deployment container to get the deployed contract's address and generated root invite link:

```bash
docker logs -f $(docker ps -aq --filter name="mobymask-1")
```

## Tests

See [Tests](./README.md#tests)

## Web Apps

For deploying the web-app(s) separately after deploying the watcher, follow [web-apps.md](./web-apps.md)

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 --include watcher-mobymask-v2 down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=mobymask_v2"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=mobymask_v2")
```
