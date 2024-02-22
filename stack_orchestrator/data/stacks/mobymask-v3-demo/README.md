# MobyMask v3 Demo

Instructions to setup and deploy an end-to-end MobyMask v3 stack (fixturenet-optimism + watchers + web-app) locally using [laconic-stack-orchestrator](/README.md#install)

## Setup

* Clone required repositories:

  ```bash
  laconic-so --stack mobymask-v3-demo setup-repositories --pull
  ```

* Build the container images:

  ```bash
  laconic-so --stack mobymask-v3-demo build-containers
  ```

* Install MetaMask Flask extension in a chromium browser from chrome web store and follow the setup instructions

## Deploy

* Create a spec file for the deployment:

  ```bash
  laconic-so --stack mobymask-v3-demo deploy init --output mobymask-v3-demo-spec.yml
  ```

* Create a deployment from the generated spec file:

  ```bash
  laconic-so --stack mobymask-v3-demo deploy create --spec-file mobymask-v3-demo-spec.yml --deployment-dir mobymask-v3-demo-deployment
  ```

* Copy over the demo config to place it at an appropriate path:

  ```bash
  cp mobymask-v3-demo-deployment/config/watcher-mobymask-v3-demo/local/config.env mobymask-v3-demo-deployment/
  ```

### Start the stack

* Start the deployment:

  ```bash
  laconic-so deployment --dir mobymask-v3-demo-deployment start

  # Useful ports exposed on host
  # 3001: MobyMask v3 watcher 1 GQL endpoint
  # 9090: MobyMask v3 watcher 1 relay node endpoint
  # 9091: MobyMask v3 watcher 2 relay node endpoint
  # 9092: MobyMask v3 watcher 3 relay node endpoint
  # 8080: MobyMask snap
  # 3004: MobyMask v3 app
  ```

  Note: This may take several minutes as it configures and runs the L1, L2 chains and the watchers; you can follow the progress from containers' logs

* To list and monitor the running containers:

  ```bash
  laconic-so deployment --dir mobymask-v3-demo-deployment ps

  # With status
  docker ps

  # Check logs for a container
  docker logs -f <CONTAINER_ID>
  ```

## Demo

Follow [demo](./demo.md) to try out the MobyMask app

## Clean up

To stop all services running in the background, while preserving data:

  ```bash
  laconic-so deployment --dir mobymask-v3-demo-deployment stop
  ```

To stop all services and also delete data:

  ```bash
  laconic-so deployment --dir mobymask-v3-demo-deployment stop --delete-volumes

  # Also remove the deployment directory
  rm -rf mobymask-v3-demo-deployment
  ```

## Known Issues

* Resource requirements (memory + time) for building the `cerc/foundry` image are on the higher side
  * `cerc/optimism-contracts` image is currently based on `cerc/foundry` (Optimism requires foundry installation)
