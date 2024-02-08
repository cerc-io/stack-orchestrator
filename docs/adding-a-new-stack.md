# Adding a new stack

See [this PR](https://git.vdb.to/cerc-io/stack-orchestrator/pull/434) for an example of how to currently add a minimal stack to stack orchestrator. The [reth stack](https://git.vdb.to/cerc-io/stack-orchestrator/pull/435) is another good example.

For external developers, we recommend forking this repo and adding your stack directly to your fork. This initially requires running in "developer mode" as described [here](/docs/CONTRIBUTING.md). Check out the [Namada stack](https://github.com/vknowable/stack-orchestrator/blob/main/app/data/stacks/public-namada/digitalocean_quickstart.md) from Knowable to see how that is done.

Core to the feature completeness of stack orchestrator is to [decouple the tool functionality from payload](https://git.vdb.to/cerc-io/stack-orchestrator/issues/315) which will no longer require forking to add a stack.

## Example

- in `stack_orchestrator/data/stacks/my-new-stack/stack.yml` add:

```yaml
version: "0.1"
name: my-new-stack
repos:
  - github.com/my-org/my-new-stack
containers:
  - cerc/my-new-stack
pods:
  - my-new-stack
```

- in `stack_orchestrator/data/container-build/cerc-my-new-stack/build.sh` add:

```yaml
#!/usr/bin/env bash
# Build the my-new-stack image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/my-new-stack:local -f ${CERC_REPO_BASE_DIR}/my-new-stack/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/my-new-stack
```

- in `stack_orchestrator/data/compose/docker-compose-my-new-stack.yml` add:

```yaml
version: "3.2"

services:
  my-new-stack:
    image: cerc/my-new-stack:local
    restart: always
    ports:
      - "0.0.0.0:3000:3000"
```

- in `stack_orchestrator/data/repository-list.txt` add:

```bash
github.com/my-org/my-new-stack
```
whereby that repository contains your source code and a `Dockerfile`, and matches the `repos:` field in the `stack.yml`.

- in `stack_orchestrator/data/container-image-list.txt` add:

```bash
cerc/my-new-stack
```

- in `stack_orchestrator/data/pod-list.txt` add:

```bash
my-new-stack
```

Now, the following commands will fetch, build, and deploy you app:

```bash
laconic-so --stack my-new-stack setup-repositories
laconic-so --stack my-new-stack build-containers
laconic-so --stack my-new-stack deploy-system up
```
