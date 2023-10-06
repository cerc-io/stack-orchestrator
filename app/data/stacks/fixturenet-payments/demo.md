# Demo

Stack components:
* `ipld-eth-db` database for statediffed data
* Local geth + lighthouse blockchain "fixturenet" running in statediffing mode
* `ipld-eth-server` which runs an ETH RPC API and a GQL server; serves data from `ipld-eth-db`
* A go-nitro node acting as the Nitro node for `ipld-eth-server`
* A reverse payment proxy server that proxies requests to `ipld-eth-server`'s RPC endpoint; it talks to `ipld-eth-server`'s go-nitro node to validate payments required for configured RPC requests
* A MobyMask v3 watcher that pays the `ipld-eth-server` for ETH RPC requests
* A MobyMask v3 app that pays the watcher for GQL requests (queries + mutations)
* An example ERC20 Ponder app that pays the `ipld-eth-server` for ETH RPC requests

## Setup

* On starting the stack, MobyMask watcher creates a payment channel with the `ipld-eth-server`'s go-nitro node. Check watcher logs and wait for the same:

  ```bash
  docker logs -f $(docker ps -aq --filter name="mobymask-watcher-server")

  # Expected output:
  # vulcanize:server Using rpcProviderEndpoint as chain URL for Nitro node +0ms
  # ...
  # ts-nitro:util:nitro Ledger channel created with id 0x65703ccdfacab09ac35367bdbe6c5a337e7a6651aad526807607b1c59b28bc1e
  # ...
  # ts-nitro:util:nitro Virtual payment channel created with id 0x29ff1335d73391a50e8fde3e9b34f00c3d81c39ddc7f89187f44dd51df96140e
  # vulcanize:server Starting server... +0ms
  ```

* Keep the above command running to keep track of incoming payments and GQL requests from the MobyMask app

* In another terminal, export the payment channel id to a variable:

  ```bash
  export WATCHER_UPSTREAM_PAYMENT_CHANNEL=<PAYMENT_CHANNEL_ID>
  ```

* Check the payment channel status:

  ```bash
  docker exec payments-nitro-rpc-client-1 npm exec -c "nitro-rpc-client get-payment-channel $WATCHER_UPSTREAM_PAYMENT_CHANNEL -h go-nitro -p 4005"

  # Expected output:
  # {
  #   ID: '0x8c0d17639bd2ba07dbcd248304a8f3c6c7276bfe25c2b87fe41f461e20f33f01',
  #   Status: 'Open',
  #   Balance: {
  #     AssetAddress: '0x0000000000000000000000000000000000000000',
  #     Payee: '0xaaa6628ec44a8a742987ef3a114ddfe2d4f7adce',
  #     Payer: '0xbbb676f9cff8d242e9eac39d063848807d3d1d94',
  #     PaidSoFar: 0n,
  #     RemainingFunds: 1000000000n
  #   }
  # }
  ```

* In another terminal, check the reverse payment proxy server's logs to keep track of incoming payments and RPC requests:

  ```bash
  docker logs -f $(docker ps -aq --filter name="nitro-reverse-payment-proxy")
  ```

* MetaMask wallet setup for running the MobyMask app:

  * Get the geth node’s port mapped to host:

    ```bash
    docker port payments-fixturenet-eth-geth-1-1 8545
    ```

  * In MetaMask Flask, add a custom network with the following settings:

    ```bash
    # Network name
    Local fixturenet

    # New RPC URL
    http://127.0.0.1:<GETH_PORT>

    # Chain ID
    1212

    # Currency symbol
    ETH
    ```

  * Import a faucet account with the following private key:

    ```bash
    # Faucet PK
    # 0x570b909da9669b2f35a0b1ac70b8358516d55ae1b5b3710e95e9a94395090597
    ```

  * Create an additional account for usage in the app; fund it from the faucet account

* Get the generated root invite link for MobyMask from contract deployment container logs:

  ```bash
  docker logs -f $(docker ps -aq --filter name="mobymask-1")

  # Expected output:
  # ...
  #   "key": "0x60e706fda4639fe0a8eb102cb0ce81231cf6e819f41cb4eadf72d865ea4c11ad"
  # }
  # http://127.0.0.1:3004/#/members?invitation=<INVITATION>
  ```

## Run

### MobyMask App

* Open app in a browser (where MetaMask was setup) using the invite link

* Run the following in browser console to enable logs:

  ```bash
  localStorage.debug = 'ts-nitro:*'
  # Refresh the tab for taking effect
  ```

* In the app’s debug panel, check that the peer gets connected to relay node and watcher peer

* Open the `NITRO` tab in debug panel
  * Click on `Connect Wallet` to connect to MetaMask (make sure that the newly funded account is active)
  * Click on `Connect Snap` to install/connect snap

* Perform `DIRECT FUND` with the preset amount; confirm the transaction and wait for a ledger channel to be created with the watcher

* Perform `VIRTUAL FUND` with amount set to `10000` and wait for a payment channel to be created with the watcher

* Perform phisher status check queries now that a payment channel is created:
  * Check the watcher logs for received payments along with the GQL queries
  * The watcher makes several ETH RPC requests to `ipld-eth-server` to fetch data required for satisfying the GQL request(s); check the payment proxy server logs for charged RPC requests (`eth_getBlockByHash`, `eth_getBlockByNumber`, `eth_getStorageAt`)

* Change the amount besides `PAY` button to `>=100` for phisher reports next

* Perform a phisher report and check the watcher logs for received payments; the RPC mutation request is sent to geth node and is not charged

* Check the watcher - ipld-eth-server payment channel status after a few requests:

  ```bash
  docker exec payments-nitro-rpc-client-1 npm exec -c "nitro-rpc-client get-payment-channel $WATCHER_UPSTREAM_PAYMENT_CHANNEL -h go-nitro -p 4005"

  # Expected output ('PaidSoFar' should be non zero):
  # {
  #   ID: '0x8c0d17639bd2ba07dbcd248304a8f3c6c7276bfe25c2b87fe41f461e20f33f01',
  #   Status: 'Open',
  #   Balance: {
  #     AssetAddress: '0x0000000000000000000000000000000000000000',
  #     Payee: '0xaaa6628ec44a8a742987ef3a114ddfe2d4f7adce',
  #     Payer: '0xbbb676f9cff8d242e9eac39d063848807d3d1d94',
  #     PaidSoFar: 30000n,
  #     RemainingFunds: 999970000n
  #   }
  # }
  ```

### ERC20 Ponder App

* Run the ponder app in it's container:

  ```bash
  docker exec -it payments-ponder-app-1 bash -c "pnpm start"

  # Expected output:
  # 09:58:54.288 INFO  payment    Creating ledger channel with nitro node 0xAAA6628Ec44A8a742987EF3A114dDFE2D4F7aDCE
  # ...
  # 09:59:14.230 INFO  payment    Creating payment channel with nitro node 0xAAA6628Ec44A8a742987EF3A114dDFE2D4F7aDCE
  # ...
  # 09:59:14.329 INFO  payment    Using payment channel 0x10f049519bc3f862e2b26e974be8666886228f30ea54aab06e2f23718afffab0
  ```

* On starting the Ponder app, it creates a payment channel with the `ipld-eth-server`'s go-nitro node and then starts the historical sync service

* The sync service makes several ETH RPC requests to the `ipld-eth-server` to fetch required data; check the payment proxy server logs for charged RPC requests (`eth_getBlockByNumber`, `eth_getLogs`)

* Export the payment channel id to a variable:

  ```bash
  export PONDER_UPSTREAM_PAYMENT_CHANNEL=<PAYMENT_CHANNEL_ID>
  ```

* Check the ponder - ipld-eth-server payment channel status:

  ```bash
  docker exec payments-nitro-rpc-client-1 npm exec -c "nitro-rpc-client get-payment-channel $PONDER_UPSTREAM_PAYMENT_CHANNEL -h go-nitro -p 4005"

  # Expected output ('PaidSoFar' is non zero):
  # {
  #   ID: '0x1178ac0f2a43e54a122216fa6afdd30333b590e49e50317a1f9274a591da0f96',
  #   Status: 'Open',
  #   Balance: {
  #     AssetAddress: '0x0000000000000000000000000000000000000000',
  #     Payee: '0xaaa6628ec44a8a742987ef3a114ddfe2d4f7adce',
  #     Payer: '0x67d5b55604d1af90074fcb69b8c51838fff84f8d',
  #     PaidSoFar: 215000n,
  #     RemainingFunds: 999785000n
  #   }
  # }
  ```

## Clean Up

* In the MobyMask app, perform `VIRTUAL DEFUND` and `DIRECT DEFUND` (in order) for closing the payment channel created with watcher

* Run the following in the browser console to delete the Nitro node's data:

  ```bash
  await clearNodeStorage()
  ```

* On a restart, clear activity tab data in MetaMask for concerned accounts
