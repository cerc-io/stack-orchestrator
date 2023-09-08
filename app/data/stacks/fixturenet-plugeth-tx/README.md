# fixturenet-plugeth-tx

A variation of `fixturenet-eth` that uses `plugeth` instead of `go-ethereum`.

See `stacks/fixturenet-eth/README.md` for more information.

## Containers

* cerc/lighthouse
* cerc/fixturenet-eth-plugeth
* cerc/fixturenet-eth-lighthouse
* cerc/tx-spammer

## Deploy the stack
Note: since some Go dependencies are currently private, `CERC_GO_AUTH_TOKEN` must be set to a valid Gitea access token before running the `build-containers` command.
```
$ laconic-so --stack fixturenet-plugeth-tx setup-repositories
$ laconic-so --stack fixturenet-plugeth-tx build-containers
$ laconic-so --stack fixturenet-plugeth-tx deploy up
```
