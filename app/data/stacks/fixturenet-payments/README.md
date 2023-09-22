# fixturenet-payments

## Setup

Clone required repositories:

```bash
laconic-so --stack fixturenet-payments setup-repositories --pull
```

Build the container images:

```bash
laconic-so --stack fixturenet-payments build-containers
```

## Deploy

Deploy the stack:

```bash
laconic-so --stack fixturenet-payments deploy --cluster [CLUSTER_NAME] up
```

## Clean up

Stop all the services running in background:

```bash
laconic-so --stack fixturenet-payments deploy --cluster [CLUSTER_NAME] down 30
```

Clear volumes created by this stack:

```bash
# List all relevant volumes
docker volume ls -q --filter "name=[CLUSTER_NAME]"

# Remove all the listed volumes
docker volume rm $(docker volume ls -q --filter "name=[CLUSTER_NAME]")
```
