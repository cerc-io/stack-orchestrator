# Laconicd Fixturenet

Instructions for deploying a local Laconic blockchain "fixturenet" for development and testing purposes using laconic-stack-orchestrator (the installation of which is covered [here](https://github.com/cerc-io/stack-orchestrator#install)):

## Clone required repositories
```
$ laconic-so setup-repositories --include cerc-io/laconicd,cerc-io/laconic-sdk,cerc-io/laconic-cns-cli
```
## Build the laconicd container
```
$ laconic-sh build-containers --include cerc/laconicd
```
This should create a container with tag `cerc/watcher-mobymask` in the local image registry.
## Deploy the stack
First the watcher database has to be initialized. Start only the watcher-db service:
```
$ laconic-so deploy-system --include fixturenet-laconicd
```
Correct operation should be verified by checking the laconicd container's log.
