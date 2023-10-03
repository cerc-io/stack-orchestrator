# fixturenet-payments

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

### Configuration

Deploy the stack:

```bash
laconic-so --stack fixturenet-payments deploy --cluster payments up

# Exposed on host ports:
# 5005: go-nitro node's p2p msg port
# 8081: reverse payment proxy's RPC endpoint
# 15432: MobyMask v3 watcher's db endpoint
# 3001: MobyMask v3 watcher endpoint
# 9090: MobyMask v3 watcher relay node endpoint
# 8080: MobyMask snap
# 3004: MobyMask v3 app
```

Check the logs of the MobyMask contract deployment container to get the deployed contract's address and generated root invite link:

```bash
docker logs -f $(docker ps -aq --filter name="mobymask-1")
```

Check the reverse payment proxy container logs:

```bash
docker logs -f $(docker ps -aq --filter name="nitro-reverse-payment-proxy")
```

Run the ponder app:

```bash
docker exec -it payments-ponder-app-1 bash -c "pnpm start"
```

## Clean up

Stop all the services running in background:

```bash
laconic-so --stack fixturenet-payments deploy --cluster payments down 30
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=[payments"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=[payments")
```
