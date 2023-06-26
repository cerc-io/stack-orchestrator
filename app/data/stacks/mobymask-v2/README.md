# MobyMask v2 watcher

Instructions to setup and deploy an end-to-end MobyMask v2 stack ([L1](../fixturenet-eth/) + [L2](../fixturenet-optimism/) chains + watcher + web-app(s)) using [laconic-stack-orchestrator](/README.md#install)

We support running just the watcher part of stack, given an external L2 Optimism endpoint.
Follow [mobymask-only](./mobymask-only.md) for the same.

We also support running just the web-app(s), given external watcher GQL (for mobymask-app) and relay node endpoints. Follow [web-apps.md](./web-apps.md) for the same.

## Setup

Clone required repositories:

```bash
laconic-so --stack mobymask-v2 setup-repositories
```

NOTE: If repositories already exist and are checked out to different versions, `setup-repositories` command will throw an error.
For getting around this, the repositories mentioned below can be removed and then run the command.

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers
```

This should create the required docker images in the local image registry.

Deploy the stack:

* Deploy the containers:

  ```bash
  laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 up
  ```

  NOTE: The `fixturenet-optimism-contracts` service takes a while to run to completion and it may restart a few times after running into errors.

* To list down and monitor the running containers:

  ```bash
  laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 ps

  # With status
  docker ps -a

  # Check logs for a container
  docker logs -f <CONTAINER_ID>
  ```

## Tests

Find the watcher container's id and export it for later use:

```bash
export CONTAINER_ID=$(docker ps -q --filter "name=peer-tests")
```

Run the peer tests:

```bash
docker exec $CONTAINER_ID yarn test
```

## Web Apps

Check that the web-app containers are healthy:

```bash
docker ps | grep -E 'mobymask-app|peer-test-app'
```

### mobymask-app

* The mobymask-app should be running at http://localhost:3002
* The lxdao-mobymask-app should be running at http://localhost:3004

### peer-test-app

* The peer-test-app should be running at http://localhost:3003

## Details

* The relay node for p2p network is running at http://localhost:9090

* The [peer package](https://github.com/cerc-io/watcher-ts/tree/main/packages/peer) (published in [gitea](https://git.vdb.to/cerc-io/-/packages/npm/@cerc-io%2Fpeer)) can be used in client code for connecting to the network

* The [react-peer package](https://github.com/cerc-io/react-peer/tree/main/packages/react-peer) (published in [gitea](https://git.vdb.to/cerc-io/-/packages/npm/@cerc-io%2Freact-peer)) which uses the peer package can be used in react app for connecting to the network

## Demo

Follow the [demo](./demo.md) to try out the MobyMask app with L2 chain

## Clean up

Stop all the services running in background run:

```bash
laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 down 30
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=mobymask_v2"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=mobymask_v2")
```
