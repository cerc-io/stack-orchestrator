# mainnet-eth

Mainnet Ethereum stack (experimental)

## Clone required repositories

```
$ laconic-so --stack mainnet-eth setup-repositories
```

## Build the fixturenet-eth containers

```
$ laconic-so --stack mainnet-eth build-containers
```

This should create several container images in the local image registry:

* cerc/go-ethereum
* cerc/lighthouse
* cerc/fixturenet-eth-geth
* cerc/fixturenet-eth-lighthouse

## Create a deployment

```
$ laconic-so --stack mainnet-eth deploy create
```


## Clean up

Stop all services running in the background:

```bash
$ laconic-so deployment --dir <directory> down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
$ docker volume ls -q --filter "name=.*fixturenet_eth_bootnode_geth_data|.*fixturenet_eth_geth_1_data|.*fixturenet_eth_geth_2_data|.*fixturenet_eth_lighthouse_1_data|.*fixturenet_eth_lighthouse_2_data"

# Remove all the listed volumes
$ docker volume rm $(docker volume ls -q --filter "name=.*fixturenet_eth_bootnode_geth_data|.*fixturenet_eth_geth_1_data|.*fixturenet_eth_geth_2_data|.*fixturenet_eth_lighthouse_1_data|.*fixturenet_eth_lighthouse_2_data")
```
