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
laconic-so --stack my-stack deploy create \
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

Stacks sharing a cluster must agree on mount topology. See
[Volume Persistence in k8s-kind](#volume-persistence-in-k8s-kind).

### cluster-id vs deployment-id

Each deployment's `deployment.yml` carries two identifiers with
different roles:

- **`cluster-id`** — which kind cluster this deployment attaches to.
  Used for the kube-config context name (`kind-{cluster-id}`) and for
  kind lifecycle ops. Inherited from the running cluster at
  `deploy create` time when one exists; freshly generated otherwise.
  Shared across every deployment that joins the same cluster.
- **`deployment-id`** — this particular deployment's identity.
  Generated fresh on every `deploy create` and never inherited. Flows
  into `app_name`, the prefix on every k8s resource name this
  deployment creates (PVs, ConfigMaps, Deployments, PVCs, …). Distinct
  per deployment even when the cluster is shared.

The split prevents silent resource-name collisions between
deployments sharing a cluster: two deployments of the same stack,
or any two deployments that happen to declare a volume with the same
name, still produce distinct `{deployment-id}-{vol}` PV names.

**Backward compatibility**: `deployment.yml` files written before the
`deployment-id` field existed fall back to using `cluster-id` as the
deployment-id. Existing resource names stay stable across this
upgrade — no PV renames, no re-bind, no data orphaning. The next
`deploy create` writes both fields going forward.

**Namespace ownership**: on top of distinct resource names, SO stamps
the k8s namespace with a `laconic.com/deployment-dir` annotation on
first creation. A subsequent `deployment start` from a different
deployment directory that would land in the same namespace fails
with a `DeployerException` pointing at the `namespace:` spec
override. Catches operator-error cases where the same deployment dir
is effectively registered twice.

## Volume Persistence in k8s-kind

k8s-kind has 3 storage layers:

- **Docker Host**: The physical server running Docker
- **Kind Node**: A Docker container simulating a k8s node
- **Pod Container**: Your workload

Volumes with paths are mounted from Docker Host → Kind Node → Pod via kind
`extraMounts`. Kind applies `extraMounts` only at cluster creation — they
cannot be added to a running cluster.

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

### Shared Clusters: Use `kind-mount-root`

Because kind `extraMounts` can only be set at cluster creation, the first
deployment to start locks in the mount topology. Later deployments that
declare new `extraMounts` have them silently ignored — their PVs fall
through to the kind node's overlay filesystem and lose data on cluster
destroy.

The fix is an umbrella mount. Set `kind-mount-root` in the spec, pointing
at a host directory all stacks will share:

```yaml
# spec.yml
kind-mount-root: /srv/kind

volumes:
  my-data: /srv/kind/my-stack/data   # visible at /mnt/my-stack/data in-node
```

SO emits a single `extraMount` (`<kind-mount-root>` → `/mnt`). Any new
host subdirectory under the root is visible in the node immediately — no
cluster recreate needed to add stacks.

**All stacks sharing a cluster must agree on `kind-mount-root`** and keep
their host paths under it.

### Mount Compatibility Enforcement

`laconic-so deployment start` validates mount topology:

- **On first cluster creation** without an umbrella mount: prints a
  warning (future stacks may require a full recreate to add mounts).
- **On cluster reuse**: compares the new deployment's `extraMounts`
  against the live mounts on the control-plane container. Any mismatch
  (wrong host path, or mount missing) fails the deploy.

### Static files in compose volumes → auto-ConfigMap

Compose volumes that bind a host file or flat directory into a container
(e.g. `../config/test/script.sh:/opt/run.sh`) are used to inject static
content that ships with the stack. k8s doesn't have a native notion of
this — the canonical way to inject static content is a ConfigMap.

At `deploy start`, laconic-so auto-generates a namespace-scoped
ConfigMap per host-path compose volume (deduped by source) and mounts
it into the pod instead of routing the bind through the kind node:

| Source shape | Behavior |
|---|---|
| Single file | ConfigMap with one key (the filename); pod mount uses `subPath` so the single key lands at the compose target path |
| Flat directory (no subdirs, ≤ ~700 KiB) | ConfigMap with one key per file; pod mount exposes all keys at the target path |
| Directory with subdirs, or over budget | Rejected at `deploy create` — embed in the container image, split into multiple ConfigMaps, or use an initContainer |
| `:rw` on any host-path bind | Rejected at `deploy create` — use a named volume with a spec-configured host path for writable data |

The deployment dir layout is unchanged: compose files stay verbatim and
`spec.yml` is not rewritten. Source files remain under
`{deployment_dir}/config/{pod}/` (as copied by `deploy create`); the
ConfigMap is built from them at deploy start and no kind extraMount is
emitted for these paths.

This works identically on kind and real k8s (ConfigMaps are
cluster-native; no node-side landing pad required), and two deployments
of the same stack sharing a cluster get their own per-namespace
ConfigMaps — no aliasing.

### Writable / generated data → named volume + host path

For volumes the workload *writes to* (databases, ledgers, caches, logs),
use a named volume backed by a spec-configured host path under
`kind-mount-root`:

```yaml
# compose
volumes:
  - my-data:/var/lib/foo

# spec.yml
kind-mount-root: /srv/kind
volumes:
  my-data: /srv/kind/my-stack/data
```

Works on both kind (via the umbrella mount) and real k8s (operator
provisions `/srv/kind/my-stack/data` on each node).

### Migrating an Existing Cluster

If a cluster was created without an umbrella mount and you need to add a
stack that requires new host-path mounts, the cluster must be recreated:

1. Back up ephemeral state (DBs, caches) from PVs that lack host mounts —
   these are in the kind node overlay FS and do not survive `kind delete`.
2. Update every stack's spec to set a shared `kind-mount-root` and place
   host paths under it.
3. Stop all deployments, destroy the cluster, recreate it by starting any
   stack (umbrella now active), and restore state.
