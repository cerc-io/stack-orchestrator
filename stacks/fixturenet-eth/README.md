# fixturenet-eth

Instructions for deploying a local a geth + lighthouse blockchain "fixturenet" for development and testing purposes using laconic-stack-orchestrator (the installation of which is covered [here](https://github.com/cerc-io/stack-orchestrator#user-mode)):

## Clone required repositories
```
$ laconic-so setup-repositories --include cerc-io/go-ethereum
```

## Build the fixturenet-eth containers
```
$ laconic-so build-containers --include cerc/go-ethereum,cerc/lighthouse,cerc/fixturenet-eth-geth,cerc/fixturenet-eth-lighthouse
```
This should create several container in the local image registry: 

* cerc/go-ethereum
* cerc/lighthouse
* cerc/fixturenet-eth-geth
* cerc/fixturenet-eth-lighthouse

## Deploy the stack
```
$ laconic-so deploy-system --include fixturenet-eth up
```

## Check status

```
$ container-build/cerc-fixturenet-eth-lighthouse/scripts/status.sh
Waiting for geth to generate DAG ..................................................... DONE!
Waiting for beacon phase0 .... DONE!
Waiting for beacon altair .... DONE!
Waiting for beacon bellatrix pre-merge .... DONE!
Waiting for beacon bellatrix merge .... DONE!
```

## Additional pieces

Several other containers can used with the basic `fixturenet-eth`:

* `ipld-eth-db` (enables statediffing)
* `ipld-eth-server` (GQL and Ethereum API server, requires `ipld-eth-db`)
* `ipld-eth-beacon-db` and `ipld-eth-beacon-indexer` (for indexing Beacon chain blocks)
* `eth-probe` (captures eth1 tx gossip)
* `keycloak` (nginx proxy with keycloak auth for API authentication)
* `tx-spammer` (generates and sends automated transactions to the fixturenet)
	
It is not necessary to use them all at once, but a complete example follows:

```
# Setup
$ laconic-so setup-repositories --include cerc-io/go-ethereum,cerc-io/ipld-eth-db,cerc-io/ipld-eth-server,cerc-io/ipld-eth-beacon-db,cerc-io/ipld-eth-beacon-indexer,cerc-io/eth-probe,cerc-io/tx-spammer

# Build
$ laconic-so build-containers --include cerc/go-ethereum,cerc/lighthouse,cerc/fixturenet-eth-geth,cerc/fixturenet-eth-lighthouse,cerc/ipld-eth-db,cerc/ipld-eth-server,cerc/ipld-eth-beacon-db,cerc/ipld-eth-beacon-indexer,cerc/eth-probe,cerc/keycloak,cerc/tx-spammer

# Deploy
$ laconic-so deploy-system --include db,fixturenet-eth,ipld-eth-server,ipld-eth-beacon-db,ipld-eth-beacon-indexer,eth-probe,keycloak,tx-spammer up

# Status

$ container-build/cerc-fixturenet-eth-lighthouse/scripts/status.sh
Waiting for geth to generate DAG.... DONE!
Waiting for beacon phase0.... DONE!
Waiting for beacon altair.... DONE!
Waiting for beacon bellatrix pre-merge.... DONE!
Waiting for beacon bellatrix merge.... DONE!

$ docker ps -f 'name=laconic' --format '{{.Names}}' | cut -d'-' -f3- | sort
eth-probe-db-1
eth-probe-mq-1
eth-probe-probe-1
fixturenet-eth-bootnode-geth-1
fixturenet-eth-bootnode-lighthouse-1
fixturenet-eth-geth-1-1
fixturenet-eth-geth-2-1
fixturenet-eth-lighthouse-1-1
fixturenet-eth-lighthouse-2-1
ipld-eth-beacon-db-1
ipld-eth-beacon-indexer-1
ipld-eth-db-1
ipld-eth-server-1
keycloak-1
keycloak-db-1
keycloak-nginx-1
migrations-1
tx-spammer-1
```