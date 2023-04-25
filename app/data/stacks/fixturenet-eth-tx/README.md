# fixturenet-eth-tx

A variation of `fixturenet-eth` that automatically generates transactions using `tx-spammer`.

See `stacks/fixturenet-eth/README.md` for more information.

## Containers

* cerc/go-ethereum
* cerc/lighthouse
* cerc/fixturenet-eth-geth
* cerc/fixturenet-eth-lighthouse
* cerc/tx-spammer

## Deploy the stack
```
$ laconic-so --stack fixturenet-eth-tx setup-repositories
$ laconic-so --stack fixturenet-eth-tx build-containers
$ laconic-so --stack fixturenet-eth-tx deploy up
```
