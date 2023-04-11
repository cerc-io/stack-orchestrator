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

Checkout to the required versions and branches in repos

```bash
# watcher-ts
cd ~/cerc/watcher-ts
git checkout v0.2.35

# react-peer
cd ~/cerc/react-peer
git checkout v0.2.31

# mobymask-ui
cd ~/cerc/mobymask-ui
git checkout laconic

# MobyMask
cd ~/cerc/MobyMask
git checkout v0.1.2

# Optimism
cd ~/cerc/optimism
git checkout @eth-optimism/sdk@0.0.0-20230329025055
```

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers
```

This should create the required docker images in the local image registry.

Deploy the stack:

* Deploy the containers:

  ```bash
  laconic-so --stack mobymask-v2 deploy-system up
  ```

* List and check the health status of all the containers using `docker ps` and wait for them to be `healthy`

  NOTE: The `mobymask-app` container might not start; if the app is not running at http://localhost:3002, restart the container using it's id:

  ```bash
  docker ps -a | grep "mobymask-app"

  docker restart <CONTAINER_ID>
  ```

## Tests

Find the watcher container's id and export it for later use:

```bash
export CONTAINER_ID=$(docker ps -q --filter "name=mobymask-watcher-server")
```

Run the peer tests:

```bash
docker exec -w /app/packages/peer $CONTAINER_ID yarn test
```

## Web Apps

Check that the web-app containers are healthy:

```bash
docker ps | grep -E 'mobymask-app|peer-test-app'
```

### mobymask-app

The mobymask-app should be running at http://localhost:3002

### peer-test-app

The peer-test-app should be running at http://localhost:3003

## Details

* The relay node for p2p network is running at http://localhost:9090

* The [peer package](https://github.com/cerc-io/watcher-ts/tree/main/packages/peer) (published in [gitea](https://git.vdb.to/cerc-io/-/packages/npm/@cerc-io%2Fpeer)) can be used in client code for connecting to the network

* The [react-peer package](https://github.com/cerc-io/react-peer/tree/main/packages/react-peer) (published in [gitea](https://git.vdb.to/cerc-io/-/packages/npm/@cerc-io%2Freact-peer)) which uses the peer package can be used in react app for connecting to the network

## Demo

Follow the [demo](./demo.md) to try out the MobyMask app with L2 chain

## Clean up

Stop all the services running in background run:

```bash
laconic-so --stack mobymask-v2 deploy-system down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=.*mobymask_watcher_db_data|.*mobymask_deployment|.*fixturenet_geth_accounts|.*l1_deployment|.*l2_accounts|.*l2_config|.*l2_geth_data"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*mobymask_watcher_db_data|.*mobymask_deployment|.*fixturenet_geth_accounts|.*l1_deployment|.*l2_accounts|.*l2_config|.*l2_geth_data")
```
