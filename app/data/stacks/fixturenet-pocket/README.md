# Pocket Fixturenet

Instructions for deploying a local single-node Pocket chain alongside a geth + lighthouse blockchain "fixturenet" for development and testing purposes using laconic-stack-orchestrator.

## 1. Build Laconic Stack Orchestrator
Build this fork of Laconic Stack Orchestrator which includes the fixturenet-pocket stack:
```
$ scripts/build_shiv_package.sh
$ cd package
$ mv laconic-so-{version} /usr/local/bin/laconic-so  # Or move laconic-so to ~/bin or your favorite on-path directory
```

## 2. Clone required repositories
```
$ laconic-so --stack fixturenet-pocket setup-repositories
```
## 3. Build the stack's containers
```
$ laconic-so --stack fixturenet-pocket build-containers
```
## 4. Deploy the stack
```
$ laconic-so --stack fixturenet-pocket deploy up
```
It may take up to 10 minutes for the Eth Fixturenet to fully come online and start producing blocks.
## 5. Check status
Eth Fixturenet:
```
$ laconic-so --stack fixturenet-pocket deploy exec fixturenet-eth-bootnode-lighthouse /scripts/status-internal.sh
Waiting for geth to generate DAG.... done
Waiting for beacon phase0.... done
Waiting for beacon altair.... done
Waiting for beacon bellatrix pre-merge.... done
Waiting for beacon bellatrix merge.... done
```
Pocket node:
```
$ laconic-so --stack fixturenet-pocket deploy exec pocket "curl localhost:26657/status"
{
  "jsonrpc": "2.0",
  "id": -1,
  "result": {
    "node_info": {
      "protocol_version": {
        "p2p": "7",
        "block": "10",
        "app": "0"
      },
      "id": "ac476b11fd3dd3b646465afe8468b1adad249d32",
      "listen_addr": "tcp://0.0.0.0:26656",
      "network": "pocketlocal-1",
      "version": "0.33.7",
      "channels": "4020212223303800",
      "moniker": "localtestnet",
      "other": {
        "tx_index": "on",
        "rpc_address": "tcp://127.0.0.1:26657"
      }
    },
    "sync_info": {
      "latest_block_hash": "CCB4E94F4958D5142C0DB218841D48FA37EABB411956ADBCBB7ECDCB17E81F66",
      "latest_app_hash": "42DFF8EC70FDCB9B00C0305395B2A82F9813680E7C33093A629CBE2EBA7163EE",
      "latest_block_height": "108",
      "latest_block_time": "2023-04-14T18:59:31.493905099Z",
      "earliest_block_hash": "AAA11DF19F18972DAF23A727B3B8BF9014972EC6561103A980014B721F53E275",
      "earliest_app_hash": "",
      "earliest_block_height": "1",
      "earliest_block_time": "2020-07-28T15:00:00Z",
      "catching_up": false
    },
    "validator_info": [
      {
        "address": "AC476B11FD3DD3B646465AFE8468B1ADAD249D32",
        "pub_key": {
          "type": "tendermint/PubKeyEd25519",
          "value": "mnDMAT9TkST340qpJq3PCk1aymrtMw+RevoUsKQOSF4="
        },
        "voting_power": "5000000"
      }
    ]
  }
}
```
## 6. Send a relay request to Pocket node
The Pocket node serves relay requests at `http://localhost:8081/v1/client/sim`  
Example request:
```
$ curl -X POST --data '{"relay_network_id":"0021","payload":{"data":"{\"jsonrpc\": \"2.0\",\"id\": 1,\"method\": \"eth_blockNumber\",\"params\": []}","method":"POST","path":"","headers":{}}}' http://localhost:8081/v1/client/sim
```
Response:
```
"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":\"0x6fe\"}\n"
```
