# Specification

Note: this page is out of date (but still useful) - it will no longer be useful once stacks are [decoupled from the tool functionality](https://git.vdb.to/cerc-io/stack-orchestrator/issues/315).

## Implementation

The orchestrator's operation is driven by files shown below.

- `repository-list.txt` contains the list of git repositories;
- `container-image-list.txt` contains the list of container image names
- `pod-list.txt` specifies the set of compose components (corresponding to individual docker-compose-xxx.yml files which may in turn specify more than one container).
- `container-build/` contains the files required to build each container image
- `config/` contains the files required at deploy time

```
├── container-image-list.txt
├── pod-list.txt
├── repository-list.txt
├── compose
│   ├── docker-compose-contract.yml
│   ├── docker-compose-eth-probe.yml
│   ├── docker-compose-eth-statediff-fill-service.yml
│   ├── docker-compose-fixturenet-eth.yml
│   ├── docker-compose-fixturenet-laconicd.yml
│   ├── docker-compose-go-ethereum-foundry.yml
│   ├── docker-compose-ipld-eth-beacon-db.yml
│   ├── docker-compose-ipld-eth-beacon-indexer.yml
│   ├── docker-compose-ipld-eth-db.yml
│   ├── docker-compose-ipld-eth-server.yml
│   ├── docker-compose-keycloak.yml
│   ├── docker-compose-laconicd.yml
│   ├── docker-compose-prometheus-grafana.yml
│   ├── docker-compose-test.yml
│   ├── docker-compose-tx-spammer.yml
│   ├── docker-compose-watcher-erc20.yml
│   ├── docker-compose-watcher-erc721.yml
│   ├── docker-compose-watcher-mobymask.yml
│   └── docker-compose-watcher-uniswap-v3.yml
├── config
│   ├── fixturenet-eth
│   ├── fixturenet-laconicd
│   ├── ipld-eth-beacon-indexer
│   ├── ipld-eth-server
│   ├── keycloak
│   ├── postgresql
│   ├── tx-spammer
│   ├── watcher-erc20
│   ├── watcher-erc721
│   ├── watcher-mobymask
│   └── watcher-uniswap-v3
├── container-build
│   ├── cerc-builder-js
│   ├── cerc-eth-probe
│   ├── cerc-eth-statediff-fill-service
│   ├── cerc-eth-statediff-service
│   ├── cerc-fixturenet-eth-geth
│   ├── cerc-fixturenet-eth-lighthouse
│   ├── cerc-go-ethereum
│   ├── cerc-go-ethereum-foundry
│   ├── cerc-ipld-eth-beacon-db
│   ├── cerc-ipld-eth-beacon-indexer
│   ├── cerc-ipld-eth-db
│   ├── cerc-ipld-eth-server
│   ├── cerc-keycloak
│   ├── cerc-laconic-registry-cli
│   ├── cerc-laconicd
│   ├── cerc-lighthouse
│   ├── cerc-test-container
│   ├── cerc-test-contract
│   ├── cerc-tx-spammer
│   ├── cerc-uniswap-v3-info
│   ├── cerc-watcher-erc20
│   ├── cerc-watcher-erc721
│   ├── cerc-watcher-mobymask
│   ├── cerc-watcher-uniswap-v3
└── stacks
    ├── erc20
    ├── erc721
    ├── fixturenet-eth
    ├── fixturenet-laconicd
    ├── mobymask
    └── uniswap-v3
```
