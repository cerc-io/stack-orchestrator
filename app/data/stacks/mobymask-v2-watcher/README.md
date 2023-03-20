# MobyMask v2 watcher

Instructions to deploy MobyMask v2 watcher stack using [laconic-stack-orchestrator](../../README.md#setup)

## Setup

Clone required repositories:

```bash
laconic-so --stack mobymask-v2-watcher setup-repositories
```

Build the container images:

```bash
laconic-so --stack mobymask-v2-watcher build-containers
```

This should create the required docker images in the local image registry.

Deploy the stack:

```bash
laconic-so --stack mobymask-v2-watcher deploy-system up
```

## Tests

Find the watcher container's id using `docker ps` and export it for later use:

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
laconic-so --stack mobymask-v2-watcher deploy-system down
```
