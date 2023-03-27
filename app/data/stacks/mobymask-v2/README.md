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
git checkout v0.2.31

# react-peer
cd ~/cerc/react-peer
git checkout v0.2.29

# mobymask-ui
cd ~/cerc/mobymask-ui
git checkout laconic

# laconicd
cd ~/cerc/laconicd
git checkout v0.8.0

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

* Deploy the laconic chain

  ```bash
  laconic-so --stack mobymask-v2 deploy-system --include mobymask-laconicd up
  ```

* Check that laconic chain status is healthy

  ```bash
  docker ps
  ```

* Export the private key from laconicd

  ```bash
  laconic-so --stack mobymask-v2 deploy-system --include mobymask-laconicd exec laconicd "echo y | laconicd keys export mykey --unarmored-hex --unsafe"
  ```

* Set the private key in [secrets.json](../../config/watcher-mobymask-v2/secrets.json) file that will be used by mobymask container to deploy contract:

  ```bash
  vi ~/.shiv/laconic-so_48964f2768eabff1d80963d853b776e5d84037f06ef3933bbaed857c1b82f93b/site-packages/app/data/config/watcher-mobymask-v2/secrets.json
  ```
  
  Note that: `~/.shiv/laconic-so_THIS_NUMBER_MIGHT_BE_DIFFERENT_FOR_YOU` and if you've had multiple `laconic-so` installations, ensure you select the correct one.

* Create a new account

  ```bash
  laconic-so --stack mobymask-v2 deploy-system --include mobymask-laconicd exec laconicd "laconicd keys add alice"
  ```

* Transfer balance to new account

  ```bash
  laconic-so --stack mobymask-v2 deploy-system --include mobymask-laconicd exec laconicd 'laconicd tx bank send $(laconicd keys show mykey -a) $(laconicd keys show alice -a) 1000000000000000000000000aphoton --fees 2000aphoton'
  ```

* Export the private key of new account from laconicd

  ```bash
  laconic-so --stack mobymask-v2 deploy-system --include mobymask-laconicd exec laconicd "echo y | laconicd keys export alice --unarmored-hex --unsafe"
  ```

* Set the private key (`PRIVATE_KEY`) in [peer-start.sh](../../config/watcher-mobymask-v2/peer-start.sh) file that will be used to start the peer that sends txs to L2 chain:

  ```bash
  vi ~/.shiv/laconic-so_48964f2768eabff1d80963d853b776e5d84037f06ef3933bbaed857c1b82f93b/site-packages/app/data/config/watcher-mobymask-v2/peer-start.sh
  ```

* Deploy the other containers

  ```bash
  laconic-so --stack mobymask-v2 deploy-system --include watcher-mobymask-v2 up
  ```

* Check that all containers are healthy using `docker ps`

  NOTE: The `mobymask-ui` container might not start. If mobymask-app is not running at http://localhost:3002, run command again to start the container

  ```bash
  laconic-so --stack mobymask-v2 deploy-system --include watcher-mobymask-v2 up
  ```

## Tests

Find the watcher container's id:

```bash
laconic-so --stack mobymask-v2 deploy-system --include watcher-mobymask-v2 ps | grep "mobymask-watcher-server"
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

Run the peer tests (from any pwd):

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
