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
