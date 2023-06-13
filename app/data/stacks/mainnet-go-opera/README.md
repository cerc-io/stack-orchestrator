# Opera (Fantom)

Deploy and Fantom API or validator node.

## Clone required repositories

```
$ laconic-so --stack mainnet-go-opera setup-repositories
```

## Build the fixturenet-eth containers

```
$ laconic-so --stack mainnet-go-opera build-containers
```

## Deploy the stack

```
$ laconic-so --stack mainnet-go-opera deploy up
```

## Check status

TODO

## Additional pieces

TODO 

## Clean up

Stop all services running in the background:

```bash
$ laconic-so --stack mainnet-go-opera deploy down
```
