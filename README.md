# Stack Orchestrator

Stack Orchestrator allows building and deployment of a Laconic Stack on a single machine with minimial prerequisites. It is a Python3 CLI tool that runs on any OS with Python3 and Docker. The following diagram summarizes the relevant repositories in the Laconic Stack - and the relationship to Stack Orchestrator.

![The Stack](/docs/images/laconic-stack.png)

## Install

Ensure that the following are already installed:

- [Python3](https://wiki.python.org/moin/BeginnersGuide/Download): `python3 --version` >= `3.10.8`
- [Docker](https://docs.docker.com/get-docker/): `docker --version` >= `20.10.21`
- [Docker Compose](https://docs.docker.com/compose/install/): `docker-compose --version` >= `2.13.0`

Note: if installing docker-compose via package manager (as opposed to Docker Desktop), you must [install the plugin](https://docs.docker.com/compose/install/linux/#install-the-plugin-manually), e.g., on Linux:

```bash
mkdir -p ~/.docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.11.2/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
```

Next, download the latest release from [this page](https://github.com/cerc-io/stack-orchestrator/tags), into a suitable directory (e.g. `~/bin`):

```bash
curl -L -o ~/bin/laconic-so https://github.com/cerc-io/stack-orchestrator/releases/latest/download/laconic-so
```

Give it permissions:
```bash
chmod +x ~/bin/laconic-so
```

Ensure `laconic-so` is on the [`PATH`](https://unix.stackexchange.com/a/26059)

Verify operation:

```
laconic-so --help
Usage: python -m laconic-so [OPTIONS] COMMAND [ARGS]...

  Laconic Stack Orchestrator

Options:
  --quiet
  --verbose
  --dry-run
  --local-stack
  -h, --help     Show this message and exit.

Commands:
  build-containers    build the set of containers required for a complete...
  build-npms          build the set of npm packages required for a...  
  deploy-system       deploy a stack
  setup-repositories  git clone the set of repositories required to build...
```

## Usage

Three sub-commands: `setup-repositories`, `build-containers` and `deploy-system` are generally run in order. The following is a slim example for standing up the `erc20-watcher`. Go further with the [erc20 watcher demo](/app/data/stacks/erc20) and other pieces of the stack, within the [`stacks` directory](/app/data/stacks).

### Setup Repositories

Clone the set of git repositories necessary to build a system:

```bash
laconic-so --verbose setup-repositories --include cerc-io/go-ethereum,cerc-io/ipld-eth-db,cerc-io/ipld-eth-server,cerc-io/watcher-ts
```

This will default to `~/cerc` or - if set - the environment variable `CERC_REPO_BASE_DIR`

### Build Containers

Build the set of docker container images required to run a system. It takes around 10 minutes to build all the containers from scratch.

```bash
laconic-so --verbose build-containers --include cerc/go-ethereum,cerc/go-ethereum-foundry,cerc/ipld-eth-db,cerc/ipld-eth-server,cerc/watcher-erc20
```

### Deploy System

Uses `docker-compose` to deploy a system (with most recently built container images).

```bash
laconic-so --verbose deploy-system --include ipld-eth-db,go-ethereum-foundry,ipld-eth-server,watcher-erc20 up
```

Check out he GraphQL playground here: [http://localhost:3002/graphql](http://localhost:3002/graphql)

See the [erc20 watcher demo](/app/data/stacks/erc20) to continue further.

### Cleanup

```bash
laconic-so --verbose deploy-system --include ipld-eth-db,go-ethereum-foundry,ipld-eth-server,watcher-erc20 down
```

## Contributing

See the [CONTRIBUTING.md](/docs/CONTRIBUTING.md) for developer mode install.

## Platform Support

Native aarm64 is _not_ currently supported. x64 emulation on ARM64 macos should work (not yet tested).

