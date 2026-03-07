# Known Issues

## BUG-6: Validator logging not configured, only stdout available

**Observed:** 2026-03-03

The validator only logs to stdout. kubectl logs retains ~2 minutes of history
at current log volume before the buffer fills. When diagnosing a replay stall,
the startup logs (snapshot load, initial replay, error conditions) were gone.

**Impact:** Cannot determine why the validator replay stage stalled — the
startup logs that would show the root cause are not available.

**Fix:** Configure the `--log` flag in the validator start script to write to
a persistent volume, so logs survive container restarts and aren't limited
to the kubectl buffer.

## BUG-7: Metrics endpoint unreachable from validator pod

**Observed:** 2026-03-03

```
WARN solana_metrics::metrics submit error: error sending request for url
(http://localhost:8086/write?db=agave_metrics&u=admin&p=admin&precision=n)
```

The validator is configured with `SOLANA_METRICS_CONFIG` pointing to
`http://172.20.0.1:8086` (the kind docker bridge gateway), but the logs show
it trying `localhost:8086`. The InfluxDB container (`solana-monitoring-influxdb-1`)
is running on the host, but the validator can't reach it.

**Impact:** No metrics collection. Cannot use Grafana dashboards to diagnose
performance issues or track sync progress over time.

## BUG-8: sysctl values not visible inside kind container

**Observed:** 2026-03-03

```
ERROR solana_core::system_monitor_service Failed to query value for net.core.rmem_max: no such sysctl
WARN  solana_core::system_monitor_service net.core.rmem_max: recommended=134217728, current=-1 too small
```

The host has correct sysctl values (`net.core.rmem_max = 134217728`), but
`/proc/sys/net/core/` does not exist inside the kind node container. The
validator reads `-1` and reports the buffer as too small.

The network buffers themselves may still be effective (they're set on the
host network namespace which the pod shares via `hostNetwork: true`), but
this is unverified. If the buffers are not effective, it could limit shred
ingestion throughput and contribute to slow repair.

**Fix options:**
- Set sysctls on the kind node container at creation time
  (`kind` supports `kubeadmConfigPatches` and sysctl configuration)
- Verify empirically whether the host sysctls apply to hostNetwork pods
  by checking actual socket buffer sizes from inside the pod

## Validator replay stall (under investigation)

**Observed:** 2026-03-03

The validator root has been stuck at slot 403,892,310 for 55+ minutes.
The gap to the cluster tip is ~120,000 slots and growing.

**Observed symptoms:**
- Zero `Frozen` banks in log history — replay stage is not processing slots
- All incoming slots show `bank_status: Unprocessed`
- Repair only requests tip slots and two specific old slots (403,892,310,
  403,909,228) — not the ~120k slot gap
- Repair peer count is 3-12 per cycle (vs 1,000+ gossip peers)
- Startup logs have rotated out (BUG-6), so initialization context is lost

**Unknown:**
- What snapshot the validator loaded at boot
- Whether replay ever started or was blocked from the beginning
- Whether the sysctl issue (BUG-8) is limiting repair throughput
- Whether the missing metrics (BUG-7) would show what's happening internally
