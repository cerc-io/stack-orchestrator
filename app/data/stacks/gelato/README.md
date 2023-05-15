# Gelato watcher

Instructions to setup and deploy Gelato watcher using [laconic-stack-orchestrator](/README.md#install)

## Setup

Prerequisite: `ipld-eth-server` endpoints

Clone required repositories:

```bash
laconic-so --stack gelato setup-repositories

# If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the repositories mentioned below and re-run the command
```

Checkout to required version in the repo:

```bash
# gelato-watcher-ts
cd ~/cerc/gelato-watcher-ts
git checkout v0.1.0
```

Build the container images:

```bash
laconic-so --stack gelato build-containers
```

This should create the required docker images in the local image registry.

## Deploy

### Configuration

Create and update an env file to be used in the next step ([defaults](../../config/watcher-gelato/watcher-params.env)):

  ```bash
  # External ipld-eth-server endpoints
  CERC_ETH_SERVER_GQL_ENDPOINT=
  CERC_ETH_SERVER_RPC_ENDPOINT=

  # Whether to use a state snapshot to initialize the watcher
  CERC_USE_STATE_SNAPSHOT=false

  # State snapshot params
  # Required if CERC_USE_STATE_SNAPSHOT is set to true
  CERC_SNAPSHOT_GQL_ENDPOINT=
  CERC_SNAPSHOT_BLOCKHASH=
  ```

* NOTE: If `ipld-eth-server` is running on the host machine, use `host.docker.internal` as the hostname to access the host port(s)

### Deploy the stack

```bash
laconic-so --stack gelato deploy --env-file <PATH_TO_ENV_FILE> up
```

To list down and monitor the running containers:

```bash
laconic-so --stack gelato deploy ps

# With status
docker ps

# Check logs for a container
docker logs -f <CONTAINER_ID>
```

The stack runs an active watcher with following endpoints exposed on the host ports:
* `3008`: watcher endpoint
* `9000`: watcher metrics
* `9001`: watcher GQL metrics

## Web Apps

TODO

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack gelato deploy down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=.*gelato_watcher_db_data|.*gelato_watcher_state_gql"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*gelato_watcher_db_data|.*gelato_watcher_state_gql")
```
