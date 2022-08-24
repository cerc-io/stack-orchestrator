# Stack Orchestrator

Stack Orchestrator allows building and deployment of a Laconic stack on a single machine.

## Setup
### Developer Mode
Developer mode runs the orchestrator from a cloned git repository.
#### Prerequisites
1. Python3
1. Docker
#### Install
1. Clone this repository:
   ```
   $ git clone (https://github.com/cerc-io/stack-orchestrator.git
   ```
1. Enter the project directory:
   ```
   $ cd stack-orchestrator
   ```
1. Create and activate a venv:
   ```
   $ python3 -m venv venv
   $ source ./venv/bin/activate
   (venv) $
   ```
1. Install the cli in edit mode:
   ```
   $ pip install --editable .
   ```
1. Verify installation:
   ```
   (venv) $ laconic-so
   Usage: laconic-so [OPTIONS] COMMAND [ARGS]...

    Laconic Stack Orchestrator

   Options:
    --quiet
    --verbose
    --dry-run
    -h, --help  Show this message and exit.

   Commands:
    build-containers    build the set of containers required for a complete...
    deploy-system       deploy a stack
    setup-repositories  git clone the set of repositories required to build...
   ```
### CI Mode
_write-me_

## Usage
There are three sub-commands: `setup-repositories`, `build-containers` and `deploy-system` that are generally run in order:
### Setup Repositories
Clones the set of git repositories necessary to build a system.
```
$ laconic-so --verbose setup-repositories
```
### Build Containers
Builds the set of docker container images required to run a system.
```
$ laconic-so --verbose build-containers
```
### Deploy System
Uses `docker compose` to deploy a system.
```
$ laconic-so --verbose deploy-system --include db-sharding,contract,ipld-eth-server,go-ethereum-foundry up
```
## Implementation

```
├── cluster-list.txt
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

_write-more-of-me_
