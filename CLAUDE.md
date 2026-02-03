# CLAUDE.md

This file provides guidance to Claude Code when working with the stack-orchestrator project.

## Some rules to follow
NEVER speculate about the cause of something
NEVER assume your hypotheses are true without evidence

ALWAYS clearly state when something is a hypothesis
ALWAYS use evidence from the systems your interacting with to support your claims and hypotheses
ALWAYS run `pre-commit run --all-files` before committing changes

## Key Principles

### Development Guidelines
- **Single responsibility** - Each component has one clear purpose
- **Fail fast** - Let errors propagate, don't hide failures
- **DRY/KISS** - Minimize duplication and complexity

## Development Philosophy: Conversational Literate Programming

### Approach
This project follows principles inspired by literate programming, where development happens through explanatory conversation rather than code-first implementation.

### Core Principles
- **Documentation-First**: All changes begin with discussion of intent and reasoning
- **Narrative-Driven**: Complex systems are explained through conversational exploration
- **Justification Required**: Every coding task must have a corresponding TODO.md item explaining the "why"
- **Iterative Understanding**: Architecture and implementation evolve through dialogue

### Working Method
1. **Explore and Understand**: Read existing code to understand current state
2. **Discuss Architecture**: Workshop complex design decisions through conversation
3. **Document Intent**: Update TODO.md with clear justification before coding
4. **Explain Changes**: Each modification includes reasoning and context
5. **Maintain Narrative**: Conversations serve as living documentation of design evolution

### Implementation Guidelines
- Treat conversations as primary documentation
- Explain architectural decisions before implementing
- Use TODO.md as the "literate document" that justifies all work
- Maintain clear narrative threads across sessions
- Workshop complex ideas before coding

This approach treats the human-AI collaboration as a form of **conversational literate programming** where understanding emerges through dialogue before code implementation.

## External Stacks Preferred

When creating new stacks for any reason, **use the external stack pattern** rather than adding stacks directly to this repository.

External stacks follow this structure:

```
my-stack/
└── stack-orchestrator/
    ├── stacks/
    │   └── my-stack/
    │       ├── stack.yml
    │       └── README.md
    ├── compose/
    │   └── docker-compose-my-stack.yml
    └── config/
        └── my-stack/
            └── (config files)
```

### Usage

```bash
# Fetch external stack
laconic-so fetch-stack github.com/org/my-stack

# Use external stack
STACK_PATH=~/cerc/my-stack/stack-orchestrator/stacks/my-stack
laconic-so --stack $STACK_PATH deploy init --output spec.yml
laconic-so --stack $STACK_PATH deploy create --spec-file spec.yml --deployment-dir deployment
laconic-so deployment --dir deployment start
```

### Examples

- `zenith-karma-stack` - Karma watcher deployment
- `urbit-stack` - Fake Urbit ship for testing
- `zenith-desk-stack` - Desk deployment stack

## Architecture: k8s-kind Deployments

### One Cluster Per Host
One Kind cluster per host by design. Never request or expect separate clusters.

- `create_cluster()` in `helpers.py` reuses any existing cluster
- `cluster-id` in deployment.yml is an identifier, not a cluster request
- All deployments share: ingress controller, etcd, certificates

### Stack Resolution
- External stacks detected via `Path(stack).exists()` in `util.py`
- Config/compose resolution: external path first, then internal fallback
- External path structure: `stack_orchestrator/data/stacks/<name>/stack.yml`

### Secret Generation Implementation
- `GENERATE_TOKEN_PATTERN` in `deployment_create.py` matches `$generate:type:length$`
- `_generate_and_store_secrets()` creates K8s Secret
- `cluster_info.py` adds `envFrom` with `secretRef` to containers
- Non-secret config written to `config.env`

### Repository Cloning
`setup-repositories --git-ssh` clones repos defined in stack.yml's `repos:` field. Requires SSH agent.

### Key Files (for codebase navigation)
- `repos/setup_repositories.py`: `setup-repositories` command (git clone)
- `deployment_create.py`: `deploy create` command, secret generation
- `deployment.py`: `deployment start/stop/restart` commands
- `deploy_k8s.py`: K8s deployer, cluster management calls
- `helpers.py`: `create_cluster()`, etcd cleanup, kind operations
- `cluster_info.py`: K8s resource generation (Deployment, Service, Ingress)

## Insights and Observations

### Design Principles
- **When something times out that doesn't mean it needs a longer timeout it means something that was expected never happened, not that we need to wait longer for it.**
- **NEVER change a timeout because you believe something truncated, you don't understand timeouts, don't edit them unless told to explicitly by user.**
