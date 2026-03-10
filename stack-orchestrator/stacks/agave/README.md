# agave stack

Unified Agave/Jito Solana stack supporting three modes:

| Mode | Compose file | Use case |
|------|-------------|----------|
| `test` | `docker-compose-agave-test.yml` | Local dev with instant finality |
| `rpc` | `docker-compose-agave-rpc.yml` | Non-voting mainnet/testnet RPC node |
| `validator` | `docker-compose-agave.yml` | Voting validator |

## Build

```bash
# Vanilla Agave v3.1.9
laconic-so --stack agave build-containers

# Jito v3.1.8
AGAVE_REPO=https://github.com/jito-foundation/jito-solana.git \
AGAVE_VERSION=v3.1.8-jito \
laconic-so --stack agave build-containers
```

Build compiles from source (~30-60 min on first build).

## Deploy

```bash
# Test validator (dev)
laconic-so --stack agave deploy init --output spec.yml
laconic-so --stack agave deploy create --spec-file spec.yml --deployment-dir my-test
laconic-so deployment --dir my-test start

# Mainnet RPC (e.g. biscayne)
# Edit spec.yml to set AGAVE_MODE=rpc, VALIDATOR_ENTRYPOINT, KNOWN_VALIDATOR, etc.
laconic-so --stack agave deploy init --output spec.yml
laconic-so --stack agave deploy create --spec-file spec.yml --deployment-dir my-rpc
laconic-so deployment --dir my-rpc start
```

## Configuration

Mode is selected via `AGAVE_MODE` environment variable (`test`, `rpc`, or `validator`).

### RPC mode required env
- `VALIDATOR_ENTRYPOINT` - cluster entrypoint (e.g. `entrypoint.mainnet-beta.solana.com:8001`)
- `KNOWN_VALIDATOR` - known validator pubkey

### Validator mode required env
- `VALIDATOR_ENTRYPOINT` - cluster entrypoint
- `KNOWN_VALIDATOR` - known validator pubkey
- Identity and vote account keypairs mounted at `/data/config/`

### Jito (optional, any mode except test)
Set `JITO_ENABLE=true` and provide:
- `JITO_BLOCK_ENGINE_URL`
- `JITO_SHRED_RECEIVER_ADDR`
- `JITO_TIP_PAYMENT_PROGRAM`
- `JITO_DISTRIBUTION_PROGRAM`
- `JITO_MERKLE_ROOT_AUTHORITY`
- `JITO_COMMISSION_BPS`

Image must be built from `jito-foundation/jito-solana` repo for Jito flags to work.

## Runtime requirements

The container requires the following (already set in compose files):

- `privileged: true` — allows `mlock()` and raw network access
- `cap_add: IPC_LOCK` — memory page locking for account indexes and ledger mappings
- `ulimits: memlock: -1` (unlimited) — Agave locks gigabytes of memory
- `ulimits: nofile: 1000000` — gossip/TPU connections + memory-mapped ledger files
- `network_mode: host` — direct host network stack for gossip, TPU, and UDP port ranges

Without these, Agave either refuses to start or dies under load.

## Container overhead

Containers running with `privileged: true` and `network_mode: host` add **zero
measurable overhead** compared to bare metal. Linux containers are not VMs — there
is no hypervisor, no emulation layer, no packet translation:

- **Network**: `network_mode: host` shares the host's network namespace directly.
  No virtual bridge, no NAT, no veth pair. Same kernel code path as bare metal.
  GRE tunnels (DoubleZero) and raw sockets work identically.
- **CPU**: No hypervisor. The process runs on the same physical cores with the
  same scheduler priority as any host process.
- **Memory**: `IPC_LOCK` + unlimited memlock means Agave can `mlock()` pages
  exactly like bare metal. No memory ballooning or overcommit.
- **Disk I/O**: PersistentVolumes backed by hostPath mounts have identical I/O
  characteristics to direct filesystem access.

The only overhead is cgroup accounting (nanoseconds per syscall) and overlayfs
for cold file opens (single-digit microseconds, zero once cached).

## DoubleZero

DoubleZero provides optimized network routing for Solana validators via GRE
tunnels (IP protocol 47) and BGP (TCP/179) over link-local 169.254.0.0/16.
Traffic to other DoubleZero participants is routed through private fiber
instead of the public internet.

### How it works

`doublezerod` creates a `doublezero0` GRE tunnel interface and runs BGP
peering through it. Routes are injected into the host routing table, so
the validator transparently sends traffic to other DZ validators over
the fiber backbone. IBRL mode falls back to public internet if DZ is down.

### Container build

```bash
laconic-so --stack agave build-containers
```

This builds both the `laconicnetwork/agave` and `laconicnetwork/doublezero` images.

### Requirements

- Validator identity keypair at `/data/config/validator-identity.json`
- `privileged: true` + `NET_ADMIN` (GRE tunnel + route table manipulation)
- `hostNetwork: true` (GRE uses IP protocol 47, not TCP/UDP — cannot be port-mapped)
- Node registered with DoubleZero passport system

### Docker Compose

The `docker-compose-doublezero.yml` runs alongside the validator with
`network_mode: host`, sharing the `validator-config` volume for identity access.

### k8s deployment

laconic-so does not pass `hostNetwork` through to generated k8s resources.
DoubleZero runs as a DaemonSet defined in `deployment/k8s-manifests/doublezero-daemonset.yaml`,
applied after `deployment start`:

```bash
kubectl apply -f deployment/k8s-manifests/doublezero-daemonset.yaml
```

Since validator pods also use `hostNetwork: true` (via the compose `network_mode: host`
which maps to the pod spec in k8s), they automatically see the GRE routes
injected by `doublezerod` into the node's routing table.

## Biscayne deployment (biscayne.vaasl.io)

Mainnet voting validator with Jito MEV and DoubleZero.

```bash
# Build Jito image
AGAVE_REPO=https://github.com/jito-foundation/jito-solana.git \
AGAVE_VERSION=v3.1.8-jito \
laconic-so --stack agave build-containers

# Create deployment from biscayne spec
laconic-so --stack agave deploy create \
  --spec-file deployment/spec.yml \
  --deployment-dir biscayne-deployment

# Copy validator keypairs
cp /path/to/validator-identity.json biscayne-deployment/data/validator-config/
cp /path/to/vote-account-keypair.json biscayne-deployment/data/validator-config/

# Start validator
laconic-so deployment --dir biscayne-deployment start

# Start DoubleZero (after deployment is running)
kubectl apply -f deployment/k8s-manifests/doublezero-daemonset.yaml
```

To run as non-voting RPC instead, change `AGAVE_MODE: rpc` in `deployment/spec.yml`.
