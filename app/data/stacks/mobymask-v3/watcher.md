# MobyMask v3 Watcher

## Setup

Prerequisite: L2 Optimism Geth and Node RPC endpoints

Clone required repositories:

```bash
laconic-so --stack mobymask-v3 setup-repositories --pull --exclude github.com/cerc-io/mobymask-ui
```

Build the container images:

```bash
laconic-so --stack mobymask-v3 build-containers --exclude cerc/mobymask-ui
```

## Deploy

### Configuration

Create and update an env file to be used in the next step ([defaults](../../config/watcher-mobymask-v3/mobymask-params.env)):

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

  # Base URI for mobymask-app
  # (used for generating a root invite link after deploying the contract)
  CERC_MOBYMASK_APP_BASE_URI="http://127.0.0.1:3004/#"

  # (Optional) Domain to be used in the relay node's announce address
  CERC_RELAY_ANNOUNCE_DOMAIN=

  # (Optional) Set of relay peers to connect to from the relay node
  CERC_RELAY_PEERS=[]

  # (Optional) Set of multiaddrs to be avoided while dialling
  CERC_DENY_MULTIADDRS=[]

  # (Optional) Type of pubsub to be used
  CERC_PUBSUB=""

  # Set to false for disabling watcher peer to send txs to L2
  CERC_ENABLE_PEER_L2_TXS=true

  # (Optional) Set already deployed MobyMask contract address to avoid deploying contract in the stack
  CERC_DEPLOYED_CONTRACT=

  # (Optional) Set already deployed Nitro addresses to avoid deploying them in the stack
  CERC_NA_ADDRESS=
  CERC_VPA_ADDRESS=
  CERC_CA_ADDRESS=

  # Specify private key of a funded account for sending txs to L2
  CERC_PRIVATE_KEY_PEER=

  # Specify private key for the Nitro account
  CERC_PRIVATE_KEY_NITRO=

  # (Optional) Set a pre-existing peer id to be used (enables consensus)
  # Uses a generated peer id if not set (disables consensus)
  CERC_PEER_ID=
  ```

* NOTE: If Optimism is running on the host machine, use `host.docker.internal` as the hostname to access the host port

### Deploy the stack

```bash
laconic-so --stack mobymask-v3 deploy --cluster mobymask_v3 --include watcher-mobymask-v3 --env-file <PATH_TO_ENV_FILE> up
```

* To list down and monitor the running containers:

  ```bash
  laconic-so --stack mobymask-v3 deploy --cluster mobymask_v3 --include watcher-mobymask-v3 ps

  # With status
  docker ps -a

  # Check logs for a container
  docker logs -f <CONTAINER_ID>
  ```

* The watcher endpoint is exposed on host port `3001` and the relay node endpoint is exposed on host port `9090`

* Check the logs of the MobyMask contract deployment container to get the deployed contract's address and generated root invite link:

  ```bash
  docker logs -f $(docker ps -aq --filter name="mobymask-1")
  ```

* Check the logs of the watcher server container to get the deployed Nitro contracts' addresses:

```bash
docker exec -it $(docker ps -q --filter name="mobymask-watcher-server") bash -c "cat /nitro/nitro-addresses.json"
```

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack mobymask-v3 deploy --cluster mobymask_v3 --include watcher-mobymask-v3 down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=mobymask_v3"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=mobymask_v3")

# WARNING: To avoid changing peer ids for the watcher, `peers_ids` volume can be persisted
# To delete all volumes except for `peers_ids`
docker volume rm $(docker volume ls -q --filter "name=mobymask_v3" | grep -v "peers_ids$")
```
