# Merkl SushiSwap v3 Watcher

## Setup

Clone required repositories:

```bash
laconic-so --stack merkl-sushiswap-v3 setup-repositories --git-ssh --pull
```

Build the container images:

```bash
laconic-so --stack merkl-sushiswap-v3 build-containers
```

## Deploy

### Configuration

Create and update an env file to be used in the next step:

  ```bash
  # External Filecoin (ETH RPC) endpoint to point the watcher
  CERC_ETH_RPC_ENDPOINT=
  ```

### Deploy the stack

```bash
laconic-so --stack merkl-sushiswap-v3 deploy --cluster merkl_sushiswap_v3 --env-file <PATH_TO_ENV_FILE> up
```

* To list down and monitor the running containers:

  ```bash
  laconic-so --stack merkl-sushiswap-v3 deploy --cluster merkl_sushiswap_v3 ps

  # With status
  docker ps -a

  # Check logs for a container
  docker logs -f <CONTAINER_ID>
  ```

* Open the GQL playground at http://localhost:3007/graphql

  ```graphql
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

Stop all the services running in background:

```bash
laconic-so --stack merkl-sushiswap-v3 deploy --cluster merkl_sushiswap_v3 down
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=merkl_sushiswap_v3"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=merkl_sushiswap_v3")
```
