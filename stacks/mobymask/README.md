# MobyMask

The MobyMask watcher is a Laconic Network component that provides efficient access to MobyMask contract data from Ethereum, along with evidence allowing users to verify the correctness of that data. The watcher source code is available in [this repository](https://github.com/cerc-io/watcher-ts/tree/main/packages/mobymask-watcher) and a developer-oriented Docker Compose setup for the watcher can be found [here](https://github.com/cerc-io/mobymask-watcher). The watcher can be deployed automatically using the Laconic Stack Orchestrator tool as detailed below:

## Deploy the MobyMask Watcher
The instructions below show how to deploy a MobyMask watcher using laconic-stack-orchestrator (the installation of which is covered [here](https://github.com/cerc-io/stack-orchestrator#user-mode)).

This deployment expects that ipld-eth-server's endpoints are available on the local machine at http://ipld-eth-server.example.com:8083/graphql and http://ipld-eth-server.example.com:8082. More advanced configurations are supported by modifying the watcher's [config file](../../config/watcher-mobymask/mobymask-watcher.toml).
## Clone required repositories
```
$ laconic-so setup-repositories --include vulcanize/assemblyscript,cerc-io/watcher-ts
```
Checkout required branches for the current release:
```
$ cd ~/cerc/assemblyscript
$ git checkout ng-integrate-asyncify
$ cd ~/cerc/watcher-ts
$ git checkout v0.2.13
```
## Build the watcher container
```
$ laconic-sh build-containers --include cerc/watcher-mobymask
```
This should create a container with tag `cerc/watcher-mobymask` in the local image registry.
## Deploy the stack
First the watcher database has to be initialized. Start only the watcher-db service:
```
$ laconic-so deploy-system --include watcher-mobymask up watcher-db
```
Next find the container's id using `docker ps` then run the following command to initialize the database:
```
$ docker exec -i <watcher-db-container> psql -U vdbm mobymask-watcher < config/watcher-mobymask/mobymask-watcher-db.sql
```
Finally start the remaining containers:
```
$ laconic-so deploy-system --include watcher-mobymask
```
Correct operation should be verified by following the instructions [here](https://github.com/cerc-io/mobymask-watcher/tree/main/mainnet-watcher-only#run), checking GraphQL queries return valid results in the watcher's [playground](http://127.0.0.1:3001/graphql).
