#!/usr/bin/env python3
"""Biscayne agave validator status check.

Collects and displays key health metrics:
- Slot position (local vs mainnet, gap, replay rate)
- Pod status (running, restarts, age)
- Memory usage (cgroup current vs limit, % used)
- OOM kills (recent dmesg entries)
- Shred relay (packets/sec on port 9100, shred-unwrap.py alive)
- Validator process state (from logs)
"""

import json
import subprocess
import sys
import time

NAMESPACE = "laconic-laconic-70ce4c4b47e23b85"
DEPLOYMENT = "laconic-70ce4c4b47e23b85-deployment"
KIND_NODE = "laconic-70ce4c4b47e23b85-control-plane"
SSH = "rix@biscayne.vaasl.io"
MAINNET_RPC = "https://api.mainnet-beta.solana.com"
LOCAL_RPC = "http://127.0.0.1:8899"


def ssh(cmd: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(
            ["ssh", SSH, cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout.strip() + r.stderr.strip()
    except subprocess.TimeoutExpired:
        return "<timeout>"


def local(cmd: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return "<timeout>"


def rpc_call(method: str, url: str = LOCAL_RPC, remote: bool = True, params: list | None = None) -> dict | None:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []})
    cmd = f"curl -s {url} -X POST -H 'Content-Type: application/json' -d '{payload}'"
    raw = ssh(cmd) if remote else local(cmd)
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def get_slots() -> tuple[int | None, int | None]:
    local_resp = rpc_call("getSlot")
    mainnet_resp = rpc_call("getSlot", MAINNET_RPC, remote=False)
    local_slot = local_resp.get("result") if local_resp else None
    mainnet_slot = mainnet_resp.get("result") if mainnet_resp else None
    return local_slot, mainnet_slot


def get_health() -> str:
    resp = rpc_call("getHealth")
    if not resp:
        return "unreachable"
    if "result" in resp and resp["result"] == "ok":
        return "healthy"
    err = resp.get("error", {})
    msg = err.get("message", "unknown")
    behind = err.get("data", {}).get("numSlotsBehind")
    if behind is not None:
        return f"behind {behind:,} slots"
    return msg


def get_pod_status() -> str:
    cmd = f"kubectl -n {NAMESPACE} get pods -o json"
    raw = ssh(cmd, timeout=15)
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return "unknown"
    items = data.get("items", [])
    if not items:
        return "no pods"
    pod = items[0]
    name = pod["metadata"]["name"].split("-")[-1]
    phase = pod["status"].get("phase", "?")
    containers = pod["status"].get("containerStatuses", [])
    restarts = sum(c.get("restartCount", 0) for c in containers)
    ready = sum(1 for c in containers if c.get("ready"))
    total = len(containers)
    age = pod["metadata"].get("creationTimestamp", "?")
    return f"{ready}/{total} {phase}  restarts={restarts}  pod=..{name}  created={age}"


def get_memory() -> str:
    cmd = (
        f"docker exec {KIND_NODE} bash -c '"
        "find /sys/fs/cgroup -name memory.current -path \"*burstable*\" 2>/dev/null | head -1 | "
        "while read f; do "
        "  dir=$(dirname $f); "
        "  cur=$(cat $f); "
        "  max=$(cat $dir/memory.max 2>/dev/null || echo unknown); "
        "  echo $cur $max; "
        "done'"
    )
    raw = ssh(cmd, timeout=10)
    try:
        parts = raw.split()
        current = int(parts[0])
        limit_str = parts[1]
        cur_gb = current / (1024**3)
        if limit_str == "max":
            return f"{cur_gb:.0f}GB / unlimited"
        limit = int(limit_str)
        lim_gb = limit / (1024**3)
        pct = (current / limit) * 100
        return f"{cur_gb:.0f}GB / {lim_gb:.0f}GB ({pct:.0f}%)"
    except (IndexError, ValueError):
        return raw or "unknown"


def get_oom_kills() -> str:
    raw = ssh("sudo dmesg | grep -c 'oom-kill' || echo 0")
    try:
        count = int(raw.strip())
    except ValueError:
        return "check failed"
    if count == 0:
        return "none"
    # Get kernel uptime-relative timestamp and convert to UTC
    # dmesg timestamps are seconds since boot; combine with boot time
    raw = ssh(
        "BOOT=$(date -d \"$(uptime -s)\" +%s); "
        "KERN_TS=$(sudo dmesg | grep 'oom-kill' | tail -1 | "
        "  sed 's/\\[\\s*\\([0-9.]*\\)\\].*/\\1/'); "
        "echo $BOOT $KERN_TS"
    )
    try:
        parts = raw.split()
        boot_epoch = int(parts[0])
        kern_secs = float(parts[1])
        oom_epoch = boot_epoch + int(kern_secs)
        from datetime import datetime, timezone
        oom_utc = datetime.fromtimestamp(oom_epoch, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"{count} total (last: {oom_utc})"
    except (IndexError, ValueError):
        return f"{count} total (timestamp parse failed)"


def get_relay_rate() -> str:
    # Two samples 3s apart from /proc/net/snmp
    cmd = (
        "T0=$(cat /proc/net/snmp | grep '^Udp:' | tail -1 | awk '{print $2}'); "
        "sleep 3; "
        "T1=$(cat /proc/net/snmp | grep '^Udp:' | tail -1 | awk '{print $2}'); "
        "echo $T0 $T1"
    )
    raw = ssh(cmd, timeout=15)
    try:
        parts = raw.split()
        t0, t1 = int(parts[0]), int(parts[1])
        rate = (t1 - t0) / 3
        return f"{rate:,.0f} UDP dgrams/sec (all ports)"
    except (IndexError, ValueError):
        return raw or "unknown"


def get_shreds_per_sec() -> str:
    """Count UDP packets on TVU port 9000 over 3 seconds using tcpdump."""
    cmd = "sudo timeout 3 tcpdump -i any udp dst port 9000 -q 2>&1 | grep -oP '\\d+(?= packets captured)'"
    raw = ssh(cmd, timeout=15)
    try:
        count = int(raw.strip())
        rate = count / 3
        return f"{rate:,.0f} shreds/sec ({count:,} in 3s)"
    except (ValueError, TypeError):
        return raw or "unknown"


def get_unwrap_status() -> str:
    raw = ssh("ps -p $(pgrep -f shred-unwrap | head -1) -o pid,etime,rss --no-headers 2>/dev/null || echo dead")
    if "dead" in raw or not raw.strip():
        return "NOT RUNNING"
    parts = raw.split()
    if len(parts) >= 3:
        pid, etime, rss_kb = parts[0], parts[1], parts[2]
        rss_mb = int(rss_kb) / 1024
        return f"pid={pid}  uptime={etime}  rss={rss_mb:.0f}MB"
    return raw


def get_replay_rate() -> tuple[float | None, int | None, int | None]:
    """Sample processed slot twice over 10s to measure replay rate."""
    params = [{"commitment": "processed"}]
    r0 = rpc_call("getSlot", params=params)
    s0 = r0.get("result") if r0 else None
    if s0 is None:
        return None, None, None
    t0 = time.monotonic()
    time.sleep(10)
    r1 = rpc_call("getSlot", params=params)
    s1 = r1.get("result") if r1 else None
    if s1 is None:
        return None, s0, None
    dt = time.monotonic() - t0
    rate = (s1 - s0) / dt if s1 != s0 else 0
    return rate, s0, s1


def main() -> None:
    print("=" * 60)
    print("  BISCAYNE VALIDATOR STATUS")
    print("=" * 60)

    # Health + slots
    print("\n--- RPC ---")
    health = get_health()
    local_slot, mainnet_slot = get_slots()
    print(f"  Health:       {health}")
    if local_slot is not None:
        print(f"  Local slot:   {local_slot:,}")
    else:
        print("  Local slot:   unreachable")
    if mainnet_slot is not None:
        print(f"  Mainnet slot: {mainnet_slot:,}")
    if local_slot and mainnet_slot:
        gap = mainnet_slot - local_slot
        print(f"  Gap:          {gap:,} slots")

    # Replay rate (10s sample)
    print("\n--- Replay ---")
    print("  Sampling replay rate (10s)...", end="", flush=True)
    rate, s0, s1 = get_replay_rate()
    if rate is not None:
        print(f"\r  Replay rate:  {rate:.1f} slots/sec ({s0:,} → {s1:,})")
        net = rate - 2.5
        if net > 0:
            print(f"  Net catchup:  +{net:.1f} slots/sec (gaining)")
        elif net < 0:
            print(f"  Net catchup:  {net:.1f} slots/sec (falling behind)")
        else:
            print("  Net catchup:  0 (keeping pace)")
    else:
        print("\r  Replay rate:  could not measure")

    # Pod
    print("\n--- Pod ---")
    pod = get_pod_status()
    print(f"  {pod}")

    # Memory
    print("\n--- Memory ---")
    mem = get_memory()
    print(f"  Cgroup:       {mem}")

    # OOM
    oom = get_oom_kills()
    print(f"  OOM kills:    {oom}")

    # Relay
    print("\n--- Shred Relay ---")
    unwrap = get_unwrap_status()
    print(f"  shred-unwrap: {unwrap}")
    print("  Measuring shred rate (3s)...", end="", flush=True)
    shreds = get_shreds_per_sec()
    print(f"\r  TVU shreds:   {shreds}          ")
    print("  Measuring UDP rate (3s)...", end="", flush=True)
    relay = get_relay_rate()
    print(f"\r  UDP inbound:  {relay}          ")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
