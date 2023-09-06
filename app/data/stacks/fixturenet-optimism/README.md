# fixturenet-optimism

Instructions to setup and deploy an end-to-end L1+L2 stack with [fixturenet-eth](../fixturenet-eth/) (L1) and [Optimism](https://stack.optimism.io) (L2)

We support running just the L2 part of stack, given an external L1 endpoint. Follow the [L2 only doc](./l2-only.md) for the same.

## Setup

Clone required repositories:

```bash
laconic-so --stack fixturenet-optimism setup-repositories

# If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the repositories mentioned below and re-run the command
```

Build the container images:

```bash
laconic-so --stack fixturenet-optimism build-containers

# If redeploying with changes in the stack containers
laconic-so --stack fixturenet-optimism build-containers --force-rebuild

# If errors are thrown during build, old images used by this stack would have to be deleted
```

Note: this will take >10 mins depending on the specs of your machine, and **requires** 16GB of memory or greater.

This should create the required docker images in the local image registry:
* `cerc/go-ethereum`
* `cerc/lighthouse`
* `cerc/fixturenet-eth-geth`
* `cerc/fixturenet-eth-lighthouse`
* `cerc/foundry`
* `cerc/optimism-contracts`
* `cerc/optimism-l2geth`
* `cerc/optimism-op-node`
* `cerc/optimism-op-batcher`
* `cerc/optimism-op-proposer`

## Deploy

Deploy the stack:

```bash
laconic-so --stack fixturenet-optimism deploy up
```

The `fixturenet-optimism-contracts` service takes a while to complete running as it:
1. waits for the 'Merge' to happen on L1
2. waits for a finalized block to exist on L1 (so that it can be taken as a starting block for roll ups)
3. deploys the L1 contracts
It may restart a few times after running into errors.

To list and monitor the running containers:

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
laconic-so --stack fixturenet-optimism deploy down 30
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=.*l1_deployment|.*l2_accounts|.*l2_config|.*l2_geth_data"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*l1_deployment|.*l2_accounts|.*l2_config|.*l2_geth_data")
```

## Troubleshooting

* If `op-geth` service aborts or is restarted, the following error might occur in the `op-node` service:

  ```bash
  WARN [02-16|21:22:02.868] Derivation process temporary error       attempts=14 err="stage 0 failed resetting: temp: failed to find the L2 Heads to start from: failed to fetch L2 block by hash 0x0000000000000000000000000000000000000000000000000000000000000000: failed to determine block-hash of hash 0x0000000000000000000000000000000000000000000000000000000000000000, could not get payload: not found"
  ```

* This means that the data directory that `op-geth` is using is corrupted and needs to be reinitialized; the containers `op-geth`, `op-node` and `op-batcher` need to be started afresh:

  WARNING: This will reset the L2 chain; consequently, all the data on it will be lost

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

  * Re-run the deployment command used in [Deploy](#deploy) to restart the stopped containers

## Known Issues

* Resource requirements (memory + time) for building the `cerc/foundry` image are on the higher side
  * `cerc/optimism-contracts` image is currently based on `cerc/foundry` (Optimism requires foundry installation)
