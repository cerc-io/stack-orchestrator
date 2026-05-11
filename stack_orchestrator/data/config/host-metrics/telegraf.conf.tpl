# host-metrics telegraf template.
# Rendered at container start by telegraf-entrypoint.sh. The entrypoint
# replaces two single-line markers in this file with TOML block fragments;
# see telegraf-entrypoint.sh for the substitution details. All ${...}
# variables are resolved by telegraf's native env substitution at
# config-load time.

@@HOST_TAG_BLOCK@@

[agent]
  interval = "${COLLECT_INTERVAL}"
  round_interval = true
  collection_jitter = "0s"
  flush_interval = "${COLLECT_INTERVAL}"
  flush_jitter = "0s"
  precision = "0s"
  hostname = ""
  omit_hostname = false

[[outputs.influxdb]]
  urls = ["${INFLUXDB_URL}"]
  database = "${INFLUXDB_DB}"
  skip_database_creation = true
  username = "${INFLUXDB_USER}"
  password = "${INFLUXDB_PASSWORD}"
  retention_policy = ""
  write_consistency = "any"
  timeout = "10s"

[[inputs.cpu]]
  percpu = false
  totalcpu = true
  collect_cpu_time = false
  report_active = true

[[inputs.mem]]

[[inputs.swap]]

[[inputs.system]]

[[inputs.processes]]

[[inputs.disk]]
  # gopsutil with HOST_MOUNT_PREFIX=/hostfs strips the /hostfs prefix
  # from /proc/mounts entries, so the mountpoints telegraf sees are
  # the host's real paths (/, /boot, /home, ...). No mount_points
  # filter; let ignore_fs do the noise reduction.
  ignore_fs = ["tmpfs", "devtmpfs", "devfs", "iso9660", "overlay",
               "aufs", "squashfs", "nsfs", "tracefs", "proc", "sysfs",
               "cgroup", "cgroup2", "fuse.lxcfs"]

[[inputs.diskio]]
  device_tags = ["DEVNAME"]
  skip_serial_number = true
  name_templates = ["$DEVNAME"]

[[inputs.net]]
  # Allowlist covers physical ethernet (eth*, en*), wireless (wl*),
  # cellular (wwan*), and bonded/teamed interfaces (bond*). Excludes
  # docker bridges, veth pairs, tun/tap, and lo. Adjust per host if
  # you need a more specific scope.
  ignore_protocol_stats = true
  interfaces = ["eth*", "en*", "wl*", "wwan*", "bond*"]

@@ZFS_BLOCK@@
