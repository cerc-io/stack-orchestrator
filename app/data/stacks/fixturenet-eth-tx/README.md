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

## Export the ethdb (optional)

It is easy to export data from the fixturenet for offline processing of the raw ethdb files (eg, by eth-statediff-service) using the `export-ethdb.sh` script.

For example:

```
$ app/data/container-build/cerc-fixturenet-eth-lighthouse/scripts/export-ethdb.sh 500
Waiting for geth to generate DAG.... done
Waiting for beacon phase0.... done
Waiting for beacon altair.... done
Waiting for beacon bellatrix pre-merge.... done
Waiting for beacon bellatrix merge.... done
Waiting for block number 500.... done
Exporting ethdb.... ./ethdb.tgz
```
