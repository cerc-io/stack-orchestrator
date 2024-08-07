# Graph Node

## Setup

Clone required repositories:

```bash
laconic-so --stack graph-node setup-repositories --pull
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
laconic-so --stack graph-node build-containers
```

## Create a deployment

Initialize deployment and create "spec" file:

```bash
laconic-so --stack graph-node deploy init --output graph-node-spec.yml
```

We need to assign fixed ports: `8000` for subgraph GQL endpoint, `8020` for subgraph deployment and `5001` for IPFS. The values can be
customized by editing the "spec" file generated by `laconic-so deploy init`.
```
$ cat graph-node-spec.yml
stack: graph-node
network:
  ports:
    graph-node:
      - '8000:8000'
      - '8001'
      - '8020:8020'
      - '8030'
      - '8040'
    ipfs:
      - '8080'
      - '4001'
      - '5001:5001'
...
```

Create deployment:

```bash
laconic-so --stack graph-node deploy create --spec-file graph-node-spec.yml --deployment-dir graph-node-deployment
```

## Start the stack

Update `config.env` file inside deployment directory with the following values before starting the stack:

```bash
# Set ETH RPC endpoint the graph node will use

# Host and port of the ETH RPC endpoint to check before starting graph-node
export ETH_RPC_HOST=
export ETH_RPC_PORT=

# The etherum network(s) graph-node will connect to
# Set this to a space-separated list of the networks where each entry has the form NAME:URL
export ETH_NETWORKS=

# Optional:

# Timeout for ETH RPC requests in seconds (default: 180s)
export GRAPH_ETHEREUM_JSON_RPC_TIMEOUT=

# Number of times to retry ETH RPC requests (default: 10)
export GRAPH_ETHEREUM_REQUEST_RETRIES=

# Maximum number of blocks to scan for triggers in each request (default: 2000)
export GRAPH_ETHEREUM_MAX_BLOCK_RANGE_SIZE=

# Maximum number of concurrent requests made against Ethereum for requesting transaction receipts during block ingestion (default: 1000)
export GRAPH_ETHEREUM_BLOCK_INGESTOR_MAX_CONCURRENT_JSON_RPC_CALLS_FOR_TXN_RECEIPTS=

# Ref: https://git.vdb.to/cerc-io/graph-node/src/branch/master/docs/environment-variables.md
```

Example `config.env` file:

```bash
export ETH_RPC_HOST=filecoin.chainup.net
export ETH_RPC_PORT=443

export ETH_NETWORKS=filecoin:https://filecoin.chainup.net/rpc/v1

export GRAPH_ETHEREUM_JSON_RPC_TIMEOUT=360
export GRAPH_ETHEREUM_REQUEST_RETRIES=5
export GRAPH_ETHEREUM_MAX_BLOCK_RANGE_SIZE=50
```

Deploy the stack:

```bash
laconic-so deployment --dir graph-node-deployment start

# Note: Remove any existing volumes in the cluster for a fresh start
```

After all services have started, follow `graph-node` logs:

```bash
laconic-so deployment --dir graph-node-deployment logs -f graph-node
```

Subgraphs can now be deployed to the graph-node.
Follow [Deploy the Subgraph](https://github.com/graphprotocol/graph-node/blob/v0.32.0/docs/getting-started.md#24-deploy-the-subgraph) section in graph-node docs for an existing subgraph.

## Set environment variables

* The graph-node environment variable `ETHEREUM_REORG_THRESHOLD` can be set in the deployment compose file
  ```bash
  $ cat graph-node-deployment/compose/docker-compose-graph-node.yml
  services:
    graph-node:
      image: cerc/graph-node:local
      ...
      environment:
        ...
        GRAPH_LOG: debug
        ETHEREUM_REORG_THRESHOLD: 3
  ```
  Change `ETHEREUM_REORG_THRESHOLD` to desired value

  * To restart graph-node with updated values
    * Stop the stack first
      ```bash
      laconic-so deployment --dir graph-node-deployment stop
      ```
    * Start the stack again
      ```
      laconic-so deployment --dir graph-node-deployment start
      ```
  * To check if environment variable has been updated in graph-node container
      ```bash
      $ laconic-so deployment --dir graph-node-deployment exec graph-node bash
      root@dc4d3abe1615:/# echo $ETHEREUM_REORG_THRESHOLD
      16
      ```

## Clean up

Stop all the services running in background run:

```bash
laconic-so deployment --dir graph-node-deployment stop
```

Clear volumes created by this stack:

```bash
laconic-so deployment --dir graph-node-deployment stop --delete-volumes
```
