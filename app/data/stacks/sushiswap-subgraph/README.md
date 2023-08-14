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

## Run

To check graph-node logs:
```bash
laconic-so --stack sushiswap-subgraph deploy --cluster sushigraph logs -f graph-node
```

To deploy tokens run:
```bash
docker exec -it sushigraph-sushiswap-v3-periphery-1 yarn hardhat --network docker deploy --tags TestERC20
```
This can be run multiple times to deploy ERC20 tokens

Take note of the deployed token addresses to use later

Get contract address of factory deployed:
```bash
docker exec -it sushigraph-sushiswap-v3-core-1 jq -r '.address' /app/deployments/docker/UniswapV3Factory.json
```
Set it to environment variable `FACTORY_ADDRESS` to use later

To create a pool:
```bash
docker exec -it sushigraph-sushiswap-v3-core-1 pnpm run pool:create:docker --factory $FACTORY_ADDRESS --token0 $TOKEN1_ADDRESS --token1 $TOKEN2_ADDRESS --fee 500
```

Set the created pool address to environment variable `POOL_ADDRESS` to use later

To initialize pool:
```bash
docker exec -it sushigraph-sushiswap-v3-core-1 pnpm run pool:initialize:docker --sqrt-price 4295128939 --pool $POOL_ADDRESS
```

Set the recipient address to the contract deployer:
```bash
export RECIPIENT=0xD375B03bd3A2434A9f675bEC4Ccd68aC5e67C743
```

Trigger pool mint event:
```bash
docker exec -it sushigraph-sushiswap-v3-core-1 pnpm run pool:mint:docker --pool $POOL_ADDRESS --recipient $RECIPIENT --amount 10
```

Trigger pool burn event:
```bash
docker exec -it sushigraph-sushiswap-v3-core-1 pnpm run pool:burn:docker --pool $POOL_ADDRESS --amount 10
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
