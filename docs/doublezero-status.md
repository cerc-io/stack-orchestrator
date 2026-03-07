# DoubleZero Current State and Bug Fixes

## Biscayne Connection Details

| Field | Value |
|-------|-------|
| Host | biscayne.vaasl.io (186.233.184.235) |
| DZ identity | `3Bw6v7EruQvTwoY79h2QjQCs2KBQFzSneBdYUbcXK1Tr` |
| Validator identity | `4WeLUxfQghbhsLEuwaAzjZiHg2VBw87vqHc4iZrGvKPr` |
| Nearest device | laconic-mia-sw01 (0.3ms) |
| DZ version (host) | 0.8.10 |
| DZ version (container) | 0.8.11 |
| k8s version | 1.35.1 (kind) |

## Current State (2026-03-03)

The host systemd `doublezerod` is connected and working. The container sidecar
doublezerod is broken. Both are running simultaneously.

| Instance | Identity | Status |
|----------|----------|--------|
| Host systemd | `3Bw6v7...` (correct) | BGP Session Up, IBRL to laconic-mia-sw01 |
| Container sidecar | `Cw9qun...` (wrong) | Disconnected, error loop |
| DaemonSet manifest | N/A | Never applied, dead code |

### Access pass

The access pass for 186.233.184.235 is registered and connected:

```
type: prepaid
payer: 3Bw6v7EruQvTwoY79h2QjQCs2KBQFzSneBdYUbcXK1Tr
status: connected
owner: DZfLKFDgLShjY34WqXdVVzHUvVtrYXb7UtdrALnGa8jw
```

## Bugs

### BUG-1: Container doublezerod has wrong identity

The entrypoint script (`entrypoint.sh`) auto-generates a new `id.json` if one isn't
found. The volume at `/srv/deployments/agave/data/doublezero-config/` was empty at
first boot, so it generated `Cw9qun...` instead of using the registered identity.

**Root cause:** The real `id.json` lives at `/home/solana/.config/doublezero/id.json`
(created by the host-level DZ install). The container volume is a separate path that
was never seeded.

**Fix:**
```bash
sudo cp /home/solana/.config/doublezero/id.json \
  /srv/deployments/agave/data/doublezero-config/id.json
```

### BUG-2: Container doublezerod can't resolve DZ passport program

`DOUBLEZERO_RPC_ENDPOINT` in `spec.yml` is `http://127.0.0.1:8899` — the local
validator. But the local validator hasn't replayed enough slots to have the DZ
passport program accounts (`ser2VaTMAcYTaauMrTSfSrxBaUDq7BLNs2xfUugTAGv`).
doublezerod calls `GetProgramAccounts` every 30 seconds and gets empty results.

**Fix in `deployment/spec.yml`:**
```yaml
# Use public RPC for DZ bootstrapping until local validator is caught up
DOUBLEZERO_RPC_ENDPOINT: https://api.mainnet-beta.solana.com
```

Switch back to `http://127.0.0.1:8899` once the local validator is synced.

### BUG-3: Container doublezerod lacks hostNetwork

laconic-so was not translating `network_mode: host` from compose files to
`hostNetwork: true` in generated k8s pod specs. Without host network access, the
container can't create GRE tunnels (IP proto 47) or run BGP (tcp/179 on
169.254.0.0/16).

**Fix:** Deploy with stack-orchestrator branch `fix/k8s-port-mappings-hostnetwork-v2`
(commit `fb69cc58`, 2026-03-03) which adds automatic hostNetwork detection.

### BUG-4: DaemonSet workaround is dead code

`deployment/k8s-manifests/doublezero-daemonset.yaml` was a workaround for BUG-3.
Now that laconic-so supports hostNetwork natively, it should be deleted.

**Fix:** Remove `deployment/k8s-manifests/doublezero-daemonset.yaml` from agave-stack.

### BUG-5: Two doublezerod instances running simultaneously

The host systemd `doublezerod` and the container sidecar are both running. Once the
container is fixed (BUG-1 through BUG-3), the host service must be disabled to avoid
two processes fighting over the GRE tunnel.

**Fix:**
```bash
sudo systemctl stop doublezerod
sudo systemctl disable doublezerod
```

## Diagnostic Commands

Always use `sudo -u solana` for host-level DZ commands — the identity is under
`/home/solana/.config/doublezero/`.

```bash
# Host
sudo -u solana doublezero address          # expect 3Bw6v7...
sudo -u solana doublezero status           # tunnel state
sudo -u solana doublezero latency          # device reachability
sudo -u solana doublezero access-pass list | grep 186.233.184  # access pass
sudo -u solana doublezero balance          # credits
ip route | grep doublezero0                # BGP routes

# Container (from kind node)
kubectl -n <ns> exec <pod> -c doublezerod -- doublezero address
kubectl -n <ns> exec <pod> -c doublezerod -- doublezero status
kubectl -n <ns> exec <pod> -c doublezerod -- doublezero --version

# Logs
kubectl -n <ns> logs <pod> -c doublezerod --tail=30
sudo journalctl -u doublezerod -f          # host systemd logs
```
