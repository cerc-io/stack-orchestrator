# fixturenet-optimism

Instructions to setup and deploy L2 fixturenet using [Optimism](https://stack.optimism.io)

## Setup

Prerequisite: An L1 Ethereum RPC endpoint

Clone required repositories:

```bash
laconic-so --stack fixturenet-optimism setup-repositories --exclude git.vdb.to/cerc-io/go-ethereum

# If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the repositories mentioned below and re-run the command
```

Build the container images:

```bash
laconic-so --stack fixturenet-optimism build-containers --include cerc/foundry,cerc/optimism-contracts,cerc/optimism-op-node,cerc/optimism-l2geth,cerc/optimism-op-batcher,cerc/optimism-op-proposer
```

This should create the required docker images in the local image registry:
* `cerc/foundry`
* `cerc/optimism-contracts`
* `cerc/optimism-l2geth`
* `cerc/optimism-op-node`
* `cerc/optimism-op-batcher`
* `cerc/optimism-op-proposer`

## Deploy

Create and update an env file to be used in the next step ([defaults](../../config/fixturenet-optimism/l1-params.env)):

  ```bash
  # External L1 endpoint
  CERC_L1_CHAIN_ID=
  CERC_L1_RPC=
  CERC_L1_HOST=
  CERC_L1_PORT=

  # URL to get CSV with credentials for accounts on L1
  # that are used to send balance to Optimism Proxy contract
  # (enables them to do transactions on L2)
  CERC_L1_ACCOUNTS_CSV_URL=

  # OR
  # Specify the required account credentials
  CERC_L1_ADDRESS=
  CERC_L1_PRIV_KEY=
  CERC_L1_ADDRESS_2=
  CERC_L1_PRIV_KEY_2=
  ```

* NOTE: If L1 is running on the host machine, use `host.docker.internal` as the hostname to access the host port

Deploy the stack:

```bash
laconic-so --stack fixturenet-optimism deploy --include fixturenet-optimism --env-file <PATH_TO_ENV_FILE> up
```

The `fixturenet-optimism-contracts` service may take a while (`~15 mins`) to complete running as it:
1. waits for the 'Merge' to happen on L1
2. waits for a finalized block to exist on L1 (so that it can be taken as a starting block for roll ups)
3. deploys the L1 contracts

To list down and monitor the running containers:

```bash
laconic-so --stack fixturenet-optimism deploy --include fixturenet-optimism ps

# With status
docker ps

# Check logs for a container
docker logs -f <CONTAINER_ID>
```

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack fixturenet-optimism deploy --include fixturenet-optimism down 30
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=.*l1_deployment|.*l2_accounts|.*l2_config|.*l2_geth_data"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*l1_deployment|.*l2_accounts|.*l2_config|.*l2_geth_data")
```

## Troubleshooting

See [Troubleshooting](./README.md#troubleshooting)
