# SushiSwap Graph

## Setup

Clone required repositories:

```bash
laconic-so --stack sushiswap-subgraph setup-repositories
```

Build the container images:

```bash
laconic-so --stack sushiswap-subgraph build-containers
```

## Deploy

Deploy the stack:

```bash
laconic-so --stack sushiswap-subgraph deploy --cluster sushigraph up
```

## Clean up

Stop all the services running in background run:

```bash
laconic-so --stack sushiswap-subgraph deploy --cluster sushigraph down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=sushigraph"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=sushigraph")
```
