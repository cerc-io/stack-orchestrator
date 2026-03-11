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

The `deploy` command group manages persistent deployments. The general workflow is `deploy init` to generate a spec file, then `deploy create` to create a deployment directory from the spec, then runtime commands like `deployment start` and `deployment stop`.

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
- `--helm-chart`: generate Helm chart instead of deploying (k8s only)
- `--network-dir`: network configuration supplied in this directory
- `--initial-peers`: initial set of persistent peers

## deployment

Runtime commands for managing a created deployment. Use `--dir` to specify the deployment directory.

### deployment start

Start a deployment (`up` is a legacy alias):
```
$ laconic-so deployment --dir <deployment-dir> start
```

Options:
- `--stay-attached` / `--detatch-terminal`: attach to container stdout (default: detach)
- `--skip-cluster-management` / `--perform-cluster-management`: skip kind cluster creation/teardown (default: perform management). Only affects k8s-kind deployments. Use this when multiple stacks share a single cluster.

### deployment stop

Stop a deployment (`down` is a legacy alias):
```
$ laconic-so deployment --dir <deployment-dir> stop
```

Options:
- `--delete-volumes` / `--preserve-volumes`: delete data volumes on stop (default: preserve)
- `--skip-cluster-management` / `--perform-cluster-management`: skip kind cluster teardown (default: perform management). Use this to stop a single deployment without destroying a shared cluster.

### deployment restart

Restart a deployment with GitOps-aware workflow. Pulls latest stack code, syncs the deployment directory from the git-tracked spec, and restarts services:
```
$ laconic-so deployment --dir <deployment-dir> restart
```

See [deployment_patterns.md](deployment_patterns.md) for the recommended GitOps workflow.

### deployment ps

Show running services:
```
$ laconic-so deployment --dir <deployment-dir> ps
```

### deployment logs

View service logs:
```
$ laconic-so deployment --dir <deployment-dir> logs
```
Use `-f` to follow and `-n <count>` to tail.

### deployment exec

Execute a command in a running service container:
```
$ laconic-so deployment --dir <deployment-dir> exec <service-name> "<command>"
```

### deployment status

Show deployment status:
```
$ laconic-so deployment --dir <deployment-dir> status
```

### deployment port

Show mapped ports for a service:
```
$ laconic-so deployment --dir <deployment-dir> port <service-name> <port>
```

### deployment push-images

Push deployment images to a registry:
```
$ laconic-so deployment --dir <deployment-dir> push-images
```

### deployment run-job

Run a one-time job in the deployment:
```
$ laconic-so deployment --dir <deployment-dir> run-job <job-name>
```
