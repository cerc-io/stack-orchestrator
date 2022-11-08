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
$ laconic-sh deploy-system --include watcher-mobymask
```