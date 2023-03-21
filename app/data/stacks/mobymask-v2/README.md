# MobyMask v2 watcher

Instructions to deploy MobyMask v2 watcher stack using [laconic-stack-orchestrator](/README.md#install)

## Setup

Clone required repositories:

```bash
laconic-so --stack mobymask-v2 setup-repositories
```

Checkout to the required branch in mobymask-ui

```bash
cd ~/cerc/mobymask-ui

git checkout laconic
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

## Web Apps

Check that the status for web-app containers are healthy by using `docker ps`

### mobymask-app

The mobymask-app should be running at http://localhost:3002

### peer-test-app

The peer-test-app should be running at http://localhost:3003

## Details

* The relay node for p2p network is running at http://localhost:9090

* The [peer package](https://github.com/cerc-io/watcher-ts/tree/main/packages/peer) (published in [gitea](https://git.vdb.to/cerc-io/-/packages/npm/@cerc-io%2Fpeer)) can be used in client code for connecting to the network

* The [react-peer package](https://github.com/cerc-io/react-peer/tree/main/packages/react-peer) (published in [gitea](https://git.vdb.to/cerc-io/-/packages/npm/@cerc-io%2Freact-peer)) which uses the peer package can be used in react app for connecting to the network

## Clean up

To stop all the services running in background run:

```bash
laconic-so --stack mobymask-v2 deploy-system down
```
