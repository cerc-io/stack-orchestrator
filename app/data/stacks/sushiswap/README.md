# SushiSwap

## Setup

Clone required repositories:

```bash
laconic-so --stack sushiswap setup-repositories

# If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the conflicting repositories and re-run the command
```

Build the container images:

```bash
laconic-so --stack sushiswap build-containers
```

## Deploy

Deploy the stack:

```bash
laconic-so --stack sushiswap deploy --cluster lotus up
```
