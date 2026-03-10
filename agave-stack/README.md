# agave-stack

Unified Agave/Jito Solana stack for [laconic-so](https://github.com/LaconicNetwork/stack-orchestrator). Deploys Solana validators, RPC nodes, and test validators as containers with optional [DoubleZero](https://doublezero.xyz) network routing.

## Modes

| Mode | Compose file | Use case |
|------|-------------|----------|
| `validator` | `docker-compose-agave.yml` | Voting validator (mainnet/testnet) |
| `rpc` | `docker-compose-agave-rpc.yml` | Non-voting RPC node |
| `test` | `docker-compose-agave-test.yml` | Local dev with instant finality |

Mode is selected via the `AGAVE_MODE` environment variable.

## Repository layout

```
agave-stack/
├── deployment/                              # Reference deployment (biscayne)
│   ├── spec.yml                            # k8s-kind deployment spec
│   └── k8s-manifests/
│       └── doublezero-daemonset.yaml       # DZ DaemonSet (hostNetwork)
├── stack-orchestrator/
│   ├── stacks/agave/
│   │   ├── stack.yml                       # laconic-so stack definition
│   │   └── README.md                       # Stack-level docs
│   ├── compose/
│   │   ├── docker-compose-agave.yml        # Voting validator
│   │   ├── docker-compose-agave-rpc.yml    # Non-voting RPC
│   │   ├── docker-compose-agave-test.yml   # Test validator
│   │   └── docker-compose-doublezero.yml   # DoubleZero daemon
│   ├── container-build/
│   │   ├── laconicnetwork-agave/           # Agave/Jito image
│   │   │   ├── Dockerfile                  # Two-stage build from source
│   │   │   ├── build.sh                    # laconic-so build script
│   │   │   ├── entrypoint.sh               # Mode router
│   │   │   ├── start-validator.sh          # Voting validator startup
│   │   │   ├── start-rpc.sh               # RPC node startup
│   │   │   └── start-test.sh              # Test validator + SPL setup
│   │   └── laconicnetwork-doublezero/      # DoubleZero image
│   │       ├── Dockerfile                  # Installs from Cloudsmith apt
│   │       ├── build.sh
│   │       └── entrypoint.sh
│   └── config/agave/
│       ├── restart-node.sh                 # Container restart helper
│       └── restart.cron                    # Scheduled restart schedule
```

## Prerequisites

- [laconic-so](https://github.com/LaconicNetwork/stack-orchestrator) (stack orchestrator)
- Docker
- Kind (for k8s deployments)

## Building

```bash
# Vanilla Agave v3.1.9
laconic-so --stack agave build-containers

# Jito v3.1.8 (required for MEV)
AGAVE_REPO=https://github.com/jito-foundation/jito-solana.git \
AGAVE_VERSION=v3.1.8-jito \
laconic-so --stack agave build-containers
```

Build compiles from source (~30-60 min on first build). This produces both the `laconicnetwork/agave:local` and `laconicnetwork/doublezero:local` images.

## Deploying

### Test validator (local dev)

```bash
laconic-so --stack agave deploy init --output spec.yml
laconic-so --stack agave deploy create --spec-file spec.yml --deployment-dir my-test
laconic-so deployment --dir my-test start
```

The test validator starts with instant finality and optionally creates SPL token mints and airdrops to configured pubkeys.

### Mainnet/testnet (Docker Compose)

```bash
laconic-so --stack agave deploy init --output spec.yml
# Edit spec.yml: set AGAVE_MODE, VALIDATOR_ENTRYPOINT, KNOWN_VALIDATOR, etc.
laconic-so --stack agave deploy create --spec-file spec.yml --deployment-dir my-node
laconic-so deployment --dir my-node start
```

### Kind/k8s deployment

The `deployment/spec.yml` provides a reference spec targeting `k8s-kind`. The compose files use `network_mode: host` which works for Docker Compose and is silently ignored by laconic-so's k8s conversion (it uses explicit ports from the deployment spec instead).

```bash
laconic-so --stack agave deploy create \
  --spec-file deployment/spec.yml \
  --deployment-dir my-deployment

# Mount validator keypairs
cp validator-identity.json my-deployment/data/validator-config/
cp vote-account-keypair.json my-deployment/data/validator-config/  # validator mode only

laconic-so deployment --dir my-deployment start
```

## Configuration

### Common (all modes)

| Variable | Default | Description |
|----------|---------|-------------|
| `AGAVE_MODE` | `test` | `test`, `rpc`, or `validator` |
| `VALIDATOR_ENTRYPOINT` | *required* | Cluster entrypoint (host:port) |
| `KNOWN_VALIDATOR` | *required* | Known validator pubkey |
| `EXTRA_ENTRYPOINTS` | | Space-separated additional entrypoints |
| `EXTRA_KNOWN_VALIDATORS` | | Space-separated additional known validators |
| `RPC_PORT` | `8899` | RPC HTTP port |
| `RPC_BIND_ADDRESS` | `127.0.0.1` | RPC bind address |
| `GOSSIP_PORT` | `8001` | Gossip protocol port |
| `DYNAMIC_PORT_RANGE` | `8000-10000` | TPU/TVU/repair UDP port range |
| `LIMIT_LEDGER_SIZE` | `50000000` | Max ledger slots to retain |
| `SNAPSHOT_INTERVAL_SLOTS` | `1000` | Full snapshot interval |
| `MAXIMUM_SNAPSHOTS_TO_RETAIN` | `5` | Max full snapshots |
| `EXPECTED_GENESIS_HASH` | | Cluster genesis verification |
| `EXPECTED_SHRED_VERSION` | | Shred version verification |
| `RUST_LOG` | `info` | Log level |
| `SOLANA_METRICS_CONFIG` | | Metrics reporting config |

### Validator mode

| Variable | Default | Description |
|----------|---------|-------------|
| `VOTE_ACCOUNT_KEYPAIR` | `/data/config/vote-account-keypair.json` | Vote account keypair path |

Identity keypair must be mounted at `/data/config/validator-identity.json`.

### RPC mode

| Variable | Default | Description |
|----------|---------|-------------|
| `PUBLIC_RPC_ADDRESS` | | If set, advertise as public RPC |
| `ACCOUNT_INDEXES` | `program-id,spl-token-owner,spl-token-mint` | Account indexes for queries |

Identity is auto-generated if not mounted.

### Jito MEV (validator and RPC modes)

Set `JITO_ENABLE=true` and provide:

| Variable | Description |
|----------|-------------|
| `JITO_BLOCK_ENGINE_URL` | Block engine endpoint |
| `JITO_SHRED_RECEIVER_ADDR` | Shred receiver (region-specific) |
| `JITO_RELAYER_URL` | Relayer URL (validator mode) |
| `JITO_TIP_PAYMENT_PROGRAM` | Tip payment program pubkey |
| `JITO_DISTRIBUTION_PROGRAM` | Tip distribution program pubkey |
| `JITO_MERKLE_ROOT_AUTHORITY` | Merkle root upload authority |
| `JITO_COMMISSION_BPS` | Commission basis points |

Image must be built from `jito-foundation/jito-solana` for Jito flags to work.

### Test mode

| Variable | Default | Description |
|----------|---------|-------------|
| `FACILITATOR_PUBKEY` | | Pubkey to airdrop SOL |
| `SERVER_PUBKEY` | | Pubkey to airdrop SOL |
| `CLIENT_PUBKEY` | | Pubkey to airdrop SOL + create ATA |
| `MINT_DECIMALS` | `6` | SPL token decimals |
| `MINT_AMOUNT` | `1000000` | SPL tokens to mint |

## DoubleZero

[DoubleZero](https://doublezero.xyz) provides optimized network routing for Solana validators via GRE tunnels (IP protocol 47) and BGP (TCP/179) over link-local 169.254.0.0/16. Validator traffic to other DZ participants is routed through private fiber instead of the public internet.

### How it works

`doublezerod` creates a `doublezero0` GRE tunnel interface and runs BGP peering through it. Routes are injected into the host routing table, so the validator transparently sends traffic over the fiber backbone. IBRL mode falls back to public internet if DZ is down.

### Requirements

- Validator identity keypair at `/data/config/validator-identity.json`
- `privileged: true` + `NET_ADMIN` (GRE tunnel + route table manipulation)
- `hostNetwork: true` (GRE uses IP protocol 47 — cannot be port-mapped)
- Node registered with DoubleZero passport system

### Docker Compose

`docker-compose-doublezero.yml` runs alongside the validator with `network_mode: host`, sharing the `validator-config` volume for identity access.

### k8s

laconic-so does not pass `hostNetwork` through to generated k8s resources. DoubleZero runs as a DaemonSet applied after `deployment start`:

```bash
kubectl apply -f deployment/k8s-manifests/doublezero-daemonset.yaml
```

Since the validator pods share the node's network namespace, they automatically see the GRE routes injected by `doublezerod`.

| Variable | Default | Description |
|----------|---------|-------------|
| `VALIDATOR_IDENTITY_PATH` | `/data/config/validator-identity.json` | Validator identity keypair |
| `DOUBLEZERO_RPC_ENDPOINT` | `http://127.0.0.1:8899` | Solana RPC for DZ registration |
| `DOUBLEZERO_EXTRA_ARGS` | | Additional doublezerod arguments |

## Runtime requirements

The container requires the following (already set in compose files):

| Setting | Value | Why |
|---------|-------|-----|
| `privileged` | `true` | `mlock()` syscall and raw network access |
| `cap_add` | `IPC_LOCK` | Memory page locking for account indexes and ledger |
| `ulimits.memlock` | `-1` (unlimited) | Agave locks gigabytes of memory |
| `ulimits.nofile` | `1000000` | Gossip/TPU connections + memory-mapped ledger files |
| `network_mode` | `host` | Direct host network stack for gossip, TPU, UDP ranges |

Without these, Agave either refuses to start or dies under load.

## Container overhead

Containers with `privileged: true` and `network_mode: host` add **zero measurable overhead** vs bare metal. Linux containers are not VMs:

- **Network**: Host network namespace directly — no bridge, no NAT, no veth. Same kernel code path as bare metal.
- **CPU**: No hypervisor. Same physical cores, same scheduler priority.
- **Memory**: `IPC_LOCK` + unlimited memlock = identical `mlock()` behavior.
- **Disk I/O**: hostPath-backed PVs have identical I/O characteristics.

The only overhead is cgroup accounting (nanoseconds per syscall) and overlayfs for cold file opens (single-digit microseconds, zero once cached).

## Scheduled restarts

The `config/agave/restart.cron` defines periodic restarts to mitigate memory growth:

- **Validator**: every 4 hours
- **RPC**: every 6 hours (staggered 30 min offset)

Uses `restart-node.sh` which sends TERM to the matching container for graceful shutdown.

## Biscayne reference deployment

The `deployment/` directory contains a reference deployment for biscayne.vaasl.io (186.233.184.235), a mainnet voting validator with Jito MEV and DoubleZero:

```bash
# Build Jito image
AGAVE_REPO=https://github.com/jito-foundation/jito-solana.git \
AGAVE_VERSION=v3.1.8-jito \
laconic-so --stack agave build-containers

# Create deployment
laconic-so --stack agave deploy create \
  --spec-file deployment/spec.yml \
  --deployment-dir biscayne-deployment

# Mount keypairs
cp validator-identity.json biscayne-deployment/data/validator-config/
cp vote-account-keypair.json biscayne-deployment/data/validator-config/

# Start
laconic-so deployment --dir biscayne-deployment start

# Start DoubleZero
kubectl apply -f deployment/k8s-manifests/doublezero-daemonset.yaml
```

To run as non-voting RPC, change `AGAVE_MODE: rpc` in `deployment/spec.yml`.

## Volumes

| Volume | Mount | Content |
|--------|-------|---------|
| `validator-config` / `rpc-config` | `/data/config` | Identity keypairs, node config |
| `validator-ledger` / `rpc-ledger` | `/data/ledger` | Blockchain ledger data |
| `validator-accounts` / `rpc-accounts` | `/data/accounts` | Account state cache |
| `validator-snapshots` / `rpc-snapshots` | `/data/snapshots` | Full and incremental snapshots |
| `doublezero-config` | `~/.config/doublezero` | DZ identity and state |
