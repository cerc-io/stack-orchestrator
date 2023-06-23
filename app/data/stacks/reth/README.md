# Reth
Deploy a Reth API node alongside Lighthouse.

## Clone required repositories

```
$ laconic-so --stack reth setup-repositories
```

## Build the fixturenet-eth containers

```
$ laconic-so --stack reth build-containers
```

## Deploy the stack

```
$ laconic-so --stack reth deploy up
```

## Check logs

```
$ laconic-so --stack reth deploy logs
```

Verify that your node is syncing. You should see entries similar to this from the Lighthouse container:

```
laconic-200e8f8ff7891515d777cd0f719078e3-lighthouse-1  | Jun 23 20:59:01.226 INFO New block received                      root: 0x9cd4a2dd9333cf802c2963c2f029deb0f94e511d2481fa0724ae8752e4c49b15, slot: 6727493
```
and entries similar to this from the Reth container:
```
laconic-200e8f8ff7891515d777cd0f719078e3-reth-1        | 2023-06-23T20:59:11.557389Z  INFO reth::node::events: Stage committed progress pipeline_stages=1/13 stage=Headers block=0 checkpoint=4.9% eta=1h 3m 57s
```

## Test the API

Reth's http api is accessible on port `8545` and the websocket api is accessible on port `8546`.
```
$ curl --request POST \
    --url http://localhost:8545/ \
    --header 'Content-Type: application/json' \
    --data '{
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": [],
    "id": 0
  }'

# Response
{"jsonrpc":"2.0","result":"0x0","id":0}
```

## Clean up

Stop all services running in the background:

```bash
$ laconic-so --stack reth deploy down
```
To also delete the docker data volumes:
```bash
$ laconic-so --stack reth deploy down --delete-volumes