# MobyMask Watcher P2P Network

Instructions to setup and deploy a MobyMask v2 watcher that joins in on the existing MobyMask v2 watcher p2p network

## Prerequisites

* Laconic Stack Orchestrator ([installation](/README.md#install))
* A publicly reachable domain name with SSL setup

This demo was tested on a `Ubuntu 22.04 LTS` machine with 8GBs of RAM

## Setup

Clone required repositories:

  ```bash
  laconic-so --stack mobymask-v2 setup-repositories --include cerc-io/MobyMask,cerc-io/watcher-ts,cerc-io/mobymask-v2-watcher-ts

  # This will clone the required repositories at ~/cerc
  # If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the repositories mentioned below and re-run the command
  ```

Checkout to the required versions and branches in repos:

  ```bash
  # watcher-ts
  cd ~/cerc/watcher-ts
  git checkout v0.2.39

  # mobymask-v2-watcher-ts
  cd ~/cerc/mobymask-v2-watcher-ts
  git checkout v0.1.0

  # MobyMask
  cd ~/cerc/MobyMask
  git checkout v0.1.2
  ```

Build the container images:

  ```bash
  laconic-so --stack mobymask-v2 build-containers --include cerc/watcher-ts,cerc/watcher-mobymask-v2,cerc/mobymask

  # This should create the required docker images (cerc/mobymask and cerc/watcher-mobymask-v2) in the local image registry
  ```

## Deploy

### Configuration

Create an env file `mobymask-watcher.env`:

  ```bash
  touch mobymask-watcher.env
  ```

Add the following contents to `mobymask-watcher.env`:

  ```bash
  # Domain to be used in the relay node's announce address
  CERC_RELAY_ANNOUNCE_DOMAIN='example.com'


  # Do not update
  CERC_DEPLOYED_CONTRACT="0x2b79F4a92c177B4E61F5c4AC37b1B8A623c665A4"
  CERC_ENABLE_PEER_L2_TXS=false
  CERC_RELAY_PEERS=['/dns4/relay1.dev.vdb.to/tcp/443/wss/p2p/12D3KooWPeiRZHym2LYTZsbDhciF8tXDimakXPfL4xkRG44s4QUB', '/dns4/relay2.dev.vdb.to/tcp/443/wss/p2p/12D3KooWJD6kLyqHayEkaFVrsDwdyYnPtr5nvjNT9CYTBQJHoYK4']
  ```

Replace `CERC_RELAY_ANNOUNCE_DOMAIN` with your public domain name

### Deploy the stack

```bash
laconic-so --stack mobymask-v2 deploy --include watcher-mobymask-v2 --env-file mobymask-watcher.env up

# Expected output:

```

This will run the `mobymask-v2-watcher` including:
* A relay node which is in a federated setup with relay nodes set in the env file
* A peer node which connects to the watcher relay node as an entrypoint to the MobyMask watcher p2p network. This peer listens for `mobymask` messages from other peers on the network and logs them out to the console

The watcher endpoint is exposed on host port `3001` and the relay node endpoint is exposed on host port `9090`

To list down and monitor the running containers:

  ```bash
  laconic-so --stack mobymask-v2 deploy --include watcher-mobymask-v2 ps

  # Expected output:


  # With status
  docker ps

  # Expected output:


  # Check logs for a container
  docker logs -f <CONTAINER_ID>
  ```

Check watcher container logs to get the multiaddr advertised by relay node:

  ```bash
  laconic-so --stack mobymask-v2 deploy --include watcher-mobymask-v2 logs mobymask-watcher-server | grep -A 3 "Relay node started"

  # Expected output:

  # The multiaddr will be of form /dns4/<CERC_RELAY_ANNOUNCE_DOMAIN>/tcp/443/wss/p2p/<RELAY_PEER_ID>
  ```

### Web App

To be able to connect to the relay node from remote peers, it needs to be publicly reachable (that's why need for a public domain). An example Nginx config for domain `example.com` with SSL and the traffic forwarded to `http://127.0.0.1:9090`:

  ```bash
  server {
    server_name example.com;

    # https://nginx.org/en/docs/http/websocket.html
    location / {
      proxy_pass http://127.0.0.1:9090;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";

      # set a large timeout to avoid websocket disconnects
      proxy_read_timeout 86400;
    }

    listen [::]:443 ssl ipv6only=on; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
  }

  server {
    if ($host = example.com) {
      return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    listen [::]:80;

    server_name example.com;
    return 404; # managed by Certbot
  }
  ```

To connect a browser peer to the watcher's relay node:
* Visit https://mobymask-app.dev.vdb.to/
* Click on the debug panel on bottom right of homepage
* Enter the watcher relay node's multiaddr as the `Primary Relay` and click on `UPDATE` (TODO: UPDATE)
* This will refresh the page and connect to the watcher's relay node; you should see the relay multiaddr in `Self Node Info` on the debug panel
* Switch to the `GRAPH (PEERS)` tab to see peers connected to this browser node and the `GRAPH (NETWORK)` tab to see the whole MobyMask p2p network

Perform transactions (invite requried):
* Open the invite link in a browser
* From the debug panel, confirm that the browser peer is connected to at least one other peer
* In `Report a phishing attempt` section, report multiple phishers using the `Submit` button. Click on the `Submit batch to p2p network` button; this broadcasts signed invocations to the peers on the network, including the watcher peer
* Check the watcher container logs to see the message received:

  ```bash
  docker logs -f $(docker ps -aq --filter name="mobymask-watcher-server")

  # Expected output
  ```
