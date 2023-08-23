# SushiSwap Subgraph

## Setup

Clone required repositories:

```bash
laconic-so --stack sushiswap-subgraph setup-repositories --pull
```

Checkout to a non-default branch in the cloned repos if required:

```bash
# Default repo base dir
cd ~/cerc

# Example
cd graph-node
git checkout <your-branch> && git pull

# Remove the corresponding docker image if it already exists
docker image rm cerc/graph-node:local
# Remove any dangling images
docker image prune
```

Build the container images:

```bash
laconic-so --stack sushiswap-subgraph build-containers
```

## Deploy

Deploy the stack:

```bash
laconic-so --stack sushiswap-subgraph deploy --cluster sushigraph up

# Note: Remove any existing volumes for the cluster for a fresh start
```

After all services have started:

* Follow `graph-node` logs:

  ```bash
  laconic-so --stack sushiswap-subgraph deploy --cluster sushigraph logs -f graph-node
  ```

* Check that the subgraphs have been deployed:

  ```bash
  laconic-so --stack sushiswap-subgraph deploy --cluster sushigraph logs -f sushiswap-subgraph-v3

  # Expected output:
  # .
  # .
  # sushigraph-sushiswap-subgraph-v3-1  | - Deploying to Graph node http://graph-node:8020/
  # sushigraph-sushiswap-subgraph-v3-1  | Deployed to http://graph-node:8000/subgraphs/name/sushiswap/blocks/graphql
  # sushigraph-sushiswap-subgraph-v3-1  |
  # sushigraph-sushiswap-subgraph-v3-1  |
  # sushigraph-sushiswap-subgraph-v3-1  | Subgraph endpoints:
  # sushigraph-sushiswap-subgraph-v3-1  | Queries (HTTP):     http://graph-node:8000/subgraphs/name/sushiswap/blocks
  # .
  # .
  # sushigraph-sushiswap-subgraph-v3-1  | - Deploying to Graph node http://graph-node:8020/
  # sushigraph-sushiswap-subgraph-v3-1  | Deployed to http://graph-node:8000/subgraphs/name/sushiswap/v3-filecoin/graphql
  # sushigraph-sushiswap-subgraph-v3-1  |
  # sushigraph-sushiswap-subgraph-v3-1  |
  # sushigraph-sushiswap-subgraph-v3-1  | Subgraph endpoints:
  # sushigraph-sushiswap-subgraph-v3-1  | Queries (HTTP):     http://graph-node:8000/subgraphs/name/sushiswap/v3-filecoin
  # sushigraph-sushiswap-subgraph-v3-1  |
  # sushigraph-sushiswap-subgraph-v3-1  |
  # sushigraph-sushiswap-subgraph-v3-1  | Done
  ```

After `graph-node` has fetched the latest blocks from upstream, use the subgraph (GQL) endpoints for querying:

```bash
# Find out the mapped host port for the subgraph endpoint
laconic-so --stack sushiswap-subgraph deploy --cluster sushigraph port graph-node 8000
# 0.0.0.0:HOST_PORT

# Blocks subgraph endpoint:
http://127.0.0.1:<HOST_PORT>/subgraphs/name/sushiswap/blocks/graphql

# v3 subgraph endpoint:
http://127.0.0.1:<HOST_PORT>/subgraphs/name/sushiswap/v3-filecoin/graphql
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
