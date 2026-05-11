# host-metrics stack

Per-host system metrics collector. Runs telegraf with host networking, host
PID namespace, and read-only bind mounts of /proc, /sys, and / so it can
report real CPU, memory, disk, network, and process metrics for the machine
it runs on. Writes to an InfluxDB 1.x endpoint of your choosing.

Deploy one instance per machine you want monitored.

## Quick deploy

(Filled in by a later task.)
