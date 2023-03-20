# MobyMask v2 watcher

Instructions to deploy MobyMask v2 watcher stack using [laconic-stack-orchestrator](/README.md#install)

## Setup

Clone required repositories:

```bash
laconic-so --stack mobymask-v2 setup-repositories
```

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers
```

This should create the required docker images in the local image registry.

Deploy the stack:

```bash
laconic-so --stack mobymask-v2 deploy-system up
```

## Tests

Find the watcher container's id:

```bash
docker ps | grep "cerc/watcher-mobymask-v2:local"
```

Example output

```
8b38e9a64d7e   cerc/watcher-mobymask-v2:local   "sh -c 'yarn server'"    35 seconds ago   Up 14 seconds (health: starting)   0.0.0.0:3001->3001/tcp, 0.0.0.0:9001->9001/tcp, 0.0.0.0:9090->9090/tcp   laconic-aeb84676de2b0a7671ae90d537fc7d26-mobymask-watcher-server-1
```

In above output the container ID is `8b38e9a64d7e`

Export it for later use:

```bash
export CONTAINER_ID=<CONTAINER_ID>
```

Run the peer tests:

```bash
docker exec -w /app/packages/peer $CONTAINER_ID yarn test
```

## Clean up

To stop all the services running in background run:

```bash
laconic-so --stack mobymask-v2 deploy-system down
```
