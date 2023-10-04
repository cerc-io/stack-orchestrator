# Demo

## MobyMask Watcher

* Check watcher logs and wait for the payment channel to be created with upstream go-nitro node:

  ```bash
  docker logs -f $(docker ps -aq --filter name="mobymask-watcher-server")

  # Expected output:
  # vulcanize:server Using rpcProviderEndpoint as chain URL for Nitro node +0ms
  # ...
  # ts-nitro:util:nitro Ledger channel created with id 0x65703ccdfacab09ac35367bdbe6c5a337e7a6651aad526807607b1c59b28bc1e
  # ...
  # ts-nitro:util:nitro Virtual payment channel created with id 0x29ff1335d73391a50e8fde3e9b34f00c3d81c39ddc7f89187f44dd51df96140e
  ```

* Export the payment channel id to a variable:

  ```bash
  export WATCHER_UPSTREAM_PAYMENT_CHANNEL=<PAYMENT_CHANNEL_ID>
  ```

* Generate an auth token required to query the go-nitro node's RPC endpoint:

  ```bash
  export AUTH_TOKEN=$(curl -s -X POST -H "Content-Type: application/json" --data '{
    "jsonrpc": "2.0", "id": 1,
    "method": "get_auth_token",
    "params": {}
  }' http://127.0.0.1:4005/api/v1 | jq -r '.result')
  ```

* Check the payment channel status:

  ```bash
  curl -X POST -H "Content-Type: application/json" --data "{
    \"jsonrpc\": \"2.0\", \"id\": 1,
    \"method\": \"get_payment_channel\",
    \"params\": { \"authtoken\": \"$AUTH_TOKEN\", \"payload\": { \"Id\": \"$WATCHER_UPSTREAM_PAYMENT_CHANNEL\" } }
  }" http://127.0.0.1:4005/api/v1 | jq

  # Expected output:
  # {
  #   "jsonrpc": "2.0",
  #   "id": 1,
  #   "result": {
  #     "ID": "0xfe1231722d6c2cd7af8606afe039582ebc438ee5ca2b956f8284cb497597583f",
  #     "Status": "Open",
  #     "Balance": {
  #       "AssetAddress": "0x0000000000000000000000000000000000000000",
  #       "Payee": "0xaaa6628ec44a8a742987ef3a114ddfe2d4f7adce",
  #       "Payer": "0xbbb676f9cff8d242e9eac39d063848807d3d1d94",
  #       "PaidSoFar": "0x0",
  #       "RemainingFunds": "0x3b9aca00"
  #     }
  #   }
  # }
  ```

## MobyMask App

* Track the reverse payment proxy container logs in a terminal:

  ```bash
  docker logs -f $(docker ps -aq --filter name="nitro-reverse-payment-proxy")
  ```

* Get the geth node’s port mapped to host:

  ```bash
  docker port payments-fixturenet-eth-geth-1-1 8545
  ```

* In MetaMask Flask, add a custom network with the following settings:

  ```bash
  # New RPC URL
  http://127.0.0.1:<GETH_PORT>

  # Chain ID
  1212

  # Currency symbol
  ETH
  ```

* Import the faucet account in MetaMask and fund an additional account for usage in the app:

  ```bash
  # Faucet PK
  # 0x570b909da9669b2f35a0b1ac70b8358516d55ae1b5b3710e95e9a94395090597

  # Clear activity tab for the accounts on chain restart
  ```

* Get the generated root invite link for the app from MobyMask contract deployment container logs:

  ```bash
  docker logs -f $(docker ps -aq --filter name="mobymask-1")

  # Expected output:
  # ...
  #   "key": "0x60e706fda4639fe0a8eb102cb0ce81231cf6e819f41cb4eadf72d865ea4c11ad"
  # }
  # http://127.0.0.1:3004/#/members?invitation=<INVITATION>
  ```

* Open app in a browser using the invite link

* Run the following in the browser console to enable logs:

  ```bash
  localStorage.debug = 'ts-nitro:*'
  # Refresh the tab for taking effect
  ```

* In the app’s debug panel, check that the peer gets connected to relay node and watcher peer

* Open the `NITRO` tab in debug panel
  * Click on `Connect Wallet` to connect to MetaMask (make sure that the newly funded account is active)
  * Click on `Connect Snap` to install/connect snap

* Perform `DIRECT FUND` with the preset amount

* Perform `VIRTUAL FUND` with amount set to `10000`

* Perform phisher status check queries now that a payment channel is created:
  * Check the watcher logs for received payments
  * Check the payment proxy server logs for charged RPC requests (`eth_getBlockByHash`, `eth_getStorageAt`) made from watcher to upstream ETH server

* Change the amount besides `PAY` button to `>=100` for phisher reports next

* Perform a phisher report and check the watcher logs for received payments; the RPC mutation request is sent to geth node and is not charged

* Check the watcher - eth-server payment channel status after a few requests:

  ```bash
  curl -X POST -H "Content-Type: application/json" --data "{
    \"jsonrpc\": \"2.0\", \"id\": 1,
    \"method\": \"get_payment_channel\",
    \"params\": { \"authtoken\": \"$AUTH_TOKEN\", \"payload\": { \"Id\": \"$WATCHER_UPSTREAM_PAYMENT_CHANNEL\" } }
  }" http://127.0.0.1:4005/api/v1 | jq

  # Expected output ('PaidSoFar' should be non zero):
  # {
  #   "jsonrpc": "2.0",
  #   "id": 1,
  #   "result": {
  #     "ID": "0xfe1231722d6c2cd7af8606afe039582ebc438ee5ca2b956f8284cb497597583f",
  #     "Status": "Open",
  #     "Balance": {
  #       "AssetAddress": "0x0000000000000000000000000000000000000000",
  #       "Payee": "0xaaa6628ec44a8a742987ef3a114ddfe2d4f7adce",
  #       "Payer": "0xbbb676f9cff8d242e9eac39d063848807d3d1d94",
  #       "PaidSoFar": "0x2710",
  #       "RemainingFunds": "0x3b9aa2f0"
  #     }
  #   }
  # }
  ```

## Ponder App

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

* Export the payment channel id to a variable:

  ```bash
  export PONDER_UPSTREAM_PAYMENT_CHANNEL=<PAYMENT_CHANNEL_ID>
  ```

* Check the ponder - eth-server payment channel status:

  ```bash
  curl -X POST -H "Content-Type: application/json" --data "{
    \"jsonrpc\": \"2.0\", \"id\": 1,
    \"method\": \"get_payment_channel\",
    \"params\": { \"authtoken\": \"$AUTH_TOKEN\", \"payload\": { \"Id\": \"$PONDER_UPSTREAM_PAYMENT_CHANNEL\" } }
  }" http://127.0.0.1:4005/api/v1 | jq

  # Expected output:
  # TODO
  ```

* Check reverse payment proxy server logs for charged RPC requests made from ponder app to upstream ETH server:

  ```bash
  # Expected output:
  # ...
  # {"time":"2023-09-28T09:59:14.499841999Z","level":"DEBUG","msg":"Request cost","cost-per-byte":1,"response-length":61,"cost":61}
  # {"time":"2023-09-28T09:59:14.500060006Z","level":"DEBUG","msg":"sent message","address":"0xAAA6628Ec44A8a742987EF3A114dDFE2D4F7aDCE","method":"receive_voucher"}
  # {"time":"2023-09-28T09:59:14.501221898Z","level":"DEBUG","msg":"Received voucher","delta":5000}
  # {"time":"2023-09-28T09:59:14.501245984Z","level":"DEBUG","msg":"Destination request","url":"http://ipld-eth-server:8081/?method=eth_getLogs"}
  ```
