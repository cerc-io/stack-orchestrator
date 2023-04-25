# MobyMask Watcher P2P Network - Web App

Instructions to setup and deploy the MobyMask app locally, pointed to a watcher on the p2p network

## Prerequisites

* Laconic Stack Orchestrator ([installation](/README.md#install))
* Watcher GQL endpoint

## Setup

Build the container images:

  ```bash
  laconic-so --stack mobymask-v2 build-containers --include cerc/react-peer,cerc/mobymask-ui
  ```

Check that the required images are created in the local image registry:

  ```bash
  docker image ls

  # Expected output:

  # REPOSITORY                TAG      IMAGE ID       CREATED          SIZE
  # cerc/react-peer           local    d66b144dbb53   4 days ago       868MB
  # cerc/mobymask-ui          local    e456bf9937ec   4 days ago       1.67GB
  # .
  # .
  ```

## Deploy

### Configuration

Create an env file `mobymask-app.env`:

  ```bash
  touch mobymask-app.env
  ```

Add the following contents to `mobymask-app.env`:

  ```bash
  # Watcher endpoint used by the app for GQL queries
  CERC_APP_WATCHER_URL="http://127.0.0.1:3001"


  # DO NOT CHANGE THESE VALUES
  CERC_DEPLOYED_CONTRACT="0x2B6AFbd4F479cE4101Df722cF4E05F941523EaD9"
  CERC_RELAY_PEERS=["/dns4/relay1.dev.vdb.to/tcp/443/wss/p2p/12D3KooWAx83SM9GWVPc9v9fNzLzftRX6EaAFMjhYiFxRYqctcW1", "/dns4/relay2.dev.vdb.to/tcp/443/wss/p2p/12D3KooWBycy6vHVEfUwwYRbPLBdb5gx9gtFSEMpErYPUjUkDNkm", "/dns4/relay3.dev.vdb.to/tcp/443/wss/p2p/12D3KooWARcUJsiGCgiygiRVVK94U8BNSy8DFBbzAF3B6orrabwn"]
  ```

Replace `CERC_APP_WATCHER_URL` with the watcher's GQL endpoint

### Deploy the stack

```bash
laconic-so --stack mobymask-v2 deploy --cluster mm_v2 --include mobymask-app --env-file mobymask-app.env up lxdao-mobymask-app

# Expected output:

```

This will run the `lxdao-mobymask-app` (at `http://localhost:3004`) pointed to `CERC_APP_WATCHER_URL` for GQL queries

To monitor the running container:

  ```bash
  # With status
  docker ps

  # Expected output:


  # Check logs for a container
  docker logs -f mm_v2_lxdao-mobymask-app
  ```

Note: For opening an invite link on this deployed app, replace the URL part before `/#` with `http://localhost:3004`
For example: `http://localhost:3004/#/members?invitation=XYZ`

## Clean up

Stop all services running in the background:

  ```bash
  laconic-so --stack mobymask-v2 deploy --cluster mm_v2 --include mobymask-app down

  # Expected output:

  ```

Clear volumes created by this stack:

  ```bash
  # List all relevant volumes
  docker volume ls -q --filter "name=mm_v2"

  # Expected output:

  # Remove all the listed volumes
  docker volume rm $(docker volume ls -q --filter "name=mm_v2")
  ```
