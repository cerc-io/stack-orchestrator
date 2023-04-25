# MobyMask Watcher P2P Network

Instructions to setup and deploy a watcher that connects to the existing watcher p2p network

## Prerequisites

* Laconic Stack Orchestrator ([installation](/README.md#install))
* A publicly reachable domain name with SSL setup

This demo has been tested on a `Ubuntu 22.04 LTS` machine with `8GB` of RAM

## Setup

Clone required repositories:

  ```bash
  laconic-so --stack mobymask-v2 setup-repositories --include cerc-io/MobyMask,cerc-io/watcher-ts,cerc-io/mobymask-v2-watcher-ts

  # This will clone the required repositories at ~/cerc
  # If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the repositories mentioned in the next step and re-run the command

  # Expected output:

  # Dev Root is: /home/xyz/cerc
  # Checking: /home/xyz/cerc/watcher-ts: Needs to be fetched
  # 100%|#############################################################################################################################################| 9.96k/9.96k [00:05<00:00, 1.70kB/s]
  # Checking: /home/xyz/cerc/mobymask-v2-watcher-ts: Needs to be fetched
  # 100%|################################################################################################################################################| 19.0/19.0 [00:01<00:00, 13.6B/s]
  # Checking: /home/xyz/cerc/MobyMask: Needs to be fetched
  # 100%|##############################################################################################################################################| 1.41k/1.41k [00:18<00:00, 76.4B/s]
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
  ```

Check that the required images are created in the local image registry:

  ```bash
  docker image ls

  # Expected output:

  # REPOSITORY                TAG      IMAGE ID       CREATED          SIZE
  # cerc/watcher-mobymask-v2  local    c4dba5dc8d48   24 seconds ago   1.02GB
  # cerc/watcher-ts           local    9ef61478c243   9 minutes ago    1.84GB
  # cerc/mobymask             local    9db3f1a69966   2 weeks ago      3.82GB
  # .
  # .
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
  CERC_RELAY_ANNOUNCE_DOMAIN="mobymask.example.com"


  # DO NOT CHANGE THESE VALUES
  CERC_L2_GETH_RPC="https://mobymask-l2.dev.vdb.to"
  CERC_DEPLOYED_CONTRACT="0x2B6AFbd4F479cE4101Df722cF4E05F941523EaD9"
  CERC_ENABLE_PEER_L2_TXS=false
  CERC_RELAY_PEERS=["/dns4/relay1.dev.vdb.to/tcp/443/wss/p2p/12D3KooWAx83SM9GWVPc9v9fNzLzftRX6EaAFMjhYiFxRYqctcW1", "/dns4/relay2.dev.vdb.to/tcp/443/wss/p2p/12D3KooWBycy6vHVEfUwwYRbPLBdb5gx9gtFSEMpErYPUjUkDNkm", "/dns4/relay3.dev.vdb.to/tcp/443/wss/p2p/12D3KooWARcUJsiGCgiygiRVVK94U8BNSy8DFBbzAF3B6orrabwn"]
  ```

Replace `CERC_RELAY_ANNOUNCE_DOMAIN` with your public domain name

### Deploy the stack

```bash
laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 --include watcher-mobymask-v2 --env-file mobymask-watcher.env up

# Expected output (ignore the "The X variable is not set. Defaulting to a blank string." warnings):

# [+] Running 9/9
#  ✔ Network mobymask_v2_default                      Created                            0.1s
#  ✔ Volume "mobymask_v2_peers_ids"                   Created                            0.0s
#  ✔ Volume "mobymask_v2_mobymask_watcher_db_data"    Created                            0.0s
#  ✔ Volume "mobymask_v2_mobymask_deployment"         Created                            0.0s
#  ✔ Container mobymask_v2-mobymask-watcher-db-1      Healthy                           22.2s
#  ✔ Container mobymask_v2-mobymask-1                 Exited                             2.2s
#  ✔ Container mobymask_v2-peer-ids-gen-1             Exited                            23.9s
#  ✔ Container mobymask_v2-mobymask-watcher-server-1  Healthy                           43.6s
#  ✔ Container mobymask_v2-peer-tests-1               Started                           44.5s
```

This will run the `mobymask-v2-watcher` including:
* A relay node which is in a federated setup with relay nodes set in the env file
* A peer node which connects to the watcher relay node as an entrypoint to the MobyMask watcher p2p network. This peer listens for messages from other peers on the network and logs them out to the console

The watcher GraphQL endpoint is exposed on host port `3001` and the relay node endpoint is exposed on host port `9090`

To list down and monitor the running containers:

  ```bash
  laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 --include watcher-mobymask-v2 ps

  # Expected output:

  # Running containers:
  # id: 25cc3a1cbda27fcd9c2ad4c772bd753ccef1e178f901a70e6ff4191d4a8684e9, name: mobymask_v2-mobymask-watcher-db-1, ports: 0.0.0.0:15432->5432/tcp
  # id: c9806f78680d68292ffe942222af2003aa3ed5d5c69d7121b573f5028444391d, name: mobymask_v2-mobymask-watcher-server-1, ports: 0.0.0.0:3001->3001/tcp, 0.0.0.0:9001->9001/tcp, 0.0.0.0:9090->9090/tcp
  # id: 6b30a1d313a88fb86f8a3b37a1b1a3bc053f238664e4b2d196c3ec74e04faf13, name: mobymask_v2-peer-tests-1, ports:


  # With status
  docker ps

  # Expected output:

  # CONTAINER ID   IMAGE                            COMMAND                  CREATED         STATUS                   PORTS                                                                    NAMES
  # 6b30a1d313a8   cerc/watcher-ts:local            "docker-entrypoint.s…"   5 minutes ago   Up 4 minutes                                                                                      mobymask_v2-peer-tests-1
  # c9806f78680d   cerc/watcher-mobymask-v2:local   "sh start-server.sh"     5 minutes ago   Up 5 minutes (healthy)   0.0.0.0:3001->3001/tcp, 0.0.0.0:9001->9001/tcp, 0.0.0.0:9090->9090/tcp   mobymask_v2-mobymask-watcher-server-1
  # 25cc3a1cbda2   postgres:14-alpine               "docker-entrypoint.s…"   5 minutes ago   Up 5 minutes (healthy)   0.0.0.0:15432->5432/tcp                                                  mobymask_v2-mobymask-watcher-db-1


  # Check logs for a container
  docker logs -f <CONTAINER_ID>
  ```

Check watcher container logs to get multiaddr advertised by the watcher's relay node and note it down for further usage:

  ```bash
  laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 --include watcher-mobymask-v2 logs mobymask-watcher-server | grep -A 2 "Relay node started"

  # The multiaddr will be of form /dns4/<CERC_RELAY_ANNOUNCE_DOMAIN>/tcp/443/wss/p2p/<RELAY_PEER_ID>
  # Expected output:

  # mobymask_v2-mobymask-watcher-server-1  | 2023-04-20T04:22:57.069Z laconic:relay Relay node started with id 12D3KooWKef84LAcBNb9wZNs6jC5kQFXjddo47hK6AGHD2dSvGai (characteristic-black-pamella)
  # mobymask_v2-mobymask-watcher-server-1  | 2023-04-20T04:22:57.069Z laconic:relay Listening on:
  # mobymask_v2-mobymask-watcher-server-1  | 2023-04-20T04:22:57.070Z laconic:relay /dns4/mobymask.example.com/tcp/443/wss/p2p/12D3KooWKef84LAcBNb9wZNs6jC5kQFXjddo47hK6AGHD2dSvGai
  ```

## Web App

To be able to connect to the relay node from remote peers, it needs to be publicly reachable.
Configure your website with SSL and the `https` traffic reverse proxied as:
* `/graphql` to port `3001` (watcher GQL endpoint)
* `/` to port `9090` (relay node)

For example, a Nginx configuration for domain `mobymask.example.com` would look something like:

  ```bash
  server {
    server_name mobymask.example.com;

    location /graphql {
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_pass http://127.0.0.1:3001;
      proxy_read_timeout 90;
    }

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
    ssl_certificate /etc/letsencrypt/live/mobymask.example.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/mobymask.example.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
  }

  server {
    if ($host = mobymask.example.com) {
      return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    listen [::]:80;

    server_name mobymask.example.com;
    return 404; # managed by Certbot
  }
  ```

To test the web-app, either visit https://mobymask-lxdao-app.dev.vdb.to/ or follow [web-app.md](./web-app.md) to deploy the app locally that hits your watcher's GQL endpoint

Connect a browser peer to the watcher's relay node:
* Click on debug panel on bottom right of the homepage
* Select `<custom>` in `Primary Relay` dropdown on the right and enter the watcher relay node's multiaddr
* Click on `UPDATE` to refresh the page and connect to the watcher's relay node; you should see the relay node's multiaddr in `Self Node Info` on the debug panel
* Switch to the `GRAPH (PEERS)` tab to see peers connected to this browser node and the `GRAPH (NETWORK)` tab to see the whole MobyMask p2p network

Perform transactions:
* An invitation is required to be able to perform transactions; ask an existing user of the app for an invite
* In a browser, close the app if it's already open and then open the invite link
* From the debug panel, confirm that the browser peer is connected to at least one other peer
* Check the status for a phisher to be reported in the `Check Phisher Status` section on homepage
* Select `Report Phisher` option in the `Pending reports` section, enter multiple phisher records and click on the `Submit batch to p2p network` button; this broadcasts signed invocations to peers on the network, including the watcher peer
* Check the watcher container logs to see the message received:
  ```bash
  docker logs $(docker ps -aq --filter name="mobymask-watcher-server")

  # Expected output:

  # .
  # .
  # 2023-04-20T04:42:01.072Z vulcanize:libp2p-utils [4:42:1] Received a message on mobymask P2P network from peer: 12D3KooWDKCke8hrjm4evwc9HzUzPZXeVTEQqmfLCkdNaXQ7efAZ
  # 2023-04-20T04:42:01.072Z vulcanize:libp2p-utils Signed invocations:
  # 2023-04-20T04:42:01.073Z vulcanize:libp2p-utils [
  #   {
  #     "signature": "0x18dc2f4092473cbcc4636eb922f6abf17675368363675779e67d2c14bb0a135f6029da12671a3367463d41720938c84bb3ceed727721c3bbc50d8739859412801c",
  #     "invocations": {
  #       "batch": [
  #         {
  #           "transaction": {
  #             "to": "0x2B6AFbd4F479cE4101Df722cF4E05F941523EaD9",
  #             "data": "0x6b6dc9de00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000c5457543a70686973686572310000000000000000000000000000000000000000",
  #             "gasLimit": 500000
  #           },
  #           "authority": [
  #             {
  #               "signature": "0x0f91c765faaf851550ddd4345d1bc11eebbf29fde0306a8051f9d3c679c6d6856f66753cad8fcff25203a3e0528b3d7673371343f66a39424f6281c474eada431c",
  #               "delegation": {
  #                 "delegate": "0x1B85a1485582C3389F62EB9F2C88f0C89bb1C1F4",
  #                 "authority": "0x0000000000000000000000000000000000000000000000000000000000000000",
  #                 "caveats": [
  #                   {
  #                     "enforcer": "0x2B6AFbd4F479cE4101Df722cF4E05F941523EaD9",
  #                     "terms": "0x0000000000000000000000000000000000000000000000000000000000000000"
  #                   }
  #                 ]
  #               }
  #             }
  #           ]
  #         }
  #       ],
  #       "replayProtection": {
  #         "nonce": 1,
  #         "queue": 64298938
  #       }
  #     }
  #   }
  # ]
  # 2023-04-20T04:42:01.087Z vulcanize:libp2p-utils method: claimIfPhisher, value: TWT:phisher1
  # 2023-04-20T04:42:01.087Z vulcanize:libp2p-utils ------------------------------------------
  # .
  # .
  ```
* Now, check the status for reported phishers again and confirm that they have been registered

## Clean up

Stop all services running in the background:

  ```bash
  laconic-so --stack mobymask-v2 deploy --cluster mobymask_v2 --include watcher-mobymask-v2 down

  # Expected output:

  # [+] Running 6/6
  #  ✔ Container mobymask_v2-peer-tests-1               Removed                   10.5s
  #  ✔ Container mobymask_v2-mobymask-watcher-server-1  Removed                   10.8s
  #  ✔ Container mobymask_v2-peer-ids-gen-1             Removed                    0.0s
  #  ✔ Container mobymask_v2-mobymask-1                 Removed                    0.0s
  #  ✔ Container mobymask_v2-mobymask-watcher-db-1      Removed                    0.6s
  #  ✔ Network mobymask_v2_default                      Removed                    0.5s
  ```

Clear volumes created by this stack:

  ```bash
  # List all relevant volumes
  docker volume ls -q --filter "name=mobymask_v2"

  # Expected output:

  # mobymask_v2_mobymask_deployment
  # mobymask_v2_mobymask_watcher_db_data
  # mobymask_v2_peers_ids


  # Remove all the listed volumes
  docker volume rm $(docker volume ls -q --filter "name=mobymask_v2")
  ```

## Troubleshooting

* If you don't see any peer connections being formed in the debug panel on https://mobymask-lxdao-app.dev.vdb.to/, try clearing out the website's local storage and refreshing the page
