# ERC20 Watcher

Instructions to deploy a local ERC20 watcher stack (core + watcher) for demonstration and testing purposes using [laconic-stack-orchestrator](../../README.md#setup)

## Setup

* Clone / pull required repositories:

  ```bash
  $ laconic-so setup-repositories --include cerc-io/go-ethereum,cerc-io/ipld-eth-db,cerc-io/ipld-eth-server,cerc-io/watcher-ts --pull
  ```

* Build the core and watcher container images:

  ```bash
  $ laconic-so build-containers --include cerc/go-ethereum,cerc/go-ethereum-foundry,cerc/ipld-eth-db,cerc/ipld-eth-server,cerc/watcher-erc20
  ```

  This should create the required docker images in the local image registry.

* Deploy the stack:

  ```bash
  $ laconic-so deploy-system --include db,go-ethereum-foundry,ipld-eth-server,watcher-erc20 up
  ```

## Demo

* Find the watcher container's id using `docker ps` and export it for later use:

  ```bash
  $ export CONTAINER_ID=<CONTAINER_ID>
  ```

* Deploy an ERC20 token:

  ```bash
  $ docker exec $CONTAINER_ID yarn token:deploy:docker
  ```

  Export the address of the deployed token to a shell variable for later use:

  ```bash
  $ export TOKEN_ADDRESS=<TOKEN_ADDRESS>
  ```

* Open `http://localhost:3001/graphql` (GraphQL Playground) in a browser window

* Connect MetaMask to `http://localhost:8545` (with chain ID `99`)

* Add the deployed token as an asset in MetaMask and check that the initial balance is zero

* Export your MetaMask account (second account) address to a shell variable for later use:

  ```bash
  $ export RECIPIENT_ADDRESS=<RECIPIENT_ADDRESS>
  ```

* To get the primary account's address, run:

  ```bash
  $ docker exec $CONTAINER_ID yarn account:docker
  ```

* To get the current block hash at any time, run:

  ```bash
  $ docker exec $CONTAINER_ID yarn block:latest:docker
  ```

* Fire a GQL query in the playground to get the name, symbol and total supply of the deployed token:

  ```graphql
  query {
    name(
      blockHash: "LATEST_BLOCK_HASH"
      token: "TOKEN_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }

    symbol(
      blockHash: "LATEST_BLOCK_HASH"
      token: "TOKEN_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }

    totalSupply(
      blockHash: "LATEST_BLOCK_HASH"
      token: "TOKEN_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }
  }
  ```

* Fire the following query to get balances for the primary and the recipient account at the latest block hash:

  ```graphql
  query {
    fromBalanceOf: balanceOf(
        blockHash: "LATEST_BLOCK_HASH"
        token: "TOKEN_ADDRESS",
        # primary account having all the balance initially
        owner: "PRIMARY_ADDRESS"
      ) {
      value
      proof {
        data
      }
    }
    toBalanceOf: balanceOf(
        blockHash: "LATEST_BLOCK_HASH"
        token: "TOKEN_ADDRESS",
        owner: "RECIPIENT_ADDRESS"
      ) {
      value
      proof {
        data
      }
    }
  }
  ```

  * The initial balance for the primary account should be `1000000000000000000000`
  * The initial balance for the recipient should be `0`

* Transfer tokens to the recipient account:

  ```bash
  $ docker exec $CONTAINER_ID yarn token:transfer:docker --token $TOKEN_ADDRESS --to $RECIPIENT_ADDRESS --amount 100
  ```

* Fire the above GQL query again with the latest block hash to get updated balances for the primary (`from`) and the recipient (`to`) account:

  * The balance for the primary account should be reduced by the transfer amount (`100`)
  * The balance for the recipient account should be equal to the transfer amount (`100`)

* Transfer funds between different accounts using MetaMask and use the playground to query the balance before and after the transfer.

## Clean up

* To stop all the services running in background run:

  ```bash
  $ laconic-so deploy-system --include db,go-ethereum-foundry,ipld-eth-server,watcher-erc20 down
  ```
