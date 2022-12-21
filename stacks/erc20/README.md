# ERC20 Watcher

## Setup

### Clone required repositories

```bash
$ laconic-so setup-repositories --include cerc-io/go-ethereum,cerc-io/ipld-eth-db,cerc-io/ipld-eth-server,cerc-io/watcher-ts
```

### Build the core and watcher containers

```bash
$ laconic-so build-containers --include cerc/go-ethereum,cerc/go-ethereum-foundry,cerc/ipld-eth-db,cerc/ipld-eth-server,cerc/watcher-erc20
```

### Deploy the stack

```bash
$ laconic-so deploy-system --include db,go-ethereum-foundry,ipld-eth-server,watcher-erc20 up
```

