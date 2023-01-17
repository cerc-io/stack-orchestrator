# Spec

TODO: update

## Implementation
The orchestrator's operation is driven by files shown below. `repository-list.txt` container the list of git repositories; `container-image-list.txt` contains
the list of container image names, while `clister-list.txt` specifies the set of compose components (corresponding to individual docker-compose-xxx.yml files which may in turn specify more than one container).
Files required to build each container image are stored under `./container-build/<container-name>`
Files required at deploy-time are stored under `./config/<component-name>`
```
├── pod-list.txt
├── compose
│   ├── docker-compose-contract.yml
│   ├── docker-compose-db-sharding.yml
│   ├── docker-compose-db.yml
│   ├── docker-compose-eth-statediff-fill-service.yml
│   ├── docker-compose-go-ethereum-foundry.yml
│   ├── docker-compose-ipld-eth-beacon-db.yml
│   ├── docker-compose-ipld-eth-beacon-indexer.yml
│   ├── docker-compose-ipld-eth-server.yml
│   ├── docker-compose-lighthouse.yml
│   └── docker-compose-prometheus-grafana.yml
├── config
│   └── ipld-eth-server
├── container-build
│   ├── cerc-eth-statediff-fill-service
│   ├── cerc-go-ethereum
│   ├── cerc-go-ethereum-foundry
│   ├── cerc-ipld-eth-beacon-db
│   ├── cerc-ipld-eth-beacon-indexer
│   ├── cerc-ipld-eth-db
│   ├── cerc-ipld-eth-server
│   ├── cerc-lighthouse
│   └── cerc-test-contract
├── container-image-list.txt
├── repository-list.txt
```
