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

After all services have started, wait and check that the subgraph has been deployed to graph-node

```bash
laconic-so --stack sushiswap-subgraph deploy --cluster sushigraph logs -f sushiswap-subgraph-v3

# Expected end output
# ...
# sushigraph-sushiswap-subgraph-v3-1  | - Deploying to Graph node http://graph-node:8020/
# sushigraph-sushiswap-subgraph-v3-1  | Deployed to http://graph-node:8000/subgraphs/name/sushiswap/v3-lotus/graphql
# sushigraph-sushiswap-subgraph-v3-1  |
# sushigraph-sushiswap-subgraph-v3-1  | Subgraph endpoints:
# sushigraph-sushiswap-subgraph-v3-1  | Queries (HTTP):     http://graph-node:8000/subgraphs/name/sushiswap/v3-lotus
# sushigraph-sushiswap-subgraph-v3-1  |
# sushigraph-sushiswap-subgraph-v3-1  | Done
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

# WARNING: After removing volumes with Lotus params
# They will be downloaded again on restart

# To remove volumes that do not contain Lotus params
docker volume rm $(docker volume ls -q --filter "name=sushigraph" | grep -v "params$")
```
