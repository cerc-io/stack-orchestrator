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
  CERC_RELAY_NODES=["/dns4/relay1.dev.vdb.to/tcp/443/wss/p2p/12D3KooWAx83SM9GWVPc9v9fNzLzftRX6EaAFMjhYiFxRYqctcW1", "/dns4/relay2.dev.vdb.to/tcp/443/wss/p2p/12D3KooWBycy6vHVEfUwwYRbPLBdb5gx9gtFSEMpErYPUjUkDNkm", "/dns4/relay3.dev.vdb.to/tcp/443/wss/p2p/12D3KooWARcUJsiGCgiygiRVVK94U8BNSy8DFBbzAF3B6orrabwn"]
  ```

Replace `CERC_APP_WATCHER_URL` with the watcher's endpoint (eg. `https://mobymask.example.com`)

### Deploy the stack

```bash
laconic-so --stack mobymask-v2 deploy --cluster mm_v2 --include mobymask-app --env-file mobymask-app.env up lxdao-mobymask-app

# Expected output (ignore the "The X variable is not set. Defaulting to a blank string." warnings):

# [+] Running 4/4
#  ✔ Network mm_v2_default                            Created                            0.1s
#  ✔ Volume "mm_v2_peers_ids"                         Created                            0.0s
#  ✔ Volume "mm_v2_mobymask_deployment"               Created                            0.0s
#  ✔ Container mm_v2-lxdao-mobymask-app-1             Started                            1.1s
```

This will run the `lxdao-mobymask-app` (at `http://localhost:3004`) pointed to `CERC_APP_WATCHER_URL` for GQL queries

To monitor the running container:

  ```bash
  # With status
  docker ps

  # Expected output:

  # CONTAINER ID   IMAGE                    COMMAND                  CREATED         STATUS                   PORTS                  NAMES
  # f1369dbae1c9   cerc/mobymask-ui:local   "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:3004->80/tcp   mm_v2-lxdao-mobymask-app-1

  # Check logs for a container
  docker logs -f mm_v2-lxdao-mobymask-app-1

  # Expected output:

  # .
  # .
  # .
  # Available on:
  #   http://127.0.0.1:80
  #   http://192.168.0.2:80
  # Hit CTRL-C to stop the server
  ```

Note: For opening an invite link on this deployed app, replace the URL part before `/#` with `http://localhost:3004`
For example: `http://localhost:3004/#/members?invitation=XYZ`

## Clean up

Stop all services running in the background:

  ```bash
  laconic-so --stack mobymask-v2 deploy --cluster mm_v2 --include mobymask-app down

  # Expected output:

  # [+] Running 2/2
  #  ✔ Container mm_v2-lxdao-mobymask-app-1             Removed                   10.6s
  #  ✔ Network mm_v2_default                            Removed                    0.5s
  ```

Clear volumes created by this stack:

  ```bash
  # List all relevant volumes
  docker volume ls -q --filter "name=mm_v2"

  # Expected output:

  # mm_v2_mobymask_deployment
  # mm_v2_peers_ids

  # Remove all the listed volumes
  docker volume rm $(docker volume ls -q --filter "name=mm_v2")
  ```
