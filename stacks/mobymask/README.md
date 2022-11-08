# Mobymask

## Set up a Mobymask Watcher

## Clone required repositories
```
$ laconic-so setup-repositories
```
Checkout required branches:
```
$ cd ~/cerc/assemblyscript
$ git checkout ng-integrate-asyncify
$ cd ~/cerc/watcher-ts
$ git checkout v0.2.13
```
## Build the watcher container
```
$ laconic-sh build-containers --include cerc/watcher-mobymask
```
## Deploy the stack
```
$ laconic-so deploy-system --include watcher-mobymask up watcher-db
$ docker exec -i <watcher-db-container> psql -U vdbm mobymask-watcher < config/watcher-mobymask/mobymask-watcher-db.sql
$ laconic-sh deploy-system --include watcher-mobymask
```