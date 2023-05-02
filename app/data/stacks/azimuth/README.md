# Azimuth Watcher

Instructions to setup and deploy Azimuth Watcher stack

## Setup

Clone required repositories:

```bash
laconic-so --stack azimuth setup-repositories
```

NOTE: If the repository already exists and checked out to different versions, `setup-repositories` command will throw an error.
For getting around this, the `azimuth-watcher-ts` repository can be removed and then run the command.

Checkout to the required versions and branches in repos

```bash
# azimuth-watcher-ts
cd ~/cerc/azimuth-watcher-ts
# git checkout v0.1.0
```

Build the container images:

```bash
laconic-so --stack azimuth build-containers
```

This should create the required docker images in the local image registry.

Deploy the stack:

* Deploy the containers:

  ```bash
  laconic-so --stack azimuth deploy-system up
  ```

* List and check the health status of all the containers using `docker ps` and wait for them to be `healthy`

## Clean up

Stop all the services running in background run:

```bash
laconic-so --stack azimuth deploy-system down 30
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=.*watcher_db_data"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=.*watcher_db_data")
```
