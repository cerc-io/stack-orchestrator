# Demo

Stack components:
* `ipld-eth-db` database for statediffed data
* Local geth + lighthouse blockchain "fixturenet" running in statediffing mode
* `ipld-eth-server-1` which runs an ETH RPC API and a GQL server; they both serve data from `ipld-eth-db`
  * It runs an in-process go-nitro node for payments required for configured RPC requests
* A MobyMask v3 watcher that pays the `ipld-eth-server-1` for ETH RPC requests
* A MobyMask v3 app that pays the watcher for reads (GQL queries) and writes

## Setup

* On starting the stack, MobyMask watcher creates a payment channel with the `ipld-eth-server-1`'s (in-process) Nitro node. Check watcher logs and wait for the same:

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
  docker exec payments-nitro-rpc-client-1 npm exec -c "nitro-rpc-client get-payment-channel $WATCHER_UPSTREAM_PAYMENT_CHANNEL -s false -h ipld-eth-server-1 -p 4005"

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

* In another terminal, check `ipld-eth-server-1`'s logs to keep track of incoming payments and RPC requests from the MobyMask watcher:

  ```bash
  docker logs -f $(docker ps -aq --filter name="ipld-eth-server-1")
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
    # laconic:payments Received a payment voucher of 50 from 0x86804299822212c070178B5135Ba6DdAcFC357D3
    # laconic:payments Serving a paid query for 0x86804299822212c070178B5135Ba6DdAcFC357D3
    # vulcanize:resolver isPhisher 0x98ae4f9e9d01cc892adfe6871e1db0287039e0c183d3b5bb31d724228c114744 0x2B6AFbd4F479cE4101Df722cF4E05F941523EaD9 TWT:ash1
    # vulcanize:indexer isPhisher: db miss, fetching from upstream server
    # laconic:payments Making RPC call: eth_chainId
    # laconic:payments Making RPC call: eth_getBlockByHash
    # 2023-10-13T06:33:58.443Z ts-nitro:engine{"msg":"Sent message","_msg":{"to":"0xAAA662","from":"0xBBB676", "payloadSummaries":[],"proposalSummaries":[],"payments":[{"amount":200,"channelId":"0x9a4bdfe03c8e72f368aab07e6bd18f1cd6821170e1a93e59864aad6ee6a853a2"}],"rejectedObjectives":[]}}
    # laconic:payments Making RPC call: eth_chainId
    # laconic:payments Making RPC call: eth_getStorageAt
    # 2023-10-13T06:34:00.483Z ts-nitro:engine {"msg":"Sent message","_msg":{"to":"0xAAA662","from":"0xBBB676",# "payloadSummaries":[],"proposalSummaries":[],"payments":[{"amount":300,"channelId":"0x9a4bdfe03c8e72f368aab07e6bd18f1cd6821170e1a93e59864aad6ee6a853a2"}],"rejectedObjectives":[]}}
    ```

  * The watcher makes several ETH RPC requests to `ipld-eth-server-1` to fetch data required for satisfying the GQL request(s); check `ipld-eth-server-1` logs for charged RPC requests (`eth_getBlockByHash`, `eth_getBlockByNumber`, `eth_getStorageAt`):

    ```bash
    # Expected output:
    # ...
    # 2023/10/13 06:34:57 INFO Received a voucher payer=0xBBB676f9cFF8D242e9eaC39D063848807d3D1D94 amount=100
    #  2023/10/13 06:34:59 INFO Serving a paid RPC request method=eth_getBlockByHash cost=50 sender=0xBBB676f9cFF8D242e9eaC39D063848807d3D1D94
    #  time="2023-10-13T06:34:59Z" level=debug msg=START api_method=eth_getBlockByHash api_params="[0x46411a554f30e607bdd79cd157a60a7c8b314c0709557be3357ed2fef53d6c3d false]" api_reqid=52 conn="192.168.64.4:59644" user_id= uuid=a1893211-6992-11ee-a67a-0242c0a8400c
    #  WARN [10-13|06:34:59.133] Attempting GerRPCCalls, but default PluginLoader has not been initialized
    #  time="2023-10-13T06:34:59Z" level=debug msg=END api_method=eth_getBlockByHash api_params="[0x46411a554f30e607bdd79cd157a60a7c8b314c0709557be3357ed2fef53d6c3d false]" api_reqid=52 conn="192.168.64.4:59644" duration=5 user_id= uuid=a1893211-6992-11ee-a67a-0242c0a8400c
    #  2023/10/13 06:34:59 INFO Serving a free RPC request method=eth_chainId
    #  time="2023-10-13T06:34:59Z" level=debug msg=START api_method=eth_chainId api_params="[]" api_reqid=53 conn="192.168.64.4:59658" user_id= uuid=a18a96d9-6992-11ee-a67a-0242c0a8400c
    #  time="2023-10-13T06:34:59Z" level=debug msg=END api_method=eth_chainId api_params="[]" api_reqid=53 conn="192.168.64.4:59658" duration=0 user_id= uuid=a18a96d9-6992-11ee-a67a-0242c0a8400c
    #  2023/10/13 06:34:59 INFO Received a voucher payer=0xBBB676f9cFF8D242e9eaC39D063848807d3D1D94 amount=100
    #  2023/10/13 06:35:01 INFO Serving a paid RPC request method=eth_getStorageAt cost=50 sender=0xBBB676f9cFF8D242e9eaC39D063848807d3D1D94
    #  time="2023-10-13T06:35:01Z" level=debug msg=START api_method=eth_getStorageAt api_params="[0x2b6afbd4f479ce4101df722cf4e05f941523ead9 0xf76621c2cc1c1705fabbc22d30ffc5ded7f26e4995feb8d1c9812a2697ba1278 0x46411a554f30e607bdd79cd157a60a7c8b314c0709557be3357ed2fef53d6c3d]" api_reqid=54 conn="192.168.64.4:59660" user_id= uuid=a2bd75d2-6992-11ee-a67a-0242c0a8400c
    #  time="2023-10-13T06:35:01Z" level=debug msg=END api_method=eth_getStorageAt api_params="[0x2b6afbd4f479ce4101df722cf4e05f941523ead9 0xf76621c2cc1c1705fabbc22d30ffc5ded7f26e4995feb8d1c9812a2697ba1278 0x46411a554f30e607bdd79cd157a60a7c8b314c0709557be3357ed2fef53d6c3d]" api_reqid=54 conn="192.168.64.4:59660" duration=7 user_id= uuid=a2bd75d2-6992-11ee-a67a-0242c0a8400c
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

* Check the watcher - ipld-eth-server-1 payment channel status after a few requests:

  ```bash
  docker exec payments-nitro-rpc-client-1 npm exec -c "nitro-rpc-client get-payment-channel $WATCHER_UPSTREAM_PAYMENT_CHANNEL -s false -h ipld-eth-server-1 -p 4005"

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


## Clean Up

* In the MobyMask app, perform `VIRTUAL DEFUND` and `DIRECT DEFUND` (in order) for closing the payment channel created with watcher

* Run the following in the browser console to delete the Nitro node's data:

  ```bash
  await clearNodeStorage()
  ```

* Run the following in the browser console to clear data in local storage:
  ```bash
  localStorage.clear()
  ```

* On a fresh restart, clear activity tab data in MetaMask for concerned accounts
