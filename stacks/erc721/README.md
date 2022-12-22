# ERC721 Watcher

Instructions to deploy a local ERC721 watcher stack (core + watcher) for demonstration and testing purposes using [laconic-stack-orchestrator](../../README.md#setup)

## Setup

* Clone / pull required repositories:

  ```bash
  $ laconic-so setup-repositories --include cerc-io/go-ethereum,cerc-io/ipld-eth-db,cerc-io/ipld-eth-server,cerc-io/watcher-ts --pull
  ```

* Build the core and watcher container images:

  ```bash
  $ laconic-so build-containers --include cerc/go-ethereum,cerc/go-ethereum-foundry,cerc/ipld-eth-db,cerc/ipld-eth-server,cerc/watcher-erc721
  ```

  This should create the required docker images in the local image registry.

* Deploy the stack:

  ```bash
  $ laconic-so deploy-system --include db,go-ethereum-foundry,ipld-eth-server,watcher-erc721 up
  ```

