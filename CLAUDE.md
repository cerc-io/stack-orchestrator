# Biscayne Agave Runbook

## Cluster Operations

### Shutdown Order

The agave validator runs inside a kind-based k8s cluster managed by `laconic-so`.
The kind node is a Docker container. **Never restart or kill the kind node container
while the validator is running.** Agave uses `io_uring` for async I/O, and on ZFS,
killing the process can produce unkillable kernel threads (D-state in
`io_wq_put_and_exit` blocked on ZFS transaction commits). This deadlocks the
container's PID namespace, making `docker stop`, `docker restart`, `docker exec`,
and even `reboot` hang.

Correct shutdown sequence:

1. Scale the deployment to 0 and wait for the pod to terminate:
   ```
   kubectl scale deployment laconic-70ce4c4b47e23b85-deployment \
     -n laconic-laconic-70ce4c4b47e23b85 --replicas=0
   kubectl wait --for=delete pod -l app=laconic-70ce4c4b47e23b85-deployment \
     -n laconic-laconic-70ce4c4b47e23b85 --timeout=120s
   ```
2. Only then restart the kind node if needed:
   ```
   docker restart laconic-70ce4c4b47e23b85-control-plane
   ```
3. Scale back up:
   ```
   kubectl scale deployment laconic-70ce4c4b47e23b85-deployment \
     -n laconic-laconic-70ce4c4b47e23b85 --replicas=1
   ```

### Ramdisk

The accounts directory must be on a ramdisk for performance. `/dev/ram0` loses its
filesystem on reboot and must be reformatted before mounting.

**Boot ordering is handled by systemd units** (installed by `biscayne-boot.yml`):
- `format-ramdisk.service`: runs `mkfs.xfs -f /dev/ram0` before `local-fs.target`
- fstab entry: mounts `/dev/ram0` at `/srv/solana/ramdisk` with
  `x-systemd.requires=format-ramdisk.service`
- `ramdisk-accounts.service`: creates `/srv/solana/ramdisk/accounts` and sets
  ownership after the mount

These units run before docker, so the kind node's bind mounts always see the
ramdisk. **No manual intervention is needed after reboot.**

**Mount propagation**: The kind node bind-mounts `/srv/kind` → `/mnt`. Because
the ramdisk is mounted at `/srv/solana/ramdisk` and symlinked/overlaid through
`/srv/kind/solana/ramdisk`, mount propagation makes it visible inside the kind
node at `/mnt/solana/ramdisk` without restarting the kind node. **Do NOT restart
the kind node just to pick up a ramdisk mount.**

### KUBECONFIG

kubectl must be told where the kubeconfig is when running as root or via ansible:
```
KUBECONFIG=/home/rix/.kube/config kubectl ...
```

The ansible playbooks set `environment: KUBECONFIG: /home/rix/.kube/config`.

### SSH Agent

SSH to biscayne goes through a ProxyCommand jump host (abernathy.ch2.vaasl.io).
The SSH agent socket rotates when the user reconnects. Find the current one:
```
ls -t /tmp/ssh-*/agent.* | head -1
```
Then export it:
```
export SSH_AUTH_SOCK=/tmp/ssh-XXXX/agent.NNNN
```

### io_uring/ZFS Deadlock — Root Cause

When agave-validator is killed while performing I/O against ZFS-backed paths (not
the ramdisk), io_uring worker threads get stuck in D-state:
```
io_wq_put_and_exit → dsl_dir_tempreserve_space (ZFS module)
```
These threads are unkillable (SIGKILL has no effect on D-state processes). They
prevent the container's PID namespace from being reaped (`zap_pid_ns_processes`
waits forever), which breaks `docker stop`, `docker restart`, `docker exec`, and
even `reboot`. The only fix is a hard power cycle.

**Prevention**: Always scale the deployment to 0 and wait for the pod to terminate
before any destructive operation (namespace delete, kind restart, host reboot).
The `biscayne-stop.yml` playbook enforces this.

### laconic-so Architecture

`laconic-so` manages kind clusters atomically — `deployment start` creates the
kind cluster, namespace, PVs, PVCs, and deployment in one shot. There is no way
to create the cluster without deploying the pod.

Key code paths in stack-orchestrator:
- `deploy_k8s.py:up()` — creates everything atomically
- `cluster_info.py:get_pvs()` — translates host paths using `kind-mount-root`
- `helpers_k8s.py:get_kind_pv_bind_mount_path()` — strips `kind-mount-root`
  prefix and prepends `/mnt/`
- `helpers_k8s.py:_generate_kind_mounts()` — when `kind-mount-root` is set,
  emits a single `/srv/kind` → `/mnt` mount instead of individual mounts

The `kind-mount-root: /srv/kind` setting in `spec.yml` means all data volumes
whose host paths start with `/srv/kind` get translated to `/mnt/...` inside the
kind node via a single bind mount.

### Key Identifiers

- Kind cluster: `laconic-70ce4c4b47e23b85`
- Namespace: `laconic-laconic-70ce4c4b47e23b85`
- Deployment: `laconic-70ce4c4b47e23b85-deployment`
- Kind node container: `laconic-70ce4c4b47e23b85-control-plane`
- Deployment dir: `/srv/deployments/agave`
- Snapshot dir: `/srv/solana/snapshots`
- Ledger dir: `/srv/solana/ledger`
- Accounts dir: `/srv/solana/ramdisk/accounts`
- Log dir: `/srv/solana/log`
- Host bind mount root: `/srv/kind` -> kind node `/mnt`
- laconic-so: `/home/rix/.local/bin/laconic-so` (editable install)

### PV Mount Paths (inside kind node)

| PV Name              | hostPath                      |
|----------------------|-------------------------------|
| validator-snapshots  | /mnt/solana/snapshots         |
| validator-ledger     | /mnt/solana/ledger            |
| validator-accounts   | /mnt/solana/ramdisk/accounts  |
| validator-log        | /mnt/solana/log               |

### Snapshot Freshness

If the snapshot is more than **20,000 slots behind** the current mainnet tip, it is
too old. Stop the validator, download a fresh snapshot, and restart. Do NOT let it
try to catch up from an old snapshot — it will take too long and may never converge.

Check with:
```
# Snapshot slot (from filename)
ls /srv/solana/snapshots/snapshot-*.tar.*

# Current mainnet slot
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getSlot","params":[{"commitment":"finalized"}]}' \
  https://api.mainnet-beta.solana.com
```

### Snapshot Leapfrog Recovery

When the validator is stuck in a repair-dependent gap (incomplete shreds from a
relay outage or insufficient turbine coverage), "grinding through" doesn't work.
At 0.4 slots/sec replay through incomplete blocks vs 2.5 slots/sec chain
production, the gap grows faster than it shrinks.

**Strategy**: Download a fresh snapshot whose slot lands *past* the incomplete zone,
into the range where turbine+relay shreds are accumulating in the blockstore.
**Keep the existing ledger** — it has those shreds. The validator replays from
local blockstore data instead of waiting on repair.

**Steps**:
1. Let the validator run — turbine+relay accumulate shreds at the tip
2. Monitor shred completeness at the tip:
   `scripts/check-shred-completeness.sh 500`
3. When there's a contiguous run of complete blocks (>100 slots), note the
   starting slot of that run
4. Scale to 0, wipe accounts (ramdisk), wipe old snapshots
5. **Do NOT wipe ledger** — it has the turbine shreds
6. Download a fresh snapshot (its slot should be within the complete run)
7. Scale to 1 — validator replays from local blockstore at 3-5 slots/sec

**Why this works**: Turbine delivers ~60% of shreds in real-time. Repair fills
the rest for recent slots quickly (peers prioritize recent data). The only
problem is repair for *old* slots (minutes/hours behind) which peers deprioritize.
By snapshotting past the gap, we skip the old-slot repair bottleneck entirely.

### Shred Relay (Ashburn)

The TVU shred relay from laconic-was-sw01 provides ~4,000 additional shreds/sec.
Without it, turbine alone delivers ~60% of blocks. With it, completeness improves
but still requires repair for full coverage.

**Current state**: Old pipeline (monitor session + socat + shred-unwrap.py).
The traffic-policy redirect was never committed (auto-revert after 5 min timer).
See `docs/tvu-shred-relay.md` for the traffic-policy config that needs to be
properly applied.

**Boot dependency**: `shred-unwrap.py` must be running on biscayne for the old
pipeline to work. It is NOT persistent across reboots. The iptables DNAT rule
for the new pipeline IS persistent (iptables-persistent installed).

### Redeploy Flow

See `playbooks/biscayne-redeploy.yml`. The scale-to-0 pattern is required because
`laconic-so` creates the cluster and deploys the pod atomically:

1. Delete namespace (teardown)
2. Optionally wipe data
3. `laconic-so deployment start` (creates cluster + pod)
4. Immediately scale to 0
5. Download snapshot via aria2c
6. Scale to 1
7. Verify
