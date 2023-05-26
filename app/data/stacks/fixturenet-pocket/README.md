# Pocket Fixturenet

Instructions for deploying a local single-node Pocket chain alongside a geth + lighthouse blockchain "fixturenet" for development and testing purposes using Stack Orchestrator.

## 1. Clone required repositories
```
$ laconic-so --stack fixturenet-pocket setup-repositories
```
## 2. Build the stack's containers
```
$ laconic-so --stack fixturenet-pocket build-containers
```
## 3. Deploy the stack
```
$ laconic-so --stack fixturenet-pocket deploy up
```
It may take up to 10 minutes for the Eth Fixturenet to fully come online and start producing blocks.

## 4. Check status
**Eth Fixturenet:**
```
$ laconic-so --stack fixturenet-pocket deploy exec fixturenet-eth-bootnode-lighthouse /scripts/status-internal.sh
Waiting for geth to generate DAG.... done
Waiting for beacon phase0.... done
Waiting for beacon altair.... done
Waiting for beacon bellatrix pre-merge.... done
Waiting for beacon bellatrix merge.... done
```
**Pocket node:**
```
$ laconic-so --stack fixturenet-pocket deploy exec pocket "pocket query height"
2023/04/20 08:07:46 Initializing Pocket Datadir
2023/04/20 08:07:46 datadir = /home/app/.pocket
http://localhost:8081/v1/query/height
{
    "height": 4
}
```
or
```
$ laconic-so --stack fixturenet-pocket deploy logs pocket
```
## 5. Send a relay request to Pocket node
The Pocket node serves relay requests at `http://localhost:8081/v1/client/sim`  
**Example request:**
```
$ curl -X POST --data '{"relay_network_id":"0021","payload":{"data":"{\"jsonrpc\": \"2.0\",\"id\": 1,\"method\": \"eth_blockNumber\",\"params\": []}","method":"POST","path":"","headers":{}}}' http://localhost:8081/v1/client/sim
```
**Response:**
```
"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":\"0x6fe\"}\n"
```
