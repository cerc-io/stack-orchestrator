# Demo

Stack components:
* `ipld-eth-db` database for statediffed data
* Local geth + lighthouse blockchain "fixturenet" running in statediffing mode
* `ipld-eth-server-2` which runs an ETH RPC API and a GQL server; they both serve data from `ipld-eth-db`
* A go-nitro deployment acting as the remote Nitro node for `ipld-eth-server-2`
* Example ERC20 Ponder apps
  * `ponder-app-indexer-1` that pays the `ipld-eth-server-2` for ETH RPC requests
  * `ponder-app-indexer-2` that pays `ponder-app-indexer-1` for GQL queries
  * `ponder-app-watcher` that pays `ponder-app-indexer-2` for GQL queries

## Setup

* In a terminal, check `ipld-eth-server-2`'s logs to keep track of incoming RPC requests from the `ponder-app-indexer-1`:

  ```bash
  docker logs -f $(docker ps -aq --filter name="ipld-eth-server-2")
  ```

## Run

### ERC20 Ponder App

* Run the first indexer Ponder app:

  ```bash
  docker exec -it payments-ponder-app-indexer-1-1 bash -c "DEBUG=laconic:payments pnpm start"

  # Expected output:
  # 12:57:03.751 INFO  payment    Nitro node setup with address 0x67D5b55604d1aF90074FcB69b8C51838FFF84f8d
  #   laconic:payments Starting voucher subscription... +0ms
  # ...
  # 09:58:54.288 INFO  payment    Creating ledger channel with nitro node 0x660a4bEF3fbC863Fcd8D3CDB39242aE513d7D92e ...
  # 09:59:14.230 INFO  payment    Creating payment channel with nitro node 0x660a4bEF3fbC863Fcd8D3CDB39242aE513d7D92e ...
  # 09:59:14.329 INFO  payment    Using payment channel 0x1ff59db391b7a55bed723b930ab53c80e7ce857487c1e58771aa5a0737d71625
  ```

* Export the payment channel id to a variable:

  ```bash
  export PONDER_UPSTREAM_PAYMENT_CHANNEL=<PAYMENT_CHANNEL_ID>
  ```

* On starting the Ponder app in indexer mode, it creates a payment channel with the `ipld-eth-server-2`'s (external) Nitro node and then starts the historical sync service

* The sync service makes several ETH RPC requests to the `ipld-eth-server-2` to fetch required data; check the `ipld-eth-server-2` logs for charged RPC requests (`eth_getBlockByNumber`, `eth_getLogs`):

  ```bash
  # Expected output:
  # ...
  # 2023/10/18 05:29:38 INFO Serving a paid RPC request method=eth_getBlockByNumber cost=50 sender=0x67D5b55604d1aF90074FcB69b8C51838FFF84f8d
  # time="2023-10-18T05:29:38Z" level=debug msg=START api_method=eth_getBlockByNumber api_params="[latest true]" api_reqid=0 conn="172.26.0.19:42306" user_id= uuid=54992dc3-6d77-11ee-9ede-0242ac1a000f
  # WARN [10-18|05:29:38.292] Attempting GerRPCCalls, but default PluginLoader has not been initialized
  # time="2023-10-18T05:29:38Z" level=debug msg=END api_method=eth_getBlockByNumber api_params="[latest true]" api_reqid=0 conn="172.26.0.19:42306" duration=22 user_id= uuid=54992dc3-6d77-11ee-9ede-0242ac1a000f
  # ...
  # 2023/10/18 05:29:40 INFO Serving a paid RPC request method=eth_getLogs cost=50 sender=0x67D5b55604d1aF90074FcB69b8C51838FFF84f8d
  # WARN [10-18|05:29:40.340] Attempting GerRPCCalls, but default PluginLoader has not been initialized
  # time="2023-10-18T05:29:40Z" level=debug msg="retrieving log cids for receipt ids"
  # ...
  ```

* Check the Ponder - ipld-eth-server-2 payment channel status:

  ```bash
  docker exec payments-nitro-rpc-client-1 npm exec -c "nitro-rpc-client get-payment-channel $PONDER_UPSTREAM_PAYMENT_CHANNEL -s false -h go-nitro -p 4006"

  # Expected output ('PaidSoFar' is non zero):
  # {
  #   ID: '0x1ff59db391b7a55bed723b930ab53c80e7ce857487c1e58771aa5a0737d71625',
  #   Status: 'Open',
  #   Balance: {
  #     AssetAddress: '0x0000000000000000000000000000000000000000',
  #     Payee: '0x660a4bef3fbc863fcd8d3cdb39242ae513d7d92e',
  #     Payer: '0x67d5b55604d1af90074fcb69b8c51838fff84f8d',
  #     PaidSoFar: 7200n,
  #     RemainingFunds: 999992800n
  #   }
  # }
  ```

* In another terminal run the second indexer Ponder app:

  ```bash
  docker exec -it payments-ponder-app-indexer-2-1 bash -c "DEBUG=laconic:payments pnpm start"

  # Expected output:
  # 08:00:28.701 INFO  payment    Nitro node setup with address 0xB2B22ec3889d11f2ddb1A1Db11e80D20EF367c01
  #   laconic:payments Starting voucher subscription... +0ms
  # ...
  # 09:58:54.288 INFO  payment    Creating ledger channel with nitro node 0x67D5b55604d1aF90074FcB69b8C51838FFF84f8d ...
  # 09:59:14.230 INFO  payment    Creating payment channel with nitro node 0x67D5b55604d1aF90074FcB69b8C51838FFF84f8d ...
  # 09:59:14.329 INFO  payment    Using payment channel 0xfbf9d7eb7c18446883c7f57f4c94db5607f414a224b3e921c787db07371d2a70
  ```

* On starting indexer Ponder app, it creates a payment channel with first indexer and then starts the sync services

* Check logs in `ponder-indexer-1` to see payments made from `ponder-indexer-2` from GQL queries to fetch network data

  ```bash
  # ...
  #   laconic:payments Received a payment voucher of 100 from 0xB2B22ec3889d11f2ddb1A1Db11e80D20EF367c01 +23ms
  #   laconic:payments Serving a paid query for 0xB2B22ec3889d11f2ddb1A1Db11e80D20EF367c01 +0ms
  # 13:01:05.671 DEBUG payment    Verified payment for GQL queries getEthLogs
  #   laconic:payments Received a payment voucher of 100 from 0xB2B22ec3889d11f2ddb1A1Db11e80D20EF367c01 +20ms
  #   laconic:payments Serving a paid query for 0xB2B22ec3889d11f2ddb1A1Db11e80D20EF367c01 +0ms
  # 13:01:05.691 DEBUG payment    Verified payment for GQL queries getEthBlock
  # 13:01:07.598 INFO  realtime   Fetched missing blocks [686, 687] (network=fixturenet)
  # 13:01:07.598 DEBUG realtime   Started processing new head block 686 (network=fixturenet)
  # ...
  ```

* In another terminal run the Ponder app in watcher mode:

  ```bash
  docker exec -it payments-ponder-app-watcher-1 bash -c "DEBUG=laconic:payments pnpm start"

  # Expected output:
  # 11:23:22.057 DEBUG app        Started using config file: ponder.config.ts
  # 08:02:12.548 INFO  payment    Nitro node setup with address 0x111A00868581f73AB42FEEF67D235Ca09ca1E8db
  #   laconic:payments Starting voucher subscription... +0ms
  # 08:02:17.417 INFO  payment    Creating ledger channel with nitro node 0xB2B22ec3889d11f2ddb1A1Db11e80D20EF367c01 ...
  # 08:02:37.135 INFO  payment    Creating payment channel with nitro node 0xB2B22ec3889d11f2ddb1A1Db11e80D20EF367c01 ...
  # 08:02:37.313 INFO  payment    Using payment channel 0xc48622577dfa389283beb19ed946274eb034587d72e61445dc997304be671f1a
  # ...
  # 11:23:22.436 INFO  server     Started responding as healthy
  ```

* Check the terminal of the second indexer Ponder app. Logs of payment for `getLogEvents` queries can be seen:

  ```bash
  # ...
  # 08:02:37.763 DEBUG realtime   Finished processing new head block 89 (network=fixturenet)
  #   laconic:payments Received a payment voucher of 50 from 0x111A00868581f73AB42FEEF67D235Ca09ca1E8db +444ms
  #   laconic:payments Serving a paid query for 0x111A00868581f73AB42FEEF67D235Ca09ca1E8db +1ms
  # 08:02:37.804 DEBUG payment    Verified payment for GQL queries getLogEvents
  #   laconic:payments Received a payment voucher of 50 from 0x111A00868581f73AB42FEEF67D235Ca09ca1E8db +45ms
  #   laconic:payments Serving a paid query for 0x111A00868581f73AB42FEEF67D235Ca09ca1E8db +0ms
  # 08:02:37.849 DEBUG payment    Verified payment for GQL queries getLogEvents
  ```

* Open watcher Ponder app endpoint http://localhost:42069

  * Try GQL query to see transfer events
    
    ```graphql
    {
      transferEvents (orderBy: "timestamp", orderDirection: "desc") {
        id
        amount
        from {
          id
        }
        to {
          id
        }
        timestamp
      }
    }
    ```
  
  * No entities will be returned at this point

* Transfer an ERC20 token on chain

  * Get the deployed ERC20 token address

    ```bash
    export TOKEN_ADDRESS=$(docker exec payments-ponder-er20-contracts-1 jq -r '.address' ./deployment/erc20-address.json)
    ```
  
  * Transfer token
  
    ```bash
    docker exec -it payments-ponder-er20-contracts-1 bash -c "yarn token:transfer:docker --token ${TOKEN_ADDRESS} --to 0xe22AD83A0dE117bA0d03d5E94Eb4E0d80a69C62a --amount 5000"
    ```

* Check the GQL query again in http://localhost:42069 to see a new `TransferEvent` entity
