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
Waiting for geth to generate DAG ....................................................................................................................................................................................................... DONE!
Waiting for beacon phase0 .... DONE!
Waiting for beacon altair .... DONE!
Waiting for beacon bellatrix pre-merge .... DONE!
Waiting for beacon bellatrix merge .... DONE!
```

## Additonal pieces

Several other containers can used with the basic `fixturenet-eth`:

  * `ipld-eth-db` (enables statediffing)
	* `ipld-eth-server` (GQL and Ethereum API server, requires `ipld-eth-db`)
	* `ipld-eth-beacon-db` and `ipld-eth-beacon-indexer` (for indexing Beacon chain blocks)
	* `eth-probe` (captures eth1 tx gossip)
	* `keycloak` (nginx proxy with keycloak auth for API authentication)
	
It is not necessary to use them all, but a complete example follows:

```
# Checkout 
$ laconic-so setup-repositories --include cerc-io/go-ethereum,cerc-io/ipld-eth-db,cerc-io/ipld-eth-server,cerc-io/ipld-eth-beacon-db,cerc-io/ipld-eth-beacon-indexer,cerc-io/eth-probe

# Build
$ laconic-so build-containers --include cerc/go-ethereum,cerc/lighthouse,cerc/fixturenet-eth-geth,cerc/fixturenet-eth-lighthouse,cerc/ipld-eth-db,cerc/ipld-eth-server,cerc/ipld-eth-beacon-db,cerc/ipld-eth-beacon-indexer,cerc/eth-probe,cerc/keycloak

# Run
$ laconic-so deploy-system --include db,fixturenet-eth,ipld-eth-server,ipld-eth-beacon-db,ipld-eth-beacon-indexer,eth-probe,keycloak up

# Status

$ container-build/cerc-fixturenet-eth-lighthouse/scripts/status.sh
Waiting for geth to generate DAG.... DONE!
Waiting for beacon phase0.... DONE!
Waiting for beacon altair.... DONE!
Waiting for beacon bellatrix pre-merge.... DONE!
Waiting for beacon bellatrix merge.... DONE!

$ docker ps -f 'name=laconic'
CONTAINER ID   IMAGE                                  COMMAND                  CREATED         STATUS                   PORTS                                                                         NAMES
fe60af64140c   cerc/ipld-eth-beacon-indexer:local     "./entrypoint.sh"        4 minutes ago   Up 3 minutes                                                                                           laconic-7ca8f4a970d7999a235e0ee27588a5ab-ipld-eth-beacon-indexer-1
015583b318c2   cerc/eth-probe:local                   "/app/run.sh"            4 minutes ago   Up 3 minutes                                                                                           laconic-7ca8f4a970d7999a235e0ee27588a5ab-eth-probe-probe-1
180b03993b1e   nginx:1.23-alpine                      "/docker-entrypoint.…"   4 minutes ago   Up 4 minutes             0.0.0.0:54162->80/tcp                                                         laconic-7ca8f4a970d7999a235e0ee27588a5ab-keycloak-nginx-1
2e963e3c4b44   cerc/ipld-eth-server:local             "/app/entrypoint.sh"     4 minutes ago   Up 4 minutes             127.0.0.1:8081-8082->8081-8082/tcp                                            laconic-7ca8f4a970d7999a235e0ee27588a5ab-ipld-eth-server-1
913cefc5cecf   cerc/fixturenet-eth-lighthouse:local   "/opt/testnet/run.sh"    4 minutes ago   Up 4 minutes (healthy)   0.0.0.0:54161->8001/tcp                                                       laconic-7ca8f4a970d7999a235e0ee27588a5ab-fixturenet-eth-lighthouse-1-1
c0659d0204ff   cerc/fixturenet-eth-lighthouse:local   "/opt/testnet/run.sh"    4 minutes ago   Up 3 minutes (healthy)                                                                                 laconic-7ca8f4a970d7999a235e0ee27588a5ab-fixturenet-eth-lighthouse-2-1
1636ed1013a6   cerc/keycloak:local                    "/opt/keycloak/bin/k…"   4 minutes ago   Up 4 minutes             8443/tcp, 0.0.0.0:54160->8080/tcp                                             laconic-7ca8f4a970d7999a235e0ee27588a5ab-keycloak-1
439b017d75c1   cerc/ipld-eth-db:local                 "/app/startup_script…"   4 minutes ago   Up 4 minutes                                                                                           laconic-7ca8f4a970d7999a235e0ee27588a5ab-migrations-1
0a2c740a8e12   cerc/eth-probe:local                   "/app/run.sh"            4 minutes ago   Up 4 minutes (healthy)                                                                                 laconic-7ca8f4a970d7999a235e0ee27588a5ab-eth-probe-mq-1
35a816e0bac1   cerc/fixturenet-eth-geth:local         "/opt/testnet/run.sh"    4 minutes ago   Up 4 minutes (healthy)   8546/tcp, 30303/tcp, 30303/udp, 0.0.0.0:54154->8545/tcp                       laconic-7ca8f4a970d7999a235e0ee27588a5ab-fixturenet-eth-geth-1-1
6691e5988519   cerc/fixturenet-eth-geth:local         "/opt/testnet/run.sh"    4 minutes ago   Up 4 minutes (healthy)   8545-8546/tcp, 30303/tcp, 30303/udp                                           laconic-7ca8f4a970d7999a235e0ee27588a5ab-fixturenet-eth-geth-2-1
06602dc7e3d0   timescale/timescaledb:latest-pg14      "docker-entrypoint.s…"   4 minutes ago   Up 4 minutes (healthy)   0.0.0.0:54153->5432/tcp                                                       laconic-7ca8f4a970d7999a235e0ee27588a5ab-eth-probe-db-1
91d73ec45b97   cerc/ipld-eth-beacon-db:local          "docker-entrypoint.s…"   4 minutes ago   Up 4 minutes (healthy)   127.0.0.1:8076->5432/tcp                                                      laconic-7ca8f4a970d7999a235e0ee27588a5ab-ipld-eth-beacon-db-1
48459978329c   postgres:14-alpine                     "docker-entrypoint.s…"   4 minutes ago   Up 4 minutes (healthy)   0.0.0.0:54152->5432/tcp                                                       laconic-7ca8f4a970d7999a235e0ee27588a5ab-keycloak-db-1
f48169806b54   timescale/timescaledb:2.8.1-pg14       "docker-entrypoint.s…"   4 minutes ago   Up 4 minutes (healthy)   127.0.0.1:8077->5432/tcp                                                      laconic-7ca8f4a970d7999a235e0ee27588a5ab-ipld-eth-db-1
56686c4e004f   cerc/fixturenet-eth-geth:local         "/opt/testnet/run.sh"    4 minutes ago   Up 4 minutes             8545-8546/tcp, 30303/udp, 0.0.0.0:54151->9898/tcp, 0.0.0.0:54150->30303/tcp   laconic-7ca8f4a970d7999a235e0ee27588a5ab-fixturenet-eth-bootnode-geth-1
95f073c5e956   cerc/fixturenet-eth-lighthouse:local   "/opt/testnet/run.sh"    4 minutes ago   Up 4 minutes                                                                                           laconic-7ca8f4a970d7999a235e0ee27588a5ab-fixturenet-eth-bootnode-lighthouse-1
```

