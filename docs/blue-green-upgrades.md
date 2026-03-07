# Blue-Green Upgrades for Biscayne

Zero-downtime upgrade procedures for the agave-stack deployment on biscayne.
Uses ZFS clones for instant data duplication, Caddy health-check routing for
traffic shifting, and k8s native sidecars for independent container upgrades.

## Architecture

```
                    Caddy ingress (biscayne.vaasl.io)
                    ├── upstream A: localhost:8899  ← health: /health
                    └── upstream B: localhost:8897  ← health: /health
                              │
            ┌─────────────────┴──────────────────┐
            │         kind cluster                │
            │                                     │
            │  Deployment A        Deployment B   │
            │  ┌─────────────┐   ┌─────────────┐  │
            │  │ agave :8899 │   │ agave :8897 │  │
            │  │ doublezerod │   │ doublezerod │  │
            │  └──────┬──────┘   └──────┬──────┘  │
            └─────────┼─────────────────┼─────────┘
                      │                 │
              ZFS dataset A      ZFS clone B
              (original)         (instant CoW copy)
```

Both deployments run in the same kind cluster with `hostNetwork: true`.
Caddy active health checks route traffic to whichever deployment has a
healthy `/health` endpoint.

## Storage Layout

| Data | Path | Type | Survives restart? |
|------|------|------|-------------------|
| Ledger | `/srv/solana/ledger` | ZFS zvol (xfs) | Yes |
| Snapshots | `/srv/solana/snapshots` | ZFS zvol (xfs) | Yes |
| Accounts | `/srv/solana/ramdisk/accounts` | `/dev/ram0` (xfs) | Until host reboot |
| Validator config | `/srv/deployments/agave/data/validator-config` | ZFS | Yes |
| DZ config | `/srv/deployments/agave/data/doublezero-config` | ZFS | Yes |

The ZFS zvol `biscayne/DATA/volumes/solana` backs `/srv/solana` (ledger, snapshots).
The ramdisk at `/dev/ram0` holds accounts — it's a block device, not tmpfs, so it
survives process restarts but not host reboots.

---

## Procedure 1: DoubleZero Binary Upgrade (zero downtime, single pod)

The GRE tunnel (`doublezero0`) and BGP routes live in kernel space. They persist
across doublezerod process restarts. Upgrading the DZ binary does not require
tearing down the tunnel or restarting the validator.

### Prerequisites

- doublezerod is defined as a k8s native sidecar (`spec.initContainers` with
  `restartPolicy: Always`). See [Required Changes](#required-changes) below.
- k8s 1.29+ (biscayne runs 1.35.1)

### Steps

1. Build or pull the new doublezero container image.

2. Patch the pod's sidecar image:
   ```bash
   kubectl -n <ns> patch pod <pod> --type='json' -p='[
     {"op": "replace", "path": "/spec/initContainers/0/image",
      "value": "laconicnetwork/doublezero:new-version"}
   ]'
   ```

3. Only the doublezerod container restarts. The agave container is unaffected.
   The GRE tunnel interface and BGP routes remain in the kernel throughout.

4. Verify:
   ```bash
   kubectl -n <ns> exec <pod> -c doublezerod -- doublezero --version
   kubectl -n <ns> exec <pod> -c doublezerod -- doublezero status
   ip route | grep doublezero0   # routes still present
   ```

### Rollback

Patch the image back to the previous version. Same process, same zero downtime.

---

## Procedure 2: Agave Version Upgrade (zero RPC downtime, blue-green)

Agave is the main container and must be restarted for a version change. To maintain
zero RPC downtime, we run two deployments simultaneously and let Caddy shift traffic
based on health checks.

### Prerequisites

- Caddy ingress configured with dual upstreams and active health checks
- A parameterized spec.yml that accepts alternate ports and volume paths
- ZFS snapshot/clone scripts

### Steps

#### Phase 1: Prepare (no downtime, no risk)

1. **ZFS snapshot** for rollback safety:
   ```bash
   zfs snapshot -r biscayne/DATA@pre-upgrade-$(date +%Y%m%d)
   ```

2. **ZFS clone** the validator volumes:
   ```bash
   zfs clone biscayne/DATA/volumes/solana@pre-upgrade-$(date +%Y%m%d) \
     biscayne/DATA/volumes/solana-blue
   ```
   This is instant (copy-on-write). No additional storage until writes diverge.

3. **Clone the ramdisk accounts** (not on ZFS):
   ```bash
   mkdir -p /srv/solana-blue/ramdisk/accounts
   cp -a /srv/solana/ramdisk/accounts/* /srv/solana-blue/ramdisk/accounts/
   ```
   This is the slow step — 460GB on ramdisk. Consider `rsync` with `--inplace`
   to minimize copy time, or investigate whether the ramdisk can move to a ZFS
   dataset for instant cloning in future deployments.

4. **Build or pull** the new agave container image.

#### Phase 2: Start blue deployment (no downtime)

5. **Create Deployment B** in the same kind cluster, pointing at cloned volumes,
   with RPC on port 8897:
   ```bash
   # Apply the blue deployment manifest (parameterized spec)
   kubectl apply -f deployment/k8s-manifests/agave-blue.yaml
   ```

6. **Deployment B catches up.** It starts from the snapshot point and replays.
   Monitor progress:
   ```bash
   kubectl -n <ns> exec <blue-pod> -c agave-validator -- \
     solana -u http://127.0.0.1:8897 slot
   ```

7. **Validate** the new version works:
   - RPC responds: `curl -sf http://localhost:8897/health`
   - Correct version: `kubectl -n <ns> exec <blue-pod> -c agave-validator -- agave-validator --version`
   - doublezerod connected (if applicable)

   Take as long as needed. Deployment A is still serving all traffic.

#### Phase 3: Traffic shift (zero downtime)

8. **Caddy routes traffic to B.** Once B's `/health` returns 200, Caddy's active
   health check automatically starts routing to it. Alternatively, update the
   Caddy upstream config to prefer B.

9. **Verify** B is serving live traffic:
   ```bash
   curl -sf https://biscayne.vaasl.io/health
   # Check Caddy access logs for requests hitting port 8897
   ```

#### Phase 4: Cleanup

10. **Stop Deployment A:**
    ```bash
    kubectl -n <ns> delete deployment agave-green
    ```

11. **Reconfigure B to use standard port** (8899) if desired, or update Caddy
    to only route to 8897.

12. **Clean up ZFS clone** (or keep as rollback):
    ```bash
    zfs destroy biscayne/DATA/volumes/solana-blue
    ```

### Rollback

At any point before Phase 4:
- Deployment A is untouched and still serving traffic (or can be restarted)
- Delete Deployment B: `kubectl -n <ns> delete deployment agave-blue`
- Destroy the ZFS clone: `zfs destroy biscayne/DATA/volumes/solana-blue`

After Phase 4 (A already stopped):
- `zfs rollback` to restore original data
- Redeploy A with old image

---

## Required Changes to agave-stack

### 1. Move doublezerod to native sidecar

In the pod spec generation (laconic-so or compose override), doublezerod must be
defined as a native sidecar container instead of a regular container:

```yaml
spec:
  initContainers:
    - name: doublezerod
      image: laconicnetwork/doublezero:local
      restartPolicy: Always          # makes it a native sidecar
      securityContext:
        privileged: true
        capabilities:
          add: [NET_ADMIN]
      env:
        - name: DOUBLEZERO_RPC_ENDPOINT
          value: https://api.mainnet-beta.solana.com
      volumeMounts:
        - name: doublezero-config
          mountPath: /root/.config/doublezero
  containers:
    - name: agave-validator
      image: laconicnetwork/agave:local
      # ... existing config
```

This change means:
- doublezerod starts before agave and stays running
- Patching the doublezerod image restarts only that container
- agave can be restarted independently without affecting doublezerod

This requires a laconic-so change to support `initContainers` with `restartPolicy`
in compose-to-k8s translation — or a post-deployment patch.

### 2. Caddy dual-upstream config

Add health-checked upstreams for both blue and green deployments:

```caddyfile
biscayne.vaasl.io {
    reverse_proxy {
        to localhost:8899 localhost:8897

        health_uri /health
        health_interval 5s
        health_timeout 3s

        lb_policy first
    }
}
```

`lb_policy first` routes to the first healthy upstream. When only A is running,
all traffic goes to :8899. When B comes up healthy, traffic shifts.

### 3. Parameterized deployment spec

Create a parameterized spec or kustomize overlay that accepts:
- RPC port (8899 vs 8897)
- Volume paths (original vs ZFS clone)
- Deployment name suffix (green vs blue)

### 4. Delete DaemonSet workaround

Remove `deployment/k8s-manifests/doublezero-daemonset.yaml` from agave-stack.

### 5. Fix container DZ identity

Copy the registered identity into the container volume:
```bash
sudo cp /home/solana/.config/doublezero/id.json \
  /srv/deployments/agave/data/doublezero-config/id.json
```

### 6. Disable host systemd doublezerod

After the container sidecar is working:
```bash
sudo systemctl stop doublezerod
sudo systemctl disable doublezerod
```

---

## Implementation Order

This is a spec-driven, test-driven plan. Each step produces a testable artifact.

### Step 1: Fix existing DZ bugs (no code changes to laconic-so)

Fixes BUG-1 through BUG-5 from [doublezero-status.md](doublezero-status.md).

**Spec:** Container doublezerod shows correct identity, connects to laconic-mia-sw01,
host systemd doublezerod is disabled.

**Test:**
```bash
kubectl -n <ns> exec <pod> -c doublezerod -- doublezero address
# assert: 3Bw6v7EruQvTwoY79h2QjQCs2KBQFzSneBdYUbcXK1Tr

kubectl -n <ns> exec <pod> -c doublezerod -- doublezero status
# assert: BGP Session Up, laconic-mia-sw01

systemctl is-active doublezerod
# assert: inactive
```

**Changes:**
- Copy `id.json` to container volume
- Update `DOUBLEZERO_RPC_ENDPOINT` in spec.yml
- Deploy with hostNetwork-enabled stack-orchestrator
- Stop and disable host doublezerod
- Delete DaemonSet manifest from agave-stack

### Step 2: Native sidecar for doublezerod

**Spec:** doublezerod image can be patched without restarting the agave container.
GRE tunnel and routes persist across doublezerod restart.

**Test:**
```bash
# Record current agave container start time
BEFORE=$(kubectl -n <ns> get pod <pod> -o jsonpath='{.status.containerStatuses[?(@.name=="agave-validator")].state.running.startedAt}')

# Patch DZ image
kubectl -n <ns> patch pod <pod> --type='json' -p='[
  {"op":"replace","path":"/spec/initContainers/0/image","value":"laconicnetwork/doublezero:test"}
]'

# Wait for DZ container to restart
sleep 10

# Verify agave was NOT restarted
AFTER=$(kubectl -n <ns> get pod <pod> -o jsonpath='{.status.containerStatuses[?(@.name=="agave-validator")].state.running.startedAt}')
[ "$BEFORE" = "$AFTER" ]  # assert: same start time

# Verify tunnel survived
ip route | grep doublezero0  # assert: routes present
```

**Changes:**
- laconic-so: support `initContainers` with `restartPolicy: Always` in
  compose-to-k8s translation (or: define doublezerod as native sidecar in
  compose via `x-kubernetes-init-container` extension or equivalent)
- Alternatively: post-deploy kubectl patch to move doublezerod to initContainers

### Step 3: Caddy dual-upstream routing

**Spec:** Caddy routes RPC traffic to whichever backend is healthy. Adding a second
healthy backend on :8897 causes traffic to shift without configuration changes.

**Test:**
```bash
# Start a test HTTP server on :8897 with /health
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
HTTPServer(('', 8897), H).serve_forever()
" &

# Verify Caddy discovers it
sleep 10
curl -sf https://biscayne.vaasl.io/health
# assert: 200

kill %1
```

**Changes:**
- Update Caddy ingress config with dual upstreams and health checks

### Step 4: ZFS clone and blue-green tooling

**Spec:** A script creates a ZFS clone, starts a blue deployment on alternate ports
using the cloned data, and the deployment catches up and becomes healthy.

**Test:**
```bash
# Run the clone + deploy script
./scripts/blue-green-prepare.sh --target-version v2.2.1

# assert: ZFS clone exists
zfs list biscayne/DATA/volumes/solana-blue

# assert: blue deployment exists and is catching up
kubectl -n <ns> get deployment agave-blue

# assert: blue RPC eventually becomes healthy
timeout 600 bash -c 'until curl -sf http://localhost:8897/health; do sleep 5; done'
```

**Changes:**
- `scripts/blue-green-prepare.sh` — ZFS snapshot, clone, deploy B
- `scripts/blue-green-promote.sh` — tear down A, optional port swap
- `scripts/blue-green-rollback.sh` — destroy B, restore A
- Parameterized deployment spec (kustomize overlay or env-driven)

### Step 5: End-to-end upgrade test

**Spec:** Full upgrade cycle completes with zero dropped RPC requests.

**Test:**
```bash
# Start continuous health probe in background
while true; do
  curl -sf -o /dev/null -w "%{http_code} %{time_total}\n" \
    https://biscayne.vaasl.io/health || echo "FAIL $(date)"
  sleep 0.5
done > /tmp/health-probe.log &

# Execute full blue-green upgrade
./scripts/blue-green-prepare.sh --target-version v2.2.1
# wait for blue to sync...
./scripts/blue-green-promote.sh

# Stop probe
kill %1

# assert: no FAIL lines in probe log
grep -c FAIL /tmp/health-probe.log
# assert: 0
```
