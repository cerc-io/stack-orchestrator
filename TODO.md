# TODO

## Features Needed

### Update Stack Command
We need an "update stack" command in stack orchestrator and cleaner documentation regarding how to do continuous deployment with and without payments.

**Context**: Currently, `deploy init` generates a spec file and `deploy create` creates a deployment directory. The `deployment update` command (added by Thomas Lackey) only syncs env vars and restarts - it doesn't regenerate configurations. There's a gap in the workflow for updating stack configurations after initial deployment.

## Architecture Refactoring

### Separate Deployer from Stack Orchestrator CLI
The deployer logic should be decoupled from the CLI tool to allow independent development and reuse.

### Separate Stacks from Stack Orchestrator Repo
Stacks should live in their own repositories, not bundled with the orchestrator tool. This allows stacks to evolve independently and be maintained by different teams.
