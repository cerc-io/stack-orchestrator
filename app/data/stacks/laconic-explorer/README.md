# Laconicd Explorer

Instructions for first deploying a local Laconic blockchain "fixturenet," and then then deploying a block explorer. The explorer stack has two containers:  
- an Nginx image to serve the explorer app, Ping.pub[https://github.com/ping-pub/explorer], configured for Laconicd
- a non-consensus Laconicd full node to connect with the fixturenet and provide chain data to the explorer

## Prerequisites
http vs https

## 1. Start a Laconicd Fixturenet
Follow the instructions here[https://github.com/cerc-io/stack-orchestrator/tree/main/app/data/stacks/fixturenet-laconicd] to start a Laconicd fixturenet.  
Verify that it is running correctly and producing blocks with:
```
$ laconic-so --stack fixturenet-laconicd deploy logs
```

## 2. Connection requirements
The explorer's full node will need to connect to the fixturenet and sync with the chain. To connect with an already running chain (such as the one created in step 1) we will need:
- the address of at least one peer (node_id@IP.address:port)
- the genesis.json file for the chain  

Get the node id of the fixturenet validator and save it for later:
```
command
```
Copy the genesis.json file to the host to a directory of your choice for later:
```
command
```

## 3. Clone explorer repositories
```
$ laconic-so --stack laconic-explorer setup-repositories
```

## 4. Set environment variables
Some environment variables need to be set prior to container build. The build script will look for a file named `laconic-explorer.env` in the explorer repo that was cloned in step 3 (`$HOME/cerc/explorer` by default). Create the file with the following content:
```
## -- Container build -- ##

# whether to configure nginx for https
USE_HTTPS="false"

# domain name hosting the explorer, required if using https
# eg: "laconic.run"
# EXPLORER_DOMAIN=""

# or IP address hosting the explorer, required if not using https
EXPLORER_IP=""

# (optional) nginx will listen on this port for laconicd rest api requests from the client
# not needed if using https
# will default to 1317 if not set
# export API_PORT=1317

# (optional) nginx will listen on this port for tendermint rpc requests from the client
# not needed if using https
# will default to 26657 if not set
# export RPC_PORT=26657

## -- Container deploy -- ##

# comma separated list of peers in the format "node_id@IP:port,node_id@IP:port,..."
# at least one peer is required
PEERS=""

# (required) path to genesis.json file on host, will be copied into laconicd container
# eg: /home/user/.laconic-explorer/genesis.json
export GENESIS_FILE="/path/to/genesis.json"

# chain id of the fixturenet
export CHAIN_ID="laconic_9000-1"

# (optional) peer to peer listen port to publish on host for the laconic node
# will default to 27656 if not set
# export P2P_PORT=27656

```
---
## *Setup for HTTP:*
In `laconic-explorer.env`, set `EXPLORER_IP` to the IP address that will be serving the explorer webpage. *E.g.:* if using a Digital Ocean droplet, set it to your droplet's public IP.  
  
You will also need to make sure that ports `80`, `API_PORT` and `RPC_PORT` are open on your firewall.
## 5a. Build containers
```
$ laconic-so --stack laconic-explorer build-containers
```
## 6a. Deploy stack
In `laconic-explorer.env`, set `PEERS` to the value of the fixturenet validator (node_id@IP.address:P2P-port). *E.g.:* if running the demo on a DO droplet, it would look something like ``PEERS={node_id}@{droplet IP}:26656`  
  
Set `GENESIS_FILE` to the location on the host of `genesis.json` you copied from the fixturenet.  
  
Source the `laconic-explorer.env` file and deploy the stack:
```
$ source ~/cerc/explorer/laconic-explorer.env
$ laconic-so --stack laconic-explorer deploy up
```
  
You should now be able to view the explorer by opening `http://EXPLORER_IP` in your web browser. (It may take a few minutes for the explorer's full node to sync up to the head of the fixturenet chain).
  
## *Setup for HTTPS:*
Before starting, you will need a domain name (we'll use `laconic.run` in the examples; yours will be different) with the following A records set to your IP:
- `laconic.run`
- `www.laconic.run`
- `api.laconic.run`
- `rpc.laconic.run`
  
In `laconic-explorer.env`, set `USE_HTTPS` to `"true"` and set `EXPLORER_DOMAIN` to your domain.
  
You will also need to make sure that ports `80` and `443` are open on your firewall.

## 5b. Request SSL certificate with Let's Encrypt
Install Let's Encrypt certbot:
```
$ sudo apt install certbot -y
```
Request a single SSL cert for your domain and two subdomains:
```
sudo certbot certonly -d laconic.run -d api.laconic.run -d rpc.laconic.run --register-unsafely-without-email --no-redirect --agree-tos
```
?additional steps?
Check that the certificate was added correctly:
```
sudo certbot certificates
sudo ls /etc/letsencrypt/live/laconic.run
```
## 6b. Build containers
```
$ laconic-so --stack laconic-explorer build-containers
```
## 7b. Deploy stack
In `laconic-explorer.env`, set `PEERS` and `GENESIS_FILE` as above (step 6a).
  
Source the `laconic-explorer.env` file and deploy the stack:
```
$ source ~/cerc/explorer/laconic-explorer.env
$ laconic-so --stack laconic-explorer deploy up
```
  
You should now be able to view the explorer by opening `https://{your.domain}` in your web browser. (It may take a few minutes for the explorer's full node to sync up to the head of the fixturenet chain).
