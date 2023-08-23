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
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus up
```

Note: When running for the first time (or after clean up), the services will take some time to start properly as the Lotus nodes download the proof params (which are persisted to volumes)

Correct operation should be verified by checking the container logs with:
```
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus logs lotus-miner-1
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus logs lotus-miner-2
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus logs lotus-miner-3
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus logs lotus-node-1
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus logs lotus-node-2
```
or by checking the chain status on each node:
```
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus exec lotus-miner-1 "lotus status"
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus exec lotus-miner-2 "lotus status"
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus exec lotus-miner-3 "lotus status"
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus exec lotus-node-1 "lotus status"
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus exec lotus-node-2 "lotus status"
```

## 4. Clean up

Stop all the services running in background:
```
$ laconic-so --stack fixturenet-lotus deploy --cluster lotus down
```

Clear volumes created by this stack:
```
# List all relevant volumes
$ docker volume ls -q --filter "name=lotus"

# Remove all the listed volumes
$ docker volume rm $(docker volume ls -q --filter "name=lotus")
```
