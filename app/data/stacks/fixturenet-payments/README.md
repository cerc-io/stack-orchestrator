# fixturenet-payments

Instructions to setup and deploy an end-to-end fixturenet-payments stack

## Setup

Clone required repositories:

```bash
laconic-so --stack fixturenet-payments setup-repositories --pull
```

Build the container images:

```bash
laconic-so --stack fixturenet-payments build-containers
```

## Deploy

Deploy the stack:

```bash
laconic-so --stack fixturenet-payments deploy --cluster payments up

# Exposed on host ports:
# 32***: geth in statediffing mode and ipld-eth-server(s)
# 4005: in-process go-nitro node's RPC endpoint
# 3005: in-process go-nitro node's p2p TCP endpoint
# 5005: in-process go-nitro node's p2p WS endpoin
# 4006: out-of-process go-nitro node's RPC endpoint
# 3006: out-of-process go-nitro node's p2p TCP endpoint
# 5006: out-of-process go-nitro node's p2p WS endpoint
# 15432: MobyMask v3 watcher's db endpoint
# 3001: MobyMask v3 watcher endpoint
# 9090: MobyMask v3 watcher relay node endpoint
# 8080: MobyMask snap
# 3004: MobyMask v3 app
```

## Demo

Follow the [demo](./demo.md) to try out end-to-end payments

## Clean up

Stop all the services running in background:

```bash
laconic-so --stack fixturenet-payments deploy --cluster payments down 30
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=payments"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=payments")
```
