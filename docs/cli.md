# laconic-so

Sub-commands and flags

## setup-repositories

Clone a single repository:
```
$ laconic-so setup-repositories --include github.com/cerc-io/go-ethereum
```
Clone the repositories for a stack:
```
$ laconic-so --stack fixturenet-eth setup-repositories
```
Pull latest commits from origin:
```
$ laconic-so --stack fixturenet-eth setup-repositories --pull
```
Use SSH rather than https:
```
$ laconic-so --stack fixturenet-eth setup-repositories --git-ssh
```

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
$ laconic-so build-npms --include registry-sdk
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

## deploy

The `deploy` command group manages persistent deployments. The general workflow is `deploy init` to generate a spec file, then `deploy create` to create a deployment directory from the spec, then runtime commands like `deploy up` and `deploy down`.

### deploy init

Generate a deployment spec file from a stack definition:
```
$ laconic-so --stack <stack-name> deploy init --output <spec-file>
```

Options:
- `--output` (required): write spec file here
- `--config`: provide config variables for the deployment
- `--config-file`: provide config variables in a file
- `--kube-config`: provide a config file for a k8s deployment
- `--image-registry`: provide a container image registry url for this k8s cluster
- `--map-ports-to-host`: map ports to the host (`any-variable-random`, `localhost-same`, `any-same`, `localhost-fixed-random`, `any-fixed-random`)

### deploy create

Create a deployment directory from a spec file:
```
$ laconic-so --stack <stack-name> deploy create --spec-file <spec-file> --deployment-dir <dir>
```

Update an existing deployment in-place (preserving data volumes and env file):
```
$ laconic-so --stack <stack-name> deploy create --spec-file <spec-file> --deployment-dir <dir> --update
```

Options:
- `--spec-file` (required): spec file to use
- `--deployment-dir`: target directory for deployment files
- `--update`: update an existing deployment directory, preserving data volumes and env file. Changed files are backed up with a `.bak` suffix. The deployment's `config.env` and `deployment.yml` are also preserved.
- `--network-dir`: network configuration supplied in this directory
- `--initial-peers`: initial set of persistent peers

### deploy up

Start a deployment:
```
$ laconic-so deployment --dir <deployment-dir> up
```

### deploy down

Stop a deployment:
```
$ laconic-so deployment --dir <deployment-dir> down
```
Use `--delete-volumes` to also remove data volumes.

### deploy ps

Show running services:
```
$ laconic-so deployment --dir <deployment-dir> ps
```

### deploy logs

View service logs:
```
$ laconic-so deployment --dir <deployment-dir> logs
```
Use `-f` to follow and `-n <count>` to tail.
