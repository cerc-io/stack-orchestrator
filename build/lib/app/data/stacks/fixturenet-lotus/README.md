# Lotus Fixturenet

Instructions for deploying a local Lotus (Filecoin) chain for development and testing purposes using laconic-stack-orchestrator.

## 1. Clone required repositories
```
$ laconic-so --stack fixturenet-lotus setup-repositories
```
## 2. Build the stack's packages and containers
```
$ laconic-so --stack fixturenet-lotus build-containers
```
## 3. Deploy the stack
```
$ laconic-so --stack fixturenet-lotus deploy up
```
Correct operation should be verified by checking the container logs with:
```
$ laconic-so --stack fixturenet-lotus deploy logs lotus-miner
$ laconic-so --stack fixturenet-lotus deploy logs lotus-node-1
$ laconic-so --stack fixturenet-lotus deploy logs lotus-node-2
```
