# fixturenet-payments-lite

Instructions to setup and deploy an end-to-end fixturenet-payments-lite stack, on a local machine. Some tips are included for running on a remote cloud machine.

## Setup

Clone required repositories:

```bash
laconic-so --stack fixturenet-nitro setup-repositories --pull
```

Build the container imagesfixturenet-payments-lite:

```bash
laconic-so --stack fixturenet-nitro build-containers
```

## Deploy

Deploy the stack:

```bash
laconic-so --stack fixturenet-nitro deploy --cluster payments up
```

```bash
# Exposed on host ports:
# 32***: geth in statediffing mode and ipld-eth-server(s)
# 4005: in-process go-nitro node's RPC endpoint
# 3005: in-process go-nitro node's p2p TCP endpoint
# 5005: in-process go-nitro node's p2p WS endpoint
# 4006: out-of-process go-nitro node's RPC endpoint
# 3006: out-of-process go-nitro node's p2p TCP endpoint
# 5006: out-of-process go-nitro node's p2p WS endpoint
# 15432: MobyMask v3 watcher's db endpoint
# 3001: MobyMask v3 watcher endpoint
# 9090: MobyMask v3 watcher relay node endpoint
# 8080: MobyMask snap
# 3004: MobyMask v3 app
# 42070: Ponder indexer-1
# 42071: Ponder indexer-2
# 42069: Ponder watcher
```

If running in the cloud, ensure all the of the above ports are open. The geth port can be retrieved with:

```bash
docker port payments-fixturenet-eth-geth-1-1 8545
```

Then for every port above, run each line in a new terminal window (or use `screen`):

```bash
ssh -L 4005:localhost:4005 user@<your-ip>
ssh -L 5005:localhost:5005 user@<your-ip>
ssh -L 8081:localhost:8081 user@<your-ip>
# ... and so on for every port
```

This will allow you to access the entirety of the app as if it were running locally.

## Demo

- Follow the [mobymask-demo](./mobymask-demo.md) to try out MobyMask end-to-end payments.
- Follow the [ponder-demo](./ponder-demo.md) to try out Ponder end-to-end payments.

## Clean up

Stop all the services running in background:

```bash
laconic-so --stack fixturenet-nitro deploy --cluster payments down 30
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=payments"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=payments")
```
