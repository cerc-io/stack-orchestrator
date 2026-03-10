# Ajna Watcher

## Setup

Clone required repositories:

```bash
laconic-so --stack ajna setup-repositories --git-ssh --pull
```

Build the container images:

```bash
laconic-so --stack ajna build-containers
```

## Deploy

Create a spec file for the deployment:

```bash
laconic-so --stack ajna deploy init --output ajna-spec.yml
```

### Ports

Edit `network` in the spec file to map container ports to host ports as required:

```yml
...
network:
  ports:
    ajna-watcher-db:
     - 15432:5432
    ajna-watcher-job-runner:
     - 9000:9000
    ajna-watcher-server:
     - 3008:3008
     - 9001:9001
```

### Create a deployment

Create a deployment from the spec file:

```bash
laconic-so --stack ajna deploy create --spec-file ajna-spec.yml --deployment-dir ajna-deployment
```

### Configuration

Inside deployment directory, open the `config.env` file  and set following env variables:

```bash
# External Filecoin (ETH RPC) endpoint to point the watcher to
CERC_ETH_RPC_ENDPOINTS=https://example-lotus-endpoint-1/rpc/v1,https://example-lotus-endpoint-2/rpc/v1
```

### Start the deployment

```bash
laconic-so deployment --dir ajna-deployment start
```

* To list down and monitor the running containers:

  ```bash
  # With status
  docker ps -a

  # Check logs for a container
  docker logs -f <CONTAINER_ID>
  ```

* Open the GQL playground at <http://localhost:3008/graphql>

  ```graphql
  # Example query
  query {
    _meta {
      block {
        hash
        number
        timestamp
      }
      deployment
      hasIndexingErrors
    }

    accounts {
      id
      txCount
      tokensDelegated
      rewardsClaimed
    }
  }
  ```

## Clean up

Stop all the ajna services running in background:

```bash
# Only stop the docker containers
laconic-so deployment --dir ajna-deployment stop

# Run 'start' to restart the deployment
```

To stop all the ajna services and also delete data:

```bash
# Stop the docker containers
laconic-so deployment --dir ajna-deployment stop --delete-volumes

# Remove deployment directory (deployment will have to be recreated for a re-run)
rm -r ajna-deployment
```
