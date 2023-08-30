# Fixturenet SushiSwap Subgraph

## Setup

Clone required repositories:

```bash
laconic-so --stack fixturenet-sushiswap-subgraph setup-repositories --pull
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
laconic-so --stack fixturenet-sushiswap-subgraph build-containers
```

## Deploy


Create an env file with the following contents to be used in the next step:

```bash
# Network and ETH RPC endpoint to run graph-node against
NETWORK=lotus-fixturenet
ETH_RPC_ENDPOINT=http://lotus-node-1:1234/rpc/v1
```

Deploy the stack:

```bash
laconic-so --stack fixturenet-sushiswap-subgraph deploy --cluster sushigraph --env-file <PATH_TO_ENV_FILE> up

# Note: Remove any existing volumes for the cluster for a fresh start
```

After all services have started:

* Follow `graph-node` logs:

  ```bash
  laconic-so --stack fixturenet-sushiswap-subgraph deploy --cluster sushigraph logs -f graph-node
  ```

* Check that the subgraphs have been deployed:

  ```bash
  laconic-so --stack fixturenet-sushiswap-subgraph deploy --cluster sushigraph logs -f sushiswap-subgraph-v3

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
laconic-so --stack fixturenet-sushiswap-subgraph deploy --cluster sushigraph port graph-node 8000
# 0.0.0.0:HOST_PORT

# Blocks subgraph endpoint:
http://127.0.0.1:<HOST_PORT>/subgraphs/name/sushiswap/blocks/graphql

# v3 subgraph endpoint:
http://127.0.0.1:<HOST_PORT>/subgraphs/name/sushiswap/v3-filecoin/graphql
```

## Run

* Deploy an ERC20 token:

  ```bash
  docker exec -it sushigraph-sushiswap-v3-periphery-1 yarn hardhat --network docker deploy --tags TestERC20

  # Deploy two tokens and set the addresses to variables TOKEN1_ADDRESS and TOKEN2_ADDRESS
  export TOKEN1_ADDRESS=<TOKEN1_ADDRESS>
  export TOKEN2_ADDRESS=<TOKEN2_ADDRESS>
  ```

* Get contract address of factory deployed:

  ```bash
  docker exec -it sushigraph-sushiswap-v3-core-1 jq -r '.address' /app/deployments/docker/UniswapV3Factory.json

  # Set the address to variable FACTORY_ADDRESS
  export FACTORY_ADDRESS=<FACTORY_ADDRESS>
  ```

* Create a pool:

  ```bash
  docker exec -it sushigraph-sushiswap-v3-core-1 pnpm run pool:create:docker --factory $FACTORY_ADDRESS --token0 $TOKEN1_ADDRESS --token1 $TOKEN2_ADDRESS --fee 500

  # Set the created pool address to variable POOL_ADDRESS
  export POOL_ADDRESS=<POOL_ADDRESS>
  ```

* Initialize pool:

  ```bash
  docker exec -it sushigraph-sushiswap-v3-core-1 pnpm run pool:initialize:docker --sqrt-price 4295128939 --pool $POOL_ADDRESS
  ```

* Set the recipient address to the contract deployer:

  ```bash
  export RECIPIENT=0xD375B03bd3A2434A9f675bEC4Ccd68aC5e67C743
  ```

* Trigger pool `Mint` event:

  ```bash
  docker exec -it sushigraph-sushiswap-v3-core-1 pnpm run pool:mint:docker --pool $POOL_ADDRESS --recipient $RECIPIENT --amount 10
  ```

* Trigger pool `Burn` event:

  ```bash
  docker exec -it sushigraph-sushiswap-v3-core-1 pnpm run pool:burn:docker --pool $POOL_ADDRESS --amount 10
  ```

## Clean up

Stop all the services running in background run:

```bash
laconic-so --stack fixturenet-sushiswap-subgraph deploy --cluster sushigraph down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=sushigraph"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=sushigraph")

# WARNING: To avoid refetching the Lotus proof params on the next run,
# avoid removing the corresponding volumes

# To remove volumes that do not contain Lotus params
docker volume rm $(docker volume ls -q --filter "name=sushigraph" | grep -v "params$")
```
