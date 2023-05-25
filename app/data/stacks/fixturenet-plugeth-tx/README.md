# fixturenet-plugeth-tx

A variation of `fixturenet-eth` that uses `plugeth` instead of `go-ethereum`.

See `stacks/fixturenet-eth/README.md` for more information.

## Containers

* cerc/plugeth
* cerc/lighthouse
* cerc/fixturenet-eth-plugeth
* cerc/fixturenet-eth-lighthouse
* cerc/tx-spammer

## Deploy the stack
```
$ laconic-so --stack fixturenet-plugeth-tx setup-repositories
$ laconic-so --stack fixturenet-plugeth-tx build-containers
$ laconic-so --stack fixturenet-plugeth-tx deploy up
```
