# Gaia Fixturenet

Instructions for deploying a local single node Gaia "fixturenet" for development and testing purposes using laconic-stack-orchestrator.

## 1. Build Laconic Stack Orchestrator
Build this fork of Laconic Stack Orchestrator which includes the fixturenet-gaia stack:
```
$ scripts/build_shiv_package.sh
$ cd package
$ mv laconic-so-{version} /usr/local/bin/laconic-so  # Or move laconic-so to ~/bin or your favorite on-path directory
```

## 2. Clone required repositories
```
$ laconic-so --stack fixturenet-gaia setup-repositories
```
## 3. Build the stack's container
```
$ laconic-so --stack fixturenet-gaia build-containers
```
## 4. Deploy the stack
```
$ laconic-so --stack fixturenet-gaia deploy up
```
Correct operation should be verified by checking the gaiad container's logs with:
```
$ laconic-so --stack fixturenet-gaia deploy logs
```
## 5. Display key/address
```
$ laconic-so --stack fixturenet-gaia deploy exec gaiad "gaiad keys list"
```
## 6. Shutdown and cleanup
```
$ laconic-so --stack fixturenet-gaia deploy down
```
