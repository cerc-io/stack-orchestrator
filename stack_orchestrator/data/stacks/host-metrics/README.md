# host-metrics stack

Per-host system metrics collector. Runs telegraf with host networking, host
PID namespace, and read-only bind mounts of /proc, /sys, and / so it can
report real CPU, memory, disk, network, and process metrics for the machine
it runs on. Writes to an InfluxDB 1.x endpoint of your choosing.

Deploy one instance per machine you want monitored.

## What gets collected

| Input | Measurements (in InfluxDB) |
|-------|----------------------------|
| inputs.cpu (totalcpu only) | cpu (`cpu=cpu-total`) |
| inputs.mem | mem |
| inputs.swap | swap |
| inputs.system | system (uptime, load1/5/15, n_users, n_cpus) |
| inputs.processes | processes (running/sleeping/blocked/zombies) |
| inputs.disk | disk (used/free/used_percent per mount) |
| inputs.diskio | diskio (read/write bytes/ops per device) |
| inputs.net | net (bytes/packets/err in/out per interface) |
| inputs.zfs (opt-in via COLLECT_ZFS=true) | zfs (ARC stats, pool state) |

All rows are tagged with `host` (kernel hostname, or `HOST_TAG` override).

## Deploy

### Create a spec

```bash
laconic-so --stack host-metrics deploy init --output spec-host-metrics.yml
```

Edit `spec-host-metrics.yml` to look like:

```yaml
stack: host-metrics
deploy-to: compose
credentials-files:
  - ~/.credentials/host-metrics.env
config:
  INFLUXDB_URL: 'https://influxdb.example.com'
  INFLUXDB_DB: 'host_metrics'          # default; override for a custom DB
  HOST_TAG: 'validator-1'              # optional; defaults to kernel hostname
  COLLECT_INTERVAL: '10s'              # telegraf collection + flush cadence
  COLLECT_ZFS: 'false'                 # set to 'true' on ZFS hosts
```

`~/.credentials/host-metrics.env` must contain:

```
INFLUXDB_WRITE_USER=<writer-username>
INFLUXDB_WRITE_PASSWORD=<writer-password>
```

These are issued by the InfluxDB admin (the monitoring host operator); they
are the same writer-only credentials used by validators/RPCs to push agave
metrics.

### Create and start

```bash
laconic-so --stack host-metrics deploy create \
    --spec-file spec-host-metrics.yml \
    --deployment-dir ./deployment-host-metrics
laconic-so deployment --dir ./deployment-host-metrics start
```

`deploy create` builds the deployment dir from the spec; `deployment start`
brings the containers up. The `--stack` option is required for `deploy`
subcommands but rejected on `deployment` subcommands (the deployment dir
already knows its stack).

### Verify

```bash
laconic-so deployment --dir ./deployment-host-metrics logs host-telegraf | head
```

Expected: telegraf prints its startup banner and `Loaded inputs: ...`. No
errors about missing config or auth failures.

Within ~20 seconds, the host's data appears in the InfluxDB endpoint's
`host_metrics` database (or whichever DB you set in INFLUXDB_DB) and in
any Grafana dashboards bound to that DB.

## Configuration reference

| Env | Required | Default | Notes |
|-----|----------|---------|-------|
| `INFLUXDB_URL` | yes | - | Full URL including scheme. Example: `https://influxdb.example.com`. |
| `INFLUXDB_DB` | no | `host_metrics` | Target database. Must exist (writer is not granted CREATE). |
| `INFLUXDB_WRITE_USER` | yes | - | Writer-only user. |
| `INFLUXDB_WRITE_PASSWORD` | yes | - | Writer-only password. |
| `COLLECT_INTERVAL` | no | `10s` | Telegraf collection and flush cadence. |
| `HOST_TAG` | no | empty | Overrides the kernel hostname for the `host` tag on every row. Useful when a VM has a generic hostname. |
| `COLLECT_ZFS` | no | `false` | Set to `true` to enable `inputs.zfs` (pool state + ARC stats). |

## ZFS hosts

`inputs.disk` already reports used/free per mount for any filesystem type
including ZFS, so the disk-usage view works out of the box. Setting
`COLLECT_ZFS=true` additionally enables `inputs.zfs` which reads
`/proc/spl/kstat/zfs/...` and emits ARC hit ratio, ARC size, and per-pool
health metrics. The bind mount of `/proc` provides the necessary
visibility; no extra mounts are needed.

If you set `COLLECT_ZFS=true` on a non-ZFS host, telegraf logs an error
once per collection cycle and skips the input. Harmless but noisy; leave
the toggle off on non-ZFS machines.

## Troubleshooting

| Symptom | Likely cause |
|---------|-------------|
| Container fails to start with `FATAL: INFLUXDB_URL is required but empty` | Missing required env. Check spec.yml + credentials file. |
| Container starts, no rows appear in InfluxDB | Writer credentials wrong, or InfluxDB unreachable from this host's network. Check `docker logs <host-telegraf>` for `Post ... 401` / `connection refused`. |
| Two hosts overwriting each other's series | Both use the same kernel hostname. Set distinct `HOST_TAG` values. |
| `inputs.processes` reports only 1 process | `pid: host` missing from compose. Re-deploy. |

## Caveats

- Requires Docker with privileges to bind-mount `/`, `/proc`, `/sys`, and to
  share the host PID namespace. Rootless Docker installations may refuse
  `pid: host` and the `/` bind mount.
- One deployment per host. Running two on the same machine writes
  duplicate rows under the same `host` tag.
