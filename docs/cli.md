# laconic-so

Sub-commands and flags

## build-containers

Build a single container:
```
$ laconic-so build-containers --include <container-name>
```
e.g.
```
$ laconic-so build-containers --include cerc/go-ethereum
```
Build the containers for a stack:
```
$ laconic-so --stack <stack-name> build-containers
```
e.g.
```
$ laconic-so --stack fixturenet-eth build-containers
```
Force full rebuild of container images:
```
$ laconic-so build-containers --include <container-name> --force-rebuild
```
