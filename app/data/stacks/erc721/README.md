# ERC721 Watcher

Instructions to deploy a local ERC721 watcher stack (core + watcher) for demonstration and testing purposes using [laconic-stack-orchestrator](../../README.md#setup)

## Setup

* Clone / pull required repositories:

  ```bash
  $ laconic-so setup-repositories --include cerc-io/go-ethereum,cerc-io/ipld-eth-db,cerc-io/ipld-eth-server,cerc-io/watcher-ts --pull
  ```

* Build the core and watcher container images:

  ```bash
  $ laconic-so build-containers --include cerc/go-ethereum,cerc/go-ethereum-foundry,cerc/ipld-eth-db,cerc/ipld-eth-server,cerc/watcher-erc721
  ```

  This should create the required docker images in the local image registry.

* Deploy the stack:

  ```bash
  $ laconic-so deploy-system --include db,go-ethereum-foundry,ipld-eth-server,watcher-erc721 up
  ```

## Demo

* Find the watcher container's id using `docker ps` and export it for later use:

  ```bash
  $ export CONTAINER_ID=<CONTAINER_ID>
  ```

* Deploy an ERC721 token:

  ```bash
  $ docker exec $CONTAINER_ID yarn nft:deploy:docker
  ```

  Export the address of the deployed token to a shell variable for later use:

  ```bash
  $ export NFT_ADDRESS=<NFT_ADDRESS>
  ```

* Open `http://localhost:3009/graphql` (GraphQL Playground) in a browser window

* Connect MetaMask to `http://localhost:8545` (with chain ID `99`)

* Export your MetaMask account (second account) address to a shell variable for later use:

  ```bash
  $ export RECIPIENT_ADDRESS=<RECIPIENT_ADDRESS>
  ```

* To get the primary account's address, run:

  ```bash
  $ docker exec $CONTAINER_ID yarn account:docker
  ```

  Export it to shell variable for later use:

  ```bash
  $ export PRIMARY_ADDRESS=<PRIMARY_ADDRESS>
  ```

* To get the current block hash at any time, run:

  ```bash
  $ docker exec $CONTAINER_ID yarn block:latest:docker
  ```

* Fire the following GQL query (uses `eth_call`) in the playground:

  ```graphql
  query {
    name(
      blockHash: "LATEST_BLOCK_HASH"
      contractAddress: "NFT_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }

    symbol(
      blockHash: "LATEST_BLOCK_HASH"
      contractAddress: "NFT_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }

    balanceOf(
      blockHash: "LATEST_BLOCK_HASH"
      contractAddress: "NFT_ADDRESS"
      owner: "PRIMARY_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }
  }
  ```

  Balance for the `PRIMARY_ADDRESS` should be `0` as the token is yet to be minted.

* Fire the following GQL query (uses `storage` calls) in the playground:

  ```graphql
  query {
    _name(
      blockHash: "LATEST_BLOCK_HASH"
      contractAddress: "NFT_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }

    _symbol(
      blockHash: "LATEST_BLOCK_HASH"
      contractAddress: "NFT_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }

    _balances(
      blockHash: "LATEST_BLOCK_HASH"
      contractAddress: "NFT_ADDRESS"
      key0: "PRIMARY_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }
  }
  ```

* Mint the token:

  ```bash
  $ docker exec $CONTAINER_ID yarn nft:mint:docker --nft $NFT_ADDRESS --to $PRIMARY_ADDRESS --token-id 1
  ```

  Fire the GQL query above again with latest block hash. The balance should increase to `1`.

* Get the latest block hash and run the following GQL query in the playground for `balanceOf` and `ownerOf` (`eth_call`):

  ```graphql
  query {
    fromBalanceOf: balanceOf(
      blockHash: "LATEST_BLOCK_HASH"
      contractAddress: "NFT_ADDRESS"
      owner: "PRIMARY_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }

    toBalanceOf: balanceOf(
      blockHash: "LATEST_BLOCK_HASH"
      contractAddress: "NFT_ADDRESS"
      owner: "RECIPIENT_ADDRESS"
    ) {
      value
      proof {
        data
      }
    }

    ownerOf(
      blockHash: "LATEST_BLOCK_HASH"
      contractAddress: "NFT_ADDRESS"
      tokenId: 1
    ) {
      value
      proof {
        data
      }
    }
  }
  ```

  Balance should be `1` for the `PRIMARY_ADDRESS`, `0` for the `RECIPIENT_ADDRESS` and owner value of the token should be equal to the `PRIMARY_ADDRESS`.

* Transfer the token:

  ```bash
  $ docker exec $CONTAINER_ID yarn nft:transfer:docker --nft $NFT_ADDRESS --from $PRIMARY_ADDRESS --to $RECIPIENT_ADDRESS --token-id 1
  ```

  Fire the GQL query above again with the latest block hash. The token should be transferred to the recipient.

## Clean up

* To stop all the services running in background:

  ```bash
  $ laconic-so deploy-system --include db,go-ethereum-foundry,ipld-eth-server,watcher-erc721 down
  ```
