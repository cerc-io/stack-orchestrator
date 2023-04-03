# fixturenet-optimism

Instructions to setup and deploy an end-to-end L1+L2 stack with [fixturenet-eth](../fixturenet-eth/) (L1) and [Optimism](https://stack.optimism.io) (L2)

## Setup

Clone required repositories:

```bash
laconic-so --stack fixturenet-optimism setup-repositories
```

Checkout to the required versions and branches in repos:

```bash
# optimism
cd ~/cerc/optimism
git checkout @eth-optimism/sdk@0.0.0-20230329025055
```

Build the container images:

```bash
laconic-so --stack fixturenet-optimism build-containers
```

This should create the required docker images in the local image registry:
* `cerc/go-ethereum`
* `cerc/lighthouse`
* `cerc/fixturenet-eth-geth`
* `cerc/fixturenet-eth-lighthouse`
* `cerc/foundry`
* `cerc/optimism-contracts`
* `cerc/optimism-l2geth`
* `cerc/optimism-op-batcher`
* `cerc/optimism-op-node`

## Deploy

Deploy the stack:

```bash
laconic-so --stack fixturenet-optimism deploy up
```

To list down the running containers:

```bash
laconic-so --stack fixturenet-optimism deploy ps

# With status
docker ps
```

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack fixturenet-optimism deploy down
```

Remove volumes created by this stack:

```bash
docker volume ls

docker volume rm laconic-d527651bba3cb61886b36a7400bd2a38_fixturenet-geth-accounts
docker volume rm laconic-d527651bba3cb61886b36a7400bd2a38_l1-deployment
docker volume rm laconic-d527651bba3cb61886b36a7400bd2a38_l2-accounts
docker volume rm laconic-d527651bba3cb61886b36a7400bd2a38_op_node_data
```

## Known Issues

* Currently not supported:
  * Stopping and restarting the stack from where it left off; currently starts fresh on a restart
  * Pointing Optimism (L2) to external L1 endpoint to allow running only L2 services
* Resource requirements (memory + time) for building `cerc/foundry` image are on the higher side
  * `cerc/optimism-contracts` image is currently based on `cerc/foundry` (Optimism requires foundry installation)
