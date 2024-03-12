# SushiSwap v3 Watcher

## Setup

Clone required repositories:

```bash
laconic-so --stack sushiswap-v3 setup-repositories --git-ssh --pull
```

Build the container images:

```bash
laconic-so --stack sushiswap-v3 build-containers
```

## Deploy

Create a spec file for the deployment:

```bash
laconic-so --stack sushiswap-v3 deploy init --output sushiswap-v3-spec.yml
```

### Ports

Edit `network` in the spec file to map container ports to host ports as required:

```
...
network:
  ports:
    sushiswap-v3-watcher-db:
     - '5432'
    sushiswap-v3-watcher-job-runner:
     - 9000:9000
    sushiswap-v3-watcher-server:
     - 127.0.0.1:3008:3008
     - 9001:9001
```

### Create a deployment

Create a deployment from the spec file:

```bash
laconic-so --stack sushiswap-v3 deploy create --spec-file sushiswap-v3-spec.yml --deployment-dir sushiswap-v3-deployment
```

### Configuration

Inside deployment directory, open the `config.env` file  and set following env variables:

```bash
# External Filecoin (ETH RPC) endpoint to point the watcher to
CERC_ETH_RPC_ENDPOINT=https://example-lotus-endpoint/rpc/v1
```

### Start the deployment

```bash
laconic-so deployment --dir sushiswap-v3-deployment start
```

* To list down and monitor the running containers:

  ```bash
  # With status
  docker ps -a

  # Check logs for a container
  docker logs -f <CONTAINER_ID>
  ```

* Open the GQL playground at http://localhost:3008/graphql

  ```graphql
  # Example query
  {
    _meta {
      block {
        number
        timestamp
      }
      hasIndexingErrors
    }

    factories {
      id
      poolCount
    }
  }
  ```

## Clean up

Stop all the sushiswap-v3 services running in background:

```bash
# Only stop the docker containers
laconic-so deployment --dir sushiswap-v3-deployment stop

# Run 'start' to restart the deployment
```

To stop all the sushiswap-v3 services and also delete data:

```bash
# Stop the docker containers
laconic-so deployment --dir sushiswap-v3-deployment stop --delete-volumes

# Remove deployment directory (deployment will have to be recreated for a re-run)
rm -r sushiswap-v3-deployment
```
