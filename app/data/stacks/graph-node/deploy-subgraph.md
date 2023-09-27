# Deploying Subgraph

## Setup

We will use the [ethereum-gravatar](https://github.com/graphprotocol/graph-tooling/tree/%40graphprotocol/graph-cli%400.58.0/examples/ethereum-gravatar) example subgraph from `graphprotocol/graph-tooling` repo

- Clone the repo
  ```bash
  git clone git@github.com:graphprotocol/graph-tooling.git
  
  cd graph-tooling
  ```

- Install dependencies
  ```bash
  pnpm install
  ```

- Change directory to example-subgraph
  ```bash
  cd examples/ethereum-gravatar
  ```

## Deploy

The following steps should be similar for every subgraph

- Change the network and address in `subgraph.yaml`
  ```yaml
  ...
  dataSources:
  - kind: ethereum/contract
    name: Gravity
    network: <NETWORK_NAME>
    source:
      address: '<CONTRACT_ADDRESS>'
      abi: Gravity
      startBlock: <START_BLOCK>
  ...
  ```
  - `CONTRACT_ADDRESS` is the address of the deployed contract on the desired network
  - `START_BLOCK` is the block number after which we want to process events
  - `NETWORK_NAME` is the name of the network specified when deploying graph-node
    - When deploying graph-node `ETH_NETWORKS` env is set to a space-separated list of the networks where each entry has the form `NAME:URL`
    - The `NAME` can be used in subgraph to specify which network to use
    - More details can be seen in [Start the stack](./README.md#start-the-stack) section

- Build the subgraph
  ```bash
  pnpm codegen
  pnpm build
  ```

- Create and deploy the subgraph
  ```bash
  pnpm graph create example --node <GRAPH_NODE_DEPLOY_ENDPOINT>
  
  pnpm graph deploy example --ipfs <GRAPH_NODE_IPFS_ENDPOINT> --node <GRAPH_NODE_DEPLOY_ENDPOINT>
  ```
  - `GRAPH_NODE_DEPLOY_ENDPOINT` and `GRAPH_NODE_IPFS_ENDPOINT` will be available after graph-node has been deployed
  - More details can be seen in [Create a deployment](./README.md#create-a-deployment) section 

- The subgraph GQL endpoint will be seen after deploy command runs successfully

- To remove the subgraph
  ```bash
  pnpm graph remove --node <GRAPH_NODE_DEPLOY_ENDPOINT> example
  ```
