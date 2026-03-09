#!/usr/bin/env python3
"""Check agave validator and snapshot download status on biscayne.

Runs kubectl and host commands over SSH to report:
  - Pod phase and container states
  - Entrypoint logs (snapshot download progress)
  - Snapshot files on disk
  - Validator slot vs mainnet slot (gap + catch-up rate)
  - Ramdisk usage

Usage:
    scripts/check-status.py                  # one-shot
    scripts/check-status.py --watch          # repeat every 30s
    scripts/check-status.py --watch -i 10    # repeat every 10s
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request

# -- Config -------------------------------------------------------------------

SSH_HOST = "biscayne.vaasl.io"
KUBECONFIG = "/home/rix/.kube/config"
DEPLOYMENT_DIR = "/srv/deployments/agave"
SNAPSHOT_DIR = "/srv/kind/solana/snapshots"
RAMDISK = "/srv/kind/solana/ramdisk"
MAINNET_RPC = "https://api.mainnet-beta.solana.com"

# Derived from deployment.yml on first connect
CLUSTER_ID: str = ""
NAMESPACE: str = ""
DEPLOYMENT: str = ""
POD_LABEL: str = ""
KIND_CONTAINER: str = ""


# -- Discovery ----------------------------------------------------------------


def discover() -> None:
    """Read cluster-id from deployment.yml and derive all identifiers."""
    global CLUSTER_ID, NAMESPACE, DEPLOYMENT, POD_LABEL, KIND_CONTAINER
    rc, out = ssh(
        f"grep '^cluster-id:' {DEPLOYMENT_DIR}/deployment.yml "
        "| awk '{print $2}'"
    )
    if rc != 0 or not out:
        print(f"ERROR: cannot read cluster-id from {DEPLOYMENT_DIR}/deployment.yml")
        sys.exit(1)
    CLUSTER_ID = out.strip()
    NAMESPACE = f"laconic-{CLUSTER_ID}"
    DEPLOYMENT = f"{CLUSTER_ID}-deployment"
    POD_LABEL = CLUSTER_ID
    KIND_CONTAINER = f"{CLUSTER_ID}-control-plane"


# -- Helpers ------------------------------------------------------------------


def ssh(cmd: str, timeout: int = 15) -> tuple[int, str]:
    """Run a command on biscayne via SSH. Returns (rc, stdout)."""
    r = subprocess.run(
        ["ssh", SSH_HOST, cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.returncode, r.stdout.strip()


def kubectl(args: str, timeout: int = 15) -> tuple[int, str]:
    """Run kubectl on biscayne."""
    return ssh(f"KUBECONFIG={KUBECONFIG} kubectl {args}", timeout)


def get_mainnet_slot() -> int | None:
    """Query mainnet for current finalized slot."""
    req = urllib.request.Request(
        MAINNET_RPC,
        data=json.dumps({
            "jsonrpc": "2.0", "id": 1,
            "method": "getSlot",
            "params": [{"commitment": "finalized"}],
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())["result"]
    except Exception:
        return None


# -- Checks -------------------------------------------------------------------


def check_pod() -> dict:
    """Get pod phase and container statuses."""
    rc, out = kubectl(
        f"get pods -n {NAMESPACE} -l app={POD_LABEL} "
        "-o json"
    )
    if rc != 0 or not out:
        return {"phase": "NoPod", "containers": {}}

    data = json.loads(out)
    if not data.get("items"):
        return {"phase": "NoPod", "containers": {}}

    pod = data["items"][0]
    phase = pod["status"].get("phase", "Unknown")
    containers = {}
    for cs in pod["status"].get("containerStatuses", []):
        state_key = list(cs["state"].keys())[0]
        state = cs["state"][state_key]
        reason = state.get("reason", "")
        detail = f"{state_key}"
        if reason:
            detail += f"({reason})"
        containers[cs["name"]] = {
            "ready": cs["ready"],
            "state": detail,
            "restarts": cs["restartCount"],
        }
    return {"phase": phase, "containers": containers}


def check_entrypoint_logs(lines: int = 15) -> str:
    """Get recent entrypoint logs from the agave-validator container."""
    rc, out = kubectl(
        f"logs -n {NAMESPACE} deployment/{DEPLOYMENT} "
        f"-c agave-validator --tail={lines}",
        timeout=20,
    )
    return out if rc == 0 else "(no logs)"


def check_snapshots() -> list[dict]:
    """List snapshot files on disk with sizes."""
    rc, out = ssh(
        f"ls -lhS {SNAPSHOT_DIR}/*.tar.* 2>/dev/null "
        f"|| echo 'NO_SNAPSHOTS'"
    )
    if "NO_SNAPSHOTS" in out:
        return []

    files = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 9:
            files.append({"size": parts[4], "name": parts[-1].split("/")[-1]})
    return files


def check_validator_slot() -> int | None:
    """Query the validator's current processed slot via RPC."""
    rc, out = kubectl(
        f"exec -n {NAMESPACE} deployment/{DEPLOYMENT} "
        f"-c agave-validator -- "
        "curl -s -X POST -H 'Content-Type: application/json' "
        "-d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getSlot\","
        "\"params\":[{\"commitment\":\"processed\"}]}' "
        "http://localhost:8899",
        timeout=10,
    )
    if rc != 0 or not out:
        return None
    try:
        return json.loads(out)["result"]
    except (json.JSONDecodeError, KeyError):
        return None


def check_ramdisk() -> str:
    """Get ramdisk usage."""
    rc, out = ssh(f"df -h {RAMDISK} | tail -1")
    if rc != 0:
        return "unknown"
    parts = out.split()
    if len(parts) >= 5:
        return f"{parts[2]}/{parts[1]} ({parts[4]})"
    return out


# -- Display ------------------------------------------------------------------


prev_slot: int | None = None
prev_time: float | None = None


def display(iteration: int = 0) -> None:
    """Run all checks and print status."""
    global prev_slot, prev_time

    now = time.time()
    ts = time.strftime("%H:%M:%S")

    # Gather data
    pod = check_pod()
    mainnet = get_mainnet_slot()
    snapshots = check_snapshots()
    ramdisk = check_ramdisk()

    print(f"\n{'=' * 60}")
    print(f"  Biscayne Agave Status — {ts}")
    print(f"{'=' * 60}")

    # Pod
    print(f"\n  Pod: {pod['phase']}")
    for name, cs in pod["containers"].items():
        ready = "✓" if cs["ready"] else "✗"
        restarts = f" (restarts: {cs['restarts']})" if cs["restarts"] > 0 else ""
        print(f"    {ready} {name}: {cs['state']}{restarts}")

    # Validator slot
    validator_slot = None
    if pod["phase"] == "Running":
        agave = pod["containers"].get("agave-validator", {})
        if agave.get("ready"):
            validator_slot = check_validator_slot()

    if validator_slot is not None and mainnet is not None:
        gap = mainnet - validator_slot
        rate = ""
        if prev_slot is not None and prev_time is not None:
            dt = now - prev_time
            if dt > 0:
                slots_gained = validator_slot - prev_slot
                # Net rate = our replay rate minus chain production
                net_rate = slots_gained / dt
                if net_rate > 0:
                    eta_sec = gap / net_rate
                    eta_min = eta_sec / 60
                    rate = f"  net {net_rate:+.1f} slots/s, ETA ~{eta_min:.0f}m"
                else:
                    rate = f"  net {net_rate:+.1f} slots/s (falling behind)"
        prev_slot = validator_slot
        prev_time = now
        print(f"\n  Validator: slot {validator_slot:,}")
        print(f"  Mainnet:   slot {mainnet:,}")
        print(f"  Gap:       {gap:,} slots{rate}")
    elif mainnet is not None:
        print(f"\n  Validator: not responding (downloading or starting)")
        print(f"  Mainnet:   slot {mainnet:,}")
    else:
        print(f"\n  Mainnet:   unreachable")

    # Snapshots
    if snapshots:
        print(f"\n  Snapshots:")
        for s in snapshots:
            print(f"    {s['size']:>6s}  {s['name']}")
    else:
        print(f"\n  Snapshots: none on disk")

    # Ramdisk
    print(f"  Ramdisk:   {ramdisk}")

    # Entrypoint logs (only if validator not yet responding)
    if validator_slot is None and pod["phase"] in ("Running", "Pending"):
        logs = check_entrypoint_logs(10)
        if logs and logs != "(no logs)":
            print(f"\n  Entrypoint logs (last 10 lines):")
            for line in logs.splitlines():
                print(f"    {line}")

    print()


# -- Main ---------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--watch", action="store_true", help="Repeat every interval")
    p.add_argument("-i", "--interval", type=int, default=30,
                   help="Watch interval in seconds (default: 30)")
    args = p.parse_args()

    discover()

    try:
        if args.watch:
            i = 0
            while True:
                display(i)
                i += 1
                time.sleep(args.interval)
        else:
            display()
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
