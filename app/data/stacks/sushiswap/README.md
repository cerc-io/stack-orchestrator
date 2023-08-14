# SushiSwap

## Setup

Clone required repositories:

```bash
laconic-so --stack sushiswap setup-repositories --git-ssh
```

Build the container images:

```bash
laconic-so --stack sushiswap build-containers
```

## Deploy

Deploy the stack:

```bash
laconic-so --stack sushiswap deploy --cluster sushiswap up
```

Note: When running for the first time (or after clean up), the services will take some time to start as Lotus nodes in the fixturenet download the proof params

## Tests

Follow [smoke-tests.md](./smoke-tests.md) to run smoke tests

## Clean up

Stop all the services running in background:

```bash
laconic-so --stack sushiswap deploy --cluster sushiswap down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=sushiswap"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=sushiswap")
```
