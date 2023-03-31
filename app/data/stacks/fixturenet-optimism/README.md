# fixturenet-optimism

Experimental Optimism Fixturenet

## Setup

Clone required repositories:

```bash
$ laconic-so --stack fixturenet-optimism setup-repositories
```

Checkout to the required versions and branches in repos:

```bash
# optimism
cd ~/cerc/optimism
git checkout @eth-optimism/sdk@0.0.0-20230329025055
```

Build the container images:

```bash
$ laconic-so --stack fixturenet-optimism build-containers
```

This should create the required docker images in the local image registry:
* cerc/go-ethereum
* cerc/lighthouse
* cerc/fixturenet-eth-geth
* cerc/fixturenet-eth-lighthouse
* cerc/optimism-l2geth
* cerc/optimism-op-batcher
* cerc/optimism-op-node
* cerc/optimism-contracts

# Deploy

Deploy the stack:

```bash
$ laconic-so --stack fixturenet-optimism deploy up
```
