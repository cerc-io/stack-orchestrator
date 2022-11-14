# Stack Orchestrator

Stack Orchestrator allows building and deployment of a Laconic stack on a single machine with minimial prerequisites.

## Setup
### Developer Mode
Developer mode runs the orchestrator from a cloned git repository.
#### Prerequisites
Stack Orchestrator is a Python3 CLI tool that runs on any OS with Python3 and Docker. Tested on: Ubuntu 20/22.

Ensure that the following are already installed:

1. Python3 (the version 3.8 available in Ubuntu 20/22 works)
   ```
   $ python3 --version
   Python 3.8.10
   ```
1. Python venv package
   This may or may not be already installed depending on the host OS and version. Check by running:
   ```
   $ python3 -m venv
   usage: venv [-h] [--system-site-packages] [--symlinks | --copies] [--clear] [--upgrade] [--without-pip] [--prompt PROMPT] ENV_DIR [ENV_DIR ...]
   venv: error: the following arguments are required: ENV_DIR
   ```
   If the venv package is missing you should see a message indicating how to install it, for example with:
   ```
   $ apt install python3.8-venv
   ```
2. Docker (Install a current version from dockerco, don't use the version from any Linux distro)
   ```
   $ docker --version
   Docker version 20.10.17, build 100c701
   ```
3. If installed from regular package repository (not Docker Desktop), BE AWARE that the compose plugin may need to be installed, as well.
   ```
   DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
   mkdir -p $DOCKER_CONFIG/cli-plugins
   curl -SL https://github.com/docker/compose/releases/download/v2.11.2/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
   chmod +x ~/.docker/cli-plugins/docker-compose
   
   # see https://docs.docker.com/compose/install/linux/#install-the-plugin-manually for further details
   # or to install for all users.
   ```
#### Install
1. Clone this repository:
   ```
   $ git clone (https://github.com/cerc-io/stack-orchestrator.git
   ```
4. Enter the project directory:
   ```
   $ cd stack-orchestrator
   ```
5. Create and activate a venv:
   ```
   $ python3 -m venv venv
   $ source ./venv/bin/activate
   (venv) $
   ```
6. Install the cli in edit mode:
   ```
   $ pip install --editable .
   ```
7. Verify installation:
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
#### Build a zipapp (single file distributable script)
Use shiv to build a single file Python executable zip archive of laconic-so:
1. Install [shiv](https://github.com/linkedin/shiv):
   ```
   $ (venv) pip install shiv
   $ (venv) pip install wheel
   ```
1. Run shiv to create a zipapp file:
   ```
   $ (venv)  shiv -c laconic-so -o laconic-so .
   ```
   This creates a file `./laconic-so` that is executable outside of any venv, and on other machines and OSes and architectures, and requiring only the system Python3:
1. Verify it works:
   ```
   $ cp stack-orchetrator/laconic-so ~/bin
   $ laconic-so
      Usage: python -m laconic-so [OPTIONS] COMMAND [ARGS]...

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

Note: $ laconic-so will run the version installed to ~/bin, while ./laconic-so can be invoked to run locally built 
version in a checkout
### Setup Repositories
Clones the set of git repositories necessary to build a system.

Note: the use of `ssh-agent` is recommended in order to avoid entering your ssh key passphrase for each repository.
```
$ laconic-so --verbose setup-repositories #this will default to ~/cerc or CERC_REPO_BASE_DIR from an env file
#$ ./laconic-so --verbose --local-stack setup-repositories #this will use cwd ../ as dev_root_path
```
### Build Containers
Builds the set of docker container images required to run a system. It takes around 10 minutes to build all the containers from cold.
```
$ laconic-so --verbose build-containers #this will default to ~/cerc or CERC_REPO_BASE_DIR from an env file
#$ ./laconic-so --verbose --local-stack build-containers #this will use cwd ../ as dev_root_path

```
### Deploy System
Uses `docker compose` to deploy a system.

Use `---include <list of components>` to deploy a subset of all containers:
```
$ laconic-so --verbose deploy-system --include db-sharding,contract,ipld-eth-server,go-ethereum-foundry up
```
```
$ laconic-so --verbose deploy-system --include db-sharding,contract,ipld-eth-server,go-ethereum-foundry down
```
Note: deploy-system command interacts with most recently built container images.

## Platform Support
Native aarm64 is _not_ currently supported. x64 emulation on ARM64 macos should work (not yet tested).
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

_write-more-of-me_
