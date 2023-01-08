# Laconicd Fixturenet

Instructions for deploying a local Laconic blockchain "fixturenet" for development and testing purposes using laconic-stack-orchestrator (the installation of which is covered [here](https://github.com/cerc-io/stack-orchestrator#user-mode)):

## Clone required repositories
```
$ laconic-so setup-repositories --include cerc-io/laconicd,cerc-io/laconic-sdk,cerc-io/laconic-cns-cli
```
## Build the laconicd container
```
$ laconic-so build-containers --include cerc/laconicd
```
This should create a container with tag `cerc/laconicd` in the local image registry.
## Deploy the stack
```
$ laconic-so deploy-system --include fixturenet-laconicd up
```
Correct operation should be verified by checking the laconicd container's log.
