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
## build-npms

Build a single package:
```
$ laconic-so build-npms --include <package-name>
```
e.g.
```
$ laconic-so build-npms --include laconic-sdk
```
Build the packages for a stack:
```
$ laconic-so --stack <stack-name> build-npms
```
e.g.
```
$ laconic-so --stack fixturenet-laconicd build-npms
```
Force full rebuild of packages:
```
$ laconic-so build-npms --include <package-name> --force-rebuild
```
