# fixturenet-optimism

Instructions to setup and deploy an end-to-end L1+L2 stack with [fixturenet-eth](../fixturenet-eth/) (L1) and Optimism (L2)

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

# Deploy

Deploy the stack:

```bash
laconic-so --stack fixturenet-optimism deploy up
```

## Clean up

Stop all services running in the background:

```bash
laconic-so --stack fixturenet-optimism deploy down
$ laconic-so --stack fixturenet-optimism deploy up
```
