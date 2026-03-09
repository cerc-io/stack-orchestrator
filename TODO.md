# TODO

## Features Needed

### Update Stack Command
We need an "update stack" command in stack orchestrator and cleaner documentation regarding how to do continuous deployment with and without payments.

**Context**: Currently, `deploy init` generates a spec file and `deploy create` creates a deployment directory. The `deployment update` command (added by Thomas Lackey) only syncs env vars and restarts - it doesn't regenerate configurations. There's a gap in the workflow for updating stack configurations after initial deployment.

## Bugs

### `deploy create` doesn't auto-generate volume mappings for new pods

When a new pod is added to `stack.yml` (e.g. `monitoring`), `deploy create`
does not generate default host path mappings in spec.yml for the new pod's
volumes. The deployment then fails at scheduling because the PVCs don't exist.

**Expected**: `deploy create` enumerates all volumes from all compose files
in the stack and generates default host paths for any that aren't already
mapped in the spec.yml `volumes:` section.

**Actual**: Only volumes already in spec.yml get PVs. New volumes are silently
missing, causing `FailedScheduling: persistentvolumeclaim not found`.

**Workaround**: Manually add volume entries to spec.yml and create host dirs.

**Files**: `deployment_create.py` (`_write_config_file`, volume handling)

## Architecture Refactoring

### Separate Deployer from Stack Orchestrator CLI
The deployer logic should be decoupled from the CLI tool to allow independent development and reuse.

### Separate Stacks from Stack Orchestrator Repo
Stacks should live in their own repositories, not bundled with the orchestrator tool. This allows stacks to evolve independently and be maintained by different teams.
