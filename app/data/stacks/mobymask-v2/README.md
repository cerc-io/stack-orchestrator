# MobyMask v2 watcher

Instructions to deploy MobyMask v2 watcher stack using [laconic-stack-orchestrator](/README.md#install)

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
git checkout v0.2.34

# react-peer
cd ~/cerc/react-peer
git checkout v0.2.31

# mobymask-ui
cd ~/cerc/mobymask-ui
git checkout laconic

# MobyMask
cd ~/cerc/MobyMask
git checkout v0.1.1
```

Build the container images:

```bash
laconic-so --stack mobymask-v2 build-containers
```

This should create the required docker images in the local image registry.

Deploy the stack:

* Deploy the containers

  ```bash
  laconic-so --stack mobymask-v2 deploy-system up
  ```

* Check that all containers are healthy using `docker ps`

  NOTE: The `mobymask-ui` container might not start. If mobymask-app is not running at http://localhost:3002, run command again to start the container

  ```bash
  laconic-so --stack mobymask-v2 deploy-system up
  ```

## Tests

Find the watcher container's id:

```bash
laconic-so --stack mobymask-v2 deploy-system ps | grep "mobymask-watcher-server"
```

Example output

```
id: 5d3aae4b22039fcd1c9b18feeb91318ede1100581e75bb5ac54f9e436066b02c, name: laconic-bfb01caf98b1b8f7c8db4d33f11b905a-mobymask-watcher-server-1, ports: 0.0.0.0:3001->3001/tcp, 0.0.0.0:9001->9001/tcp, 0.0.0.0:9090->9090/tcp
```

In above output the container ID is `5d3aae4b22039fcd1c9b18feeb91318ede1100581e75bb5ac54f9e436066b02c`

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

## Demo

Follow the [demo](./demo.md) to try out the MobyMask app with L2 chain

## Clean up

Stop all the services running in background run:

```bash
laconic-so --stack mobymask-v2 deploy-system --include watcher-mobymask-v2 down

laconic-so --stack mobymask-v2 deploy-system --include mobymask-laconicd down
```

Clear volumes:

* List all volumes

  ```bash
  docker volume ls
  ```

* Remove volumes created by this stack

  Example:
  ```bash
  docker volume rm laconic-bfb01caf98b1b8f7c8db4d33f11b905a_moby_data_server
  ```
