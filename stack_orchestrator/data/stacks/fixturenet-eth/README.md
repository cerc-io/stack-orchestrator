# fixturenet-eth

Instructions for deploying a local a geth + lighthouse blockchain "fixturenet" for development and testing purposes using laconic-stack-orchestrator (the installation of which is covered [here](https://github.com/cerc-io/stack-orchestrator)):

## Clone required repositories

```
$ laconic-so --stack fixturenet-eth setup-repositories
```

## Build the fixturenet-eth containers

```
$ laconic-so --stack fixturenet-eth build-containers
```

This should create several container images in the local image registry:

* cerc/go-ethereum
* cerc/lighthouse
* cerc/fixturenet-eth-geth
* cerc/fixturenet-eth-lighthouse

## Deploy the stack

```
$ laconic-so --stack fixturenet-eth deploy up
```

## Check status

```
$ laconic-so --stack fixturenet-eth deploy exec fixturenet-eth-bootnode-lighthouse /scripts/status-internal.sh
Waiting for geth to generate DAG.... done
Waiting for beacon phase0.... done
Waiting for beacon altair.... done
Waiting for beacon bellatrix pre-merge.... done
Waiting for beacon bellatrix merge.... done

$ laconic-so --stack fixturenet-eth deploy ps
Running containers:
id: c6538b60c0328dadfa2c5585c4d09674a6a13e6d712ff1cd82a26849e4e5679b, name: laconic-b12fa16e999821562937781f8ab0b1e8-fixturenet-eth-bootnode-geth-1, ports: 0.0.0.0:58909->30303/tcp, 0.0.0.0:58910->9898/tcp
id: 5b70597a8211bc7e78d33e50486cb565a7f4a9ce581ce150b3bb450e342bdeda, name: laconic-b12fa16e999821562937781f8ab0b1e8-fixturenet-eth-bootnode-lighthouse-1, ports:
id: 19ed78867b6c534d893835cdeb1e89a9ea553b8e8c02ab02468e4bd1563a340f, name: laconic-b12fa16e999821562937781f8ab0b1e8-fixturenet-eth-geth-1-1, ports: 0.0.0.0:58911->40000/tcp, 0.0.0.0:58912->6060/tcp, 0.0.0.0:58913->8545/tcp
id: 8da0e30a1ce33122d8fd2225e4d26c7f30eb4bfbfa743f2af04d9db5d0bf7fa6, name: laconic-b12fa16e999821562937781f8ab0b1e8-fixturenet-eth-geth-2-1, ports:
id: 387a42a14971034588ba9aeb9b9e2ca7fc0cc61b96f8fe8c2ab770c9d6fb1e0f, name: laconic-b12fa16e999821562937781f8ab0b1e8-fixturenet-eth-lighthouse-1-1, ports: 0.0.0.0:58917->8001/tcp
id: de5115bf89087bae03b291664a73ffe3554fe23e79e4b8345e088b040d5580ac, name: laconic-b12fa16e999821562937781f8ab0b1e8-fixturenet-eth-lighthouse-2-1, ports:
id: 2a7e5a0fb2be7fc9261a7b725a40818facbbe6d0cb2497d82c0e02de0a8e959b, name: laconic-b12fa16e999821562937781f8ab0b1e8-foundry-1, ports:

$ laconic-so --stack fixturenet-eth deploy exec foundry "cast block-number"
3
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
$ laconic-so setup-repositories --include git.vdb.to/cerc-io/go-ethereum,git.vdb.to/cerc-io/ipld-eth-db,git.vdb.to/cerc-io/ipld-eth-server,github.com/cerc-io/ipld-eth-beacon-db,github.com/cerc-io/ipld-eth-beacon-indexer,github.com/cerc-io/eth-probe,git.vdb.to/cerc-io/tx-spammer

# Build
$ laconic-so build-containers --include cerc/go-ethereum,cerc/lighthouse,cerc/fixturenet-eth-geth,cerc/fixturenet-eth-lighthouse,cerc/ipld-eth-db,cerc/ipld-eth-server,cerc/ipld-eth-beacon-db,cerc/ipld-eth-beacon-indexer,cerc/eth-probe,cerc/keycloak,cerc/tx-spammer

# Deploy
$ laconic-so deploy-system --include db,fixturenet-eth,ipld-eth-server,ipld-eth-beacon-db,ipld-eth-beacon-indexer,eth-probe,keycloak,tx-spammer up

# Status

$ container-build/cerc-fixturenet-eth-lighthouse/scripts/status.sh
Waiting for geth to generate DAG.... done
Waiting for beacon phase0.... done
Waiting for beacon altair.... done
Waiting for beacon bellatrix pre-merge.... done
Waiting for beacon bellatrix merge.... done

$ docker ps -f 'name=laconic' --format 'table {{.Names}}\t{{.Ports}}'  | cut -d'-' -f3- | sort
NAMES                                                                           PORTS
eth-probe-db-1                         0.0.0.0:55849->5432/tcp
eth-probe-mq-1
eth-probe-probe-1
fixturenet-eth-bootnode-geth-1         8545-8546/tcp, 30303/udp, 0.0.0.0:55847->9898/tcp, 0.0.0.0:55848->30303/tcp
fixturenet-eth-bootnode-lighthouse-1
fixturenet-eth-geth-1-1                8546/tcp, 30303/tcp, 30303/udp, 0.0.0.0:55851->8545/tcp
fixturenet-eth-geth-2-1                8545-8546/tcp, 30303/tcp, 30303/udp
fixturenet-eth-lighthouse-1-1          0.0.0.0:55858->8001/tcp
fixturenet-eth-lighthouse-2-1
ipld-eth-beacon-db-1                   127.0.0.1:8076->5432/tcp
ipld-eth-beacon-indexer-1
ipld-eth-db-1                          127.0.0.1:8077->5432/tcp
ipld-eth-server-1                      127.0.0.1:8081-8082->8081-8082/tcp
keycloak-1                             8443/tcp, 0.0.0.0:55857->8080/tcp
keycloak-db-1                          0.0.0.0:55850->5432/tcp
keycloak-nginx-1                       0.0.0.0:55859->80/tcp
migrations-1
tx-spammer-1
```

## Clean up

Stop all services running in the background:

```bash
$ laconic-so --stack fixturenet-eth deploy down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
$ docker volume ls -q --filter "name=.*fixturenet_eth_bootnode_geth_data|.*fixturenet_eth_geth_1_data|.*fixturenet_eth_geth_2_data|.*fixturenet_eth_lighthouse_1_data|.*fixturenet_eth_lighthouse_2_data"

# Remove all the listed volumes
$ docker volume rm $(docker volume ls -q --filter "name=.*fixturenet_eth_bootnode_geth_data|.*fixturenet_eth_geth_1_data|.*fixturenet_eth_geth_2_data|.*fixturenet_eth_lighthouse_1_data|.*fixturenet_eth_lighthouse_2_data")
```
