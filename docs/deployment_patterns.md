# Deployment Patterns

## GitOps Pattern

For production deployments, we recommend a GitOps approach where your deployment configuration is tracked in version control.

### Overview

- **spec.yml is your source of truth**: Maintain it in your operator repository
- **Don't regenerate on every restart**: Run `deploy init` once, then customize and commit
- **Use restart for updates**: The restart command respects your git-tracked spec.yml

### Workflow

1. **Initial setup**: Run `deploy init` once to generate a spec.yml template
2. **Customize and commit**: Edit spec.yml with your configuration (hostnames, resources, etc.) and commit to your operator repo
3. **Deploy from git**: Use the committed spec.yml for deployments
4. **Update via git**: Make changes in git, then restart to apply

```bash
# Initial setup (run once)
laconic-so --stack my-stack deploy init --output spec.yml

# Customize for your environment
vim spec.yml  # Set hostname, resources, etc.

# Commit to your operator repository
git add spec.yml
git commit -m "Add my-stack deployment configuration"
git push

# On deployment server: deploy from git-tracked spec
laconic-so deploy create \
  --spec-file /path/to/operator-repo/spec.yml \
  --deployment-dir my-deployment

laconic-so deployment --dir my-deployment start
```

### Updating Deployments

When you need to update a deployment:

```bash
# 1. Make changes in your operator repo
vim /path/to/operator-repo/spec.yml
git commit -am "Update configuration"
git push

# 2. On deployment server: pull and restart
cd /path/to/operator-repo && git pull
laconic-so deployment --dir my-deployment restart
```

The `restart` command:
- Pulls latest code from the stack repository
- Uses your git-tracked spec.yml (does NOT regenerate from defaults)
- Syncs the deployment directory
- Restarts services

### Anti-patterns

**Don't do this:**
```bash
# BAD: Regenerating spec on every deployment
laconic-so --stack my-stack deploy init --output spec.yml
laconic-so deploy create --spec-file spec.yml ...
```

This overwrites your customizations with defaults from the stack's `commands.py`.

**Do this instead:**
```bash
# GOOD: Use your git-tracked spec
git pull  # Get latest spec.yml from your operator repo
laconic-so deployment --dir my-deployment restart
```

## Private Registry Authentication

For deployments using images from private container registries (e.g., GitHub Container Registry), configure authentication in your spec.yml:

### Configuration

Add a `registry-credentials` section to your spec.yml:

```yaml
registry-credentials:
  server: ghcr.io
  username: your-org-or-username
  token-env: REGISTRY_TOKEN
```

**Fields:**
- `server`: The registry hostname (e.g., `ghcr.io`, `docker.io`, `gcr.io`)
- `username`: Registry username (for GHCR, use your GitHub username or org name)
- `token-env`: Name of the environment variable containing your API token/PAT

### Token Environment Variable

The `token-env` pattern keeps credentials out of version control. Set the environment variable when running `deployment start`:

```bash
export REGISTRY_TOKEN="your-personal-access-token"
laconic-so deployment --dir my-deployment start
```

For GHCR, create a Personal Access Token (PAT) with `read:packages` scope.

### Ansible Integration

When using Ansible for deployments, pass the token from a credentials file:

```yaml
- name: Start deployment
  ansible.builtin.command:
    cmd: laconic-so deployment --dir {{ deployment_dir }} start
  environment:
    REGISTRY_TOKEN: "{{ lookup('file', '~/.credentials/ghcr_token') }}"
```

### How It Works

1. laconic-so reads the `registry-credentials` config from spec.yml
2. Creates a Kubernetes `docker-registry` secret named `{deployment}-registry`
3. The deployment's pods reference this secret for image pulls

## Cluster and Volume Management

### Stopping Deployments

The `deployment stop` command has two important flags:

```bash
# Default: stops deployment, deletes cluster, PRESERVES volumes
laconic-so deployment --dir my-deployment stop

# Explicitly delete volumes (USE WITH CAUTION)
laconic-so deployment --dir my-deployment stop --delete-volumes
```

### Volume Persistence

Volumes persist across cluster deletion by design. This is important because:
- **Data survives cluster recreation**: Ledger data, databases, and other state are preserved
- **Faster recovery**: No need to re-sync or rebuild data after cluster issues
- **Safe cluster upgrades**: Delete and recreate cluster without data loss

**Only use `--delete-volumes` when:**
- You explicitly want to start fresh with no data
- The user specifically requests volume deletion
- You're cleaning up a test/dev environment completely

### Shared Cluster Architecture

In kind deployments, multiple stacks share a single cluster:
- First `deployment start` creates the cluster
- Subsequent deployments reuse the existing cluster
- `deployment stop` on ANY deployment deletes the shared cluster
- Other deployments will fail until cluster is recreated

To stop a single deployment without affecting the cluster:
```bash
laconic-so deployment --dir my-deployment stop --skip-cluster-management
```

## Volume Persistence in k8s-kind

k8s-kind has 3 storage layers:

- **Docker Host**: The physical server running Docker
- **Kind Node**: A Docker container simulating a k8s node
- **Pod Container**: Your workload

For k8s-kind, volumes with paths are mounted from Docker Host → Kind Node → Pod via extraMounts.

| spec.yml volume | Storage Location | Survives Pod Restart | Survives Cluster Restart |
|-----------------|------------------|---------------------|-------------------------|
| `vol:` (empty)  | Kind Node PVC    | ✅ | ❌ |
| `vol: ./data/x` | Docker Host      | ✅ | ✅ |
| `vol: /abs/path`| Docker Host      | ✅ | ✅ |

**Recommendation**: Always use paths for data you want to keep. Relative paths
(e.g., `./data/rpc-config`) resolve to `$DEPLOYMENT_DIR/data/rpc-config` on the
Docker Host.

### Example

```yaml
# In spec.yml
volumes:
  rpc-config: ./data/rpc-config  # Persists to $DEPLOYMENT_DIR/data/rpc-config
  chain-data: ./data/chain       # Persists to $DEPLOYMENT_DIR/data/chain
  temp-cache:                    # Empty = Kind Node PVC (lost on cluster delete)
```

### The Antipattern

Empty-path volumes appear persistent because they survive pod restarts (data lives
in Kind Node container). However, this data is lost when the kind cluster is
recreated. This "false persistence" has caused data loss when operators assumed
their data was safe.
