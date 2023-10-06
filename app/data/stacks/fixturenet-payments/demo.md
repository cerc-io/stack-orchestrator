# Demo

Stack components:
* `ipld-eth-db` database for statediffed data
* Local geth + lighthouse blockchain "fixturenet" running in statediffing mode
* `ipld-eth-server` which runs an ETH RPC API and a GQL server; serves data from `ipld-eth-db`
* A go-nitro deployment acting as the Nitro node for `ipld-eth-server`
* A modified reverse payment proxy server (based on the one from go-nitro) that proxies requests to `ipld-eth-server`'s RPC endpoint; it talks to `ipld-eth-server`'s Nitro node to accept and validate payments required for configured RPC requests
* A MobyMask v3 watcher that pays the `ipld-eth-server` for ETH RPC requests
* A MobyMask v3 app that pays the watcher for reads (GQL queries) and writes
* An example ERC20 Ponder app that pays the `ipld-eth-server` for ETH RPC requests

## Setup

* On starting the stack, MobyMask watcher creates a payment channel with the `ipld-eth-server`'s Nitro node. Check watcher logs and wait for the same:

  ```bash
  docker logs -f $(docker ps -aq --filter name="mobymask-watcher-server")

  # Expected output:
  # vulcanize:server Peer ID: 12D3KooWKLqLWU82VU7jmsmQMruRvZWhoBoVsf1UHchM5Nuq9ymY
  # vulcanize:server Using chain URL http://fixturenet-eth-geth-1:8546 for Nitro node
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

* MetaMask flask wallet setup for running the MobyMask app:

  * Get the geth node’s port mapped to host:

    ```bash
    docker port payments-fixturenet-eth-geth-1-1 8545
    ```

  * In MetaMask, add a custom network with the following settings:

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

* Perform `DIRECT FUND` with the preset amount and wait for the MetaMask confirmation prompt to appear; confirm the transaction and wait for a ledger channel to be created with the watcher

* Perform `VIRTUAL FUND` with amount set to `10000` and wait for a payment channel to be created with the watcher

* Perform phisher status check queries now that a payment channel is created:

  * Check the watcher logs for received payments along with the GQL queries:

    ```bash
    # Expected output:
    # ...
    # laconic:payments Serving a paid query for 0x86804299822212c070178B5135Ba6DdAcFC357D3
    # vulcanize:resolver isPhisher 0x98ae4f9e9d01cc892adfe6871e1db0287039e0c183d3b5bb31d724228c114744 0x2B6AFbd4F479cE4101Df722cF4E05F941523EaD9 TWT:ash1
    # vulcanize:indexer isPhisher: db miss, fetching from upstream server
    # laconic:payments Making RPC call: eth_chainId
    # laconic:payments Making RPC call: eth_getBlockByHash
    # laconic:payments Making RPC call: eth_chainId
    # laconic:payments Making RPC call: eth_getStorageAt
    ```

  * The watcher makes several ETH RPC requests to `ipld-eth-server` to fetch data required for satisfying the GQL request(s); check the payment proxy server logs for charged RPC requests (`eth_getBlockByHash`, `eth_getBlockByNumber`, `eth_getStorageAt`):

    ```bash
    # Expected output:
    # ...
    # {"time":"2023-10-06T06:46:52.769009314Z","level":"DEBUG","msg":"Serving RPC request","method":"eth_chainId"}
    # {"time":"2023-10-06T06:46:52.773006426Z","level":"DEBUG","msg":"Serving RPC request","method":"eth_getBlockByNumber"}
    # {"time":"2023-10-06T06:46:52.811142054Z","level":"DEBUG","msg":"Request cost","cost-per-byte":1,"response-length":1480,"cost":1480,"method":"eth_getBlockByNumber"}
    # {"time":"2023-10-06T06:46:52.811418494Z","level":"DEBUG","msg":"sent message","address":"0xAAA6628Ec44A8a742987EF3A114dDFE2D4F7aDCE","method":"receive_voucher"}
    # {"time":"2023-10-06T06:46:52.812557482Z","level":"DEBUG","msg":"Received voucher","delta":5000}
    # ...
    # {"time":"2023-10-06T06:46:52.87525215Z","level":"DEBUG","msg":"Serving RPC request","method":"eth_getStorageAt"}
    # {"time":"2023-10-06T06:46:52.882859654Z","level":"DEBUG","msg":"Request cost","cost-per-byte":1,"response-length":104,"cost":104,"method":"eth_getStorageAt"}
    # {"time":"2023-10-06T06:46:52.882946485Z","level":"DEBUG","msg":"sent message","address":"0xAAA6628Ec44A8a742987EF3A114dDFE2D4F7aDCE","method":"receive_voucher"}
    # {"time":"2023-10-06T06:46:52.884012641Z","level":"DEBUG","msg":"Received voucher","delta":5000}
    # {"time":"2023-10-06T06:46:52.884032961Z","level":"DEBUG","msg":"Destination request","url":"http://ipld-eth-server:8081/"}
    ```

* Change the amount besides `PAY` button in debug panel to `>=100` for phisher reports next

* Perform a phisher report and check the watcher logs for received payments:

  ```bash
  # Expected output:
  # ...
  # vulcanize:libp2p-utils [6:50:2] Received a message on mobymask P2P network from peer: 12D3KooWRkxV9SX8uTUZYkbRjai4Fsn7yavB61J5TMnksixsabsP
  # ts-nitro:engine {"msg":"Received message","_msg":{"to":"0xBBB676","from":"0x868042","payloadSummaries":[],"proposalSummaries":[],"payments":[{"amount":200,"channelId":"0x557153d729cf3323c0bdb40a36b245f98c2d4562933ba2182c9d61c5cfeda948"}],"rejectedObjectives":[]}}
  # laconic:payments Received a payment voucher of 100 from 0x86804299822212c070178B5135Ba6DdAcFC357D3
  # vulcanize:libp2p-utils Payment received for a mutation request from 0x86804299822212c070178B5135Ba6DdAcFC357D3
  # vulcanize:libp2p-utils Transaction receipt for invoke message {
  #   to: '0x2B6AFbd4F479cE4101Df722cF4E05F941523EaD9',
  #   blockNumber: 232,
  #   blockHash: '0x6a188722c102662ea48af3786fe9db0d4b6c7ab7b27473eb0e628cf95746a244',
  #   transactionHash: '0x6521205db8a905b3222adc2b6855f9b2abc72580624d299bec2a35bcba173efa',
  #   effectiveGasPrice: '1500000007',
  #   gasUsed: '113355'
  # }
  ```

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

* On starting the Ponder app, it creates a payment channel with the `ipld-eth-server`'s Nitro node and then starts the historical sync service

* The sync service makes several ETH RPC requests to the `ipld-eth-server` to fetch required data; check the payment proxy server logs for charged RPC requests (`eth_getBlockByNumber`, `eth_getLogs`)

  ```bash
  # Expected output:
  # ...
  # {"time":"2023-10-06T06:51:45.214478402Z","level":"DEBUG","msg":"Serving RPC request","method":"eth_getBlockByNumber"}
  # {"time":"2023-10-06T06:51:45.22251171Z","level":"DEBUG","msg":"Request cost","cost-per-byte":1,"response-length":576,"cost":576,"method":"eth_getBlockByNumber"}
  # {"time":"2023-10-06T06:51:45.222641963Z","level":"DEBUG","msg":"sent message","address":"0xAAA6628Ec44A8a742987EF3A114dDFE2D4F7aDCE","method":"receive_voucher"}
  # {"time":"2023-10-06T06:51:45.224042391Z","level":"DEBUG","msg":"Received voucher","delta":5000}
  # {"time":"2023-10-06T06:51:45.224061411Z","level":"DEBUG","msg":"Destination request","url":"http://ipld-eth-server:8081/"}
  # {"time":"2023-10-06T06:51:45.242064953Z","level":"DEBUG","msg":"Serving RPC request","method":"eth_getLogs"}
  # {"time":"2023-10-06T06:51:45.249118517Z","level":"DEBUG","msg":"Request cost","cost-per-byte":1,"response-length":61,"cost":61,"method":"eth_getLogs"}
  # {"time":"2023-10-06T06:51:45.249189892Z","level":"DEBUG","msg":"sent message","address":"0xAAA6628Ec44A8a742987EF3A114dDFE2D4F7aDCE","method":"receive_voucher"}
  # {"time":"2023-10-06T06:51:45.249743149Z","level":"DEBUG","msg":"Received voucher","delta":5000}
  # {"time":"2023-10-06T06:51:45.249760631Z","level":"DEBUG","msg":"Destination request","url":"http://ipld-eth-server:8081/"}
  # ...
  ```

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

* On a fresh restart, clear activity tab data in MetaMask for concerned accounts
