# Web Apps

Instructions to setup and deploy MobyMask and Peer Test web apps

## Setup

Prerequisite: Watcher with GQL and relay node endpoints

Clone required repositories:

```bash
laconic-so --stack mobymask-v2 setup-repositories --include cerc-io/react-peer,cerc-io/mobymask-ui
```

Checkout to the required versions and branches in repos:

```bash
# react-peer
cd ~/cerc/react-peer
git checkout v0.2.31

# mobymask-ui
cd ~/cerc/mobymask-ui
git checkout laconic
```

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers --include cerc/react-peer-v2,cerc/mobymask-ui
```

This should create the required docker images in the local image registry

## Deploy

### Configuration

* Update the [mobymask-params.env](../../config/watcher-mobymask-v2/mobymask-params.env) file with watcher endpoints and other params required by the web-apps
  * `WATCHER_HOST` and `WATCHER_PORT` is used to check if watcher is up before building and deploying mobymask-app
  * `APP_WATCHER_URL` is used by mobymask-app to make GQL queries
  * `DEPLOYED_CONTRACT` and `CHAIN_ID` is used by mobymask-app in app config when creating messgaes for L2 txs
  * `RELAY_NODES` is used by the web-apps to connect to the relay nodes (run in watcher)
* NOTE:
  * Stack Orchestrator needs to be run in [`dev`](/docs/CONTRIBUTING.md#install-developer-mode) mode to be able to edit the env file
  * If watcher is running on the host machine, use `host.docker.internal` as the hostname to access the host port

### Deploy the stack

For running mobymask-app
```bash
laconic-so --stack mobymask-v2 deploy --include mobymask-app up
```

For running peer-test-app
```bash
laconic-so --stack mobymask-v2 deploy --include peer-test-app up
```

To list down and monitor the running containers:

```bash
docker ps

# Check logs for a container
docker logs -f <CONTAINER_ID>
```

## Clean up

Stop all services running in the background:

For mobymask-app
```bash
laconic-so --stack mobymask-v2 deploy --include mobymask-app down
```

For peer-test-app
```bash
laconic-so --stack mobymask-v2 deploy --include peer-test-app down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=.*mobymask_deployment"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*mobymask_deployment")
```
