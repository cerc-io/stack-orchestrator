# fixturenet-optimism

Instructions to setup and deploy an end-to-end L1+L2 stack with [fixturenet-eth](../fixturenet-eth/) (L1) and [Optimism](https://stack.optimism.io) (L2)

## Setup

Clone required repositories:

```bash
laconic-so --stack fixturenet-optimism setup-repositories

# Exclude cerc-io/go-ethereum repository if running L1 separately
laconic-so --stack fixturenet-optimism setup-repositories --exclude cerc-io/go-ethereum
```

Checkout to the required versions and branches in repos:

```bash
# Optimism
cd ~/cerc/optimism
git checkout @eth-optimism/sdk@0.0.0-20230329025055
```

Build the container images:

```bash
laconic-so --stack fixturenet-optimism build-containers

# Only build containers required for L2 if running L1 separately
laconic-so --stack fixturenet-optimism build-containers --include cerc/foundry,cerc/optimism-contracts,cerc/optimism-op-node,cerc/optimism-l2geth,cerc/optimism-op-batcher
```

This should create the required docker images in the local image registry:
* `cerc/go-ethereum`
* `cerc/lighthouse`
* `cerc/fixturenet-eth-geth`
* `cerc/fixturenet-eth-lighthouse`
* `cerc/foundry`
* `cerc/optimism-contracts`
* `cerc/optimism-l2geth`
* `cerc/optimism-op-batcher`
* `cerc/optimism-op-node`

## Deploy

(Optional) Update the [l1-params.env](../../config/fixturenet-optimism/l1-params.env) file with L1 endpoint (`L1_RPC`, `L1_HOST` and `L1_PORT`) and other params if running L1 separately

* NOTE:
  * Stack Orchestrator needs to be run in [`dev`](/docs/CONTRIBUTING.md#install-developer-mode) mode to be able to edit the env file
  * If L1 is running on the host machine, use `host.docker.internal` as the hostname to access the host port

Deploy the stack:

```bash
laconic-so --stack fixturenet-optimism deploy up

# Only start fixturenet-optimism pod (L2) if running L1 separately
laconic-so --stack fixturenet-optimism deploy up --include fixturenet-optimism
```

The `fixturenet-optimism-contracts` service may take a while (`~15 mins`) to complete running as it:
1. waits for the 'Merge' to happen on L1
2. waits for a finalized block to exist on L1 (so that it can be taken as a starting block for roll ups)
3. deploys the L1 contracts

To list down and monitor the running containers:

```bash
laconic-so --stack fixturenet-optimism deploy ps

# With status
docker ps

# Check logs for a container
docker logs -f <CONTAINER_ID>
```

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack fixturenet-optimism deploy down

# If only ran fixturenet-optimism pod (L2)
laconic-so --stack fixturenet-optimism deploy down --include fixturenet-optimism
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter name=laconic*

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter name=laconic*)
```

## Known Issues

* `fixturenet-eth` currently starts fresh on a restart
* Resource requirements (memory + time) for building the `cerc/foundry` image are on the higher side
  * `cerc/optimism-contracts` image is currently based on `cerc/foundry` (Optimism requires foundry installation)

## Troubleshooting

* If `op-geth` service aborts or is restarted, the following error might occur in the `op-node` service:

  ```bash
  WARN [02-16|21:22:02.868] Derivation process temporary error       attempts=14 err="stage 0 failed resetting: temp: failed to find the L2 Heads to start from: failed to fetch L2 block by hash 0x0000000000000000000000000000000000000000000000000000000000000000: failed to determine block-hash of hash 0x0000000000000000000000000000000000000000000000000000000000000000, could not get payload: not found"
  ```

* This means that the data directory that `op-geth` is using is corrupted and needs to be reinitialized; the containers `op-geth`, `op-node` and `op-batcher` need to be started afresh:
  * Stop and remove the concerned containers:

    ```bash
    # List the containers
    docker ps -f "name=op-geth|op-node|op-batcher"

    # Force stop and remove the listed containers
    docker rm -f $(docker ps -qf "name=op-geth|op-node|op-batcher")
    ```

  * Remove the concerned volume:

    ```bash
    # List the volume
    docker volume ls -q --filter name=l2_geth_data

    # Remove the listed volume
    docker volume rm $(docker volume ls -q --filter name=l2_geth_data)
    ```

  * Reuse the deployment command used in [Deploy](#deploy) to restart the stopped containers
