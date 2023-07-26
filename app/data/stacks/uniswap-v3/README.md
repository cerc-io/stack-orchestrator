# Uniswap v3

Instructions to deploy Uniswap v3 watcher stack (watcher + uniswap-v3-info frontend app) using [laconic-stack-orchestrator](../../README.md#setup)

## Prerequisites

* Access to [uniswap-watcher-ts](https://github.com/vulcanize/uniswap-watcher-ts).

* This deployment expects core services to be running; specifically, it requires `ipld-eth-server` RPC and GQL endpoints. Update the `upstream.ethServer` endpoints in the [watcher config files](../../config/watcher-uniswap-v3) accordingly:

  ```toml
  [upstream]
    [upstream.ethServer]
      gqlApiEndpoint = "http://ipld-eth-server.example.com:8083/graphql"
      rpcProviderEndpoint = "http://ipld-eth-server.example.com:8082"
  ```

* `uni-watcher` and `uni-info-watcher` database dumps (optional).

## Setup

* Clone / pull required repositories:

  ```bash
  $ laconic-so --stack uniswap-v3 setup-repositories
  ```

* Build watcher and info app container images:

  ```bash
  $ laconic-so --stack uniswap-v3 build-containers
  ```

  This should create the required docker images in the local image registry.

## Deploy

* (Optional) Initialize the watcher database with existing database dumps if available:

  * Start the watcher database to be initialized:

    ```bash
    $ laconic-so deploy-system --include watcher-uniswap-v3 up uniswap-watcher-db
    ```

  * Find the watcher database container's id using `docker ps` and export it for further usage:

    ```bash
    $ export CONTAINER_ID=<CONTAINER_ID>
    ```

  * Load watcher database dumps:

    ```bash
    # uni-watcher database
    $ docker exec -i $CONTAINER_ID psql -U vdbm uni-watcher < UNI_WATCHER_DB_DUMP_FILE_PATH.sql

    # uni-info-watcher database
    $ docker exec -i $CONTAINER_ID psql -U vdbm uni-info-watcher < UNI_INFO_WATCHER_DB_DUMP_FILE_PATH.sql
    ```

* Start all the watcher and info app services:

  ```bash
  $ laconic-so deploy-system --include watcher-uniswap-v3 up
  ```

* Check that all the services are up and healthy:

  ```bash
  $ docker ps
  ```

  * The `uni-info-watcher` GraphQL Playground can be accessed at `http://localhost:3004/graphql`
  * The frontend app can be accessed at `http://localhost:3006`

## Clean up

* To stop all the services running in background:

  ```bash
  $ laconic-so deploy-system --include watcher-uniswap-v3 down
  ```
