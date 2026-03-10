#!/usr/bin/env python3
"""Agave validator entrypoint — snapshot management, arg construction, liveness probe.

Two subcommands:
  entrypoint.py serve   (default) — snapshot freshness check + run agave-validator
  entrypoint.py probe   — liveness probe (slot lag check, exits 0/1)

Replaces the bash entrypoint.sh / start-rpc.sh / start-validator.sh with a single
Python module. Test mode still dispatches to start-test.sh.

Python stays as PID 1 and traps SIGTERM. On SIGTERM, it runs
``agave-validator exit --force --ledger /data/ledger`` which connects to the
admin RPC Unix socket and tells the validator to flush I/O and exit cleanly.
This avoids the io_uring/ZFS deadlock that occurs when the process is killed.

All configuration comes from environment variables — same vars as the original
bash scripts. See compose files for defaults.
"""

from __future__ import annotations

import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.request import Request

log: logging.Logger = logging.getLogger("entrypoint")

# Directories
CONFIG_DIR = "/data/config"
LEDGER_DIR = "/data/ledger"
ACCOUNTS_DIR = "/data/accounts"
SNAPSHOTS_DIR = "/data/snapshots"
LOG_DIR = "/data/log"
IDENTITY_FILE = f"{CONFIG_DIR}/validator-identity.json"

# Snapshot filename patterns
FULL_SNAP_RE: re.Pattern[str] = re.compile(
    r"^snapshot-(\d+)-[A-Za-z0-9]+\.tar\.(zst|bz2)$"
)
INCR_SNAP_RE: re.Pattern[str] = re.compile(
    r"^incremental-snapshot-(\d+)-(\d+)-[A-Za-z0-9]+\.tar\.(zst|bz2)$"
)

MAINNET_RPC = "https://api.mainnet-beta.solana.com"


# -- Helpers -------------------------------------------------------------------


def env(name: str, default: str = "") -> str:
    """Read env var with default."""
    return os.environ.get(name, default)


def env_required(name: str) -> str:
    """Read required env var, exit if missing."""
    val = os.environ.get(name)
    if not val:
        log.error("%s is required but not set", name)
        sys.exit(1)
    return val


def env_bool(name: str, default: bool = False) -> bool:
    """Read boolean env var (true/false/1/0)."""
    val = os.environ.get(name, "").lower()
    if not val:
        return default
    return val in ("true", "1", "yes")


def rpc_get_slot(url: str, timeout: int = 10) -> int | None:
    """Get current slot from a Solana RPC endpoint."""
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "getSlot", "params": [],
    }).encode()
    req = Request(url, data=payload,
                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            result = data.get("result")
            if isinstance(result, int):
                return result
    except (urllib.error.URLError, json.JSONDecodeError, OSError, TimeoutError):
        pass
    return None


# -- Snapshot management -------------------------------------------------------


def get_local_snapshot_slot(snapshots_dir: str) -> int | None:
    """Find the highest slot among local snapshot files."""
    best_slot: int | None = None
    snap_path = Path(snapshots_dir)
    if not snap_path.is_dir():
        return None
    for entry in snap_path.iterdir():
        m = FULL_SNAP_RE.match(entry.name)
        if m:
            slot = int(m.group(1))
            if best_slot is None or slot > best_slot:
                best_slot = slot
    return best_slot


def clean_snapshots(snapshots_dir: str) -> None:
    """Remove all snapshot files from the directory."""
    snap_path = Path(snapshots_dir)
    if not snap_path.is_dir():
        return
    for entry in snap_path.iterdir():
        if entry.name.startswith(("snapshot-", "incremental-snapshot-")):
            log.info("Removing old snapshot: %s", entry.name)
            entry.unlink(missing_ok=True)


def get_incremental_slot(snapshots_dir: str, full_slot: int | None) -> int | None:
    """Get the highest incremental snapshot slot matching the full's base slot."""
    if full_slot is None:
        return None
    snap_path = Path(snapshots_dir)
    if not snap_path.is_dir():
        return None
    best: int | None = None
    for entry in snap_path.iterdir():
        m = INCR_SNAP_RE.match(entry.name)
        if m and int(m.group(1)) == full_slot:
            slot = int(m.group(2))
            if best is None or slot > best:
                best = slot
    return best


def maybe_download_snapshot(snapshots_dir: str) -> None:
    """Ensure full + incremental snapshots exist before starting.

    The validator should always start from a full + incremental pair to
    minimize replay time. If either is missing or the full is too old,
    download fresh ones via download_best_snapshot (which does rolling
    incremental convergence after downloading the full).

    Controlled by env vars:
      SNAPSHOT_AUTO_DOWNLOAD (default: true) — enable/disable
      SNAPSHOT_MAX_AGE_SLOTS (default: 100000) — full snapshot staleness threshold
        (one full snapshot generation, ~11 hours)
    """
    if not env_bool("SNAPSHOT_AUTO_DOWNLOAD", default=True):
        log.info("Snapshot auto-download disabled")
        return

    max_age = int(env("SNAPSHOT_MAX_AGE_SLOTS", "100000"))

    mainnet_slot = rpc_get_slot(MAINNET_RPC)
    if mainnet_slot is None:
        log.warning("Cannot reach mainnet RPC — skipping snapshot check")
        return

    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))
    from snapshot_download import download_best_snapshot, download_incremental_for_slot

    convergence = int(env("SNAPSHOT_CONVERGENCE_SLOTS", "500"))
    retry_delay = int(env("SNAPSHOT_RETRY_DELAY", "60"))

    # Check local full snapshot
    local_slot = get_local_snapshot_slot(snapshots_dir)
    have_fresh_full = (local_slot is not None
                       and (mainnet_slot - local_slot) <= max_age)

    if have_fresh_full:
        assert local_slot is not None
        inc_slot = get_incremental_slot(snapshots_dir, local_slot)
        if inc_slot is not None:
            inc_gap = mainnet_slot - inc_slot
            if inc_gap <= convergence:
                log.info("Full (slot %d) + incremental (slot %d, gap %d) "
                         "within convergence, starting",
                         local_slot, inc_slot, inc_gap)
                return
            log.info("Incremental too stale (slot %d, gap %d > %d)",
                     inc_slot, inc_gap, convergence)
        # Fresh full, need a fresh incremental
        log.info("Downloading incremental for full at slot %d", local_slot)
        while True:
            if download_incremental_for_slot(snapshots_dir, local_slot,
                                             convergence_slots=convergence):
                return
            log.warning("Incremental download failed — retrying in %ds",
                        retry_delay)
            time.sleep(retry_delay)

    # No full or full too old — download both
    log.info("Downloading full + incremental")
    clean_snapshots(snapshots_dir)
    while True:
        if download_best_snapshot(snapshots_dir, convergence_slots=convergence):
            return
        log.warning("Snapshot download failed — retrying in %ds", retry_delay)
        time.sleep(retry_delay)


# -- Directory and identity setup ----------------------------------------------


def ensure_dirs(*dirs: str) -> None:
    """Create directories and fix ownership."""
    uid = os.getuid()
    gid = os.getgid()
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        try:
            subprocess.run(
                ["sudo", "chown", "-R", f"{uid}:{gid}", d],
                check=False, capture_output=True,
            )
        except FileNotFoundError:
            pass  # sudo not available — dirs already owned correctly


def ensure_identity_rpc() -> None:
    """Generate ephemeral identity keypair for RPC mode if not mounted."""
    if os.path.isfile(IDENTITY_FILE):
        return
    log.info("Generating RPC node identity keypair...")
    subprocess.run(
        ["solana-keygen", "new", "--no-passphrase", "--silent",
         "--force", "--outfile", IDENTITY_FILE],
        check=True,
    )


def print_identity() -> None:
    """Print the node identity pubkey."""
    result = subprocess.run(
        ["solana-keygen", "pubkey", IDENTITY_FILE],
        capture_output=True, text=True, check=False,
    )
    if result.returncode == 0:
        log.info("Node identity: %s", result.stdout.strip())


# -- Arg construction ----------------------------------------------------------


def build_common_args() -> list[str]:
    """Build agave-validator args common to both RPC and validator modes."""
    args: list[str] = [
        "--identity", IDENTITY_FILE,
        "--entrypoint", env_required("VALIDATOR_ENTRYPOINT"),
        "--known-validator", env_required("KNOWN_VALIDATOR"),
        "--ledger", LEDGER_DIR,
        "--accounts", ACCOUNTS_DIR,
        "--snapshots", SNAPSHOTS_DIR,
        "--rpc-port", env("RPC_PORT", "8899"),
        "--rpc-bind-address", env("RPC_BIND_ADDRESS", "127.0.0.1"),
        "--gossip-port", env("GOSSIP_PORT", "8001"),
        "--dynamic-port-range", env("DYNAMIC_PORT_RANGE", "9000-10000"),
        "--no-os-network-limits-test",
        "--wal-recovery-mode", "skip_any_corrupted_record",
        "--limit-ledger-size", env("LIMIT_LEDGER_SIZE", "50000000"),
        "--no-snapshot-fetch",  # entrypoint handles snapshot download
    ]

    # Snapshot generation
    if env("NO_SNAPSHOTS") == "true":
        args.append("--no-snapshots")
    else:
        args += [
            "--full-snapshot-interval-slots", env("SNAPSHOT_INTERVAL_SLOTS", "100000"),
            "--maximum-full-snapshots-to-retain", env("MAXIMUM_SNAPSHOTS_TO_RETAIN", "1"),
        ]
        if env("NO_INCREMENTAL_SNAPSHOTS") != "true":
            args += ["--maximum-incremental-snapshots-to-retain", "2"]

    # Account indexes
    account_indexes = env("ACCOUNT_INDEXES")
    if account_indexes:
        for idx in account_indexes.split(","):
            idx = idx.strip()
            if idx:
                args += ["--account-index", idx]

    # Additional entrypoints
    for ep in env("EXTRA_ENTRYPOINTS").split():
        if ep:
            args += ["--entrypoint", ep]

    # Additional known validators
    for kv in env("EXTRA_KNOWN_VALIDATORS").split():
        if kv:
            args += ["--known-validator", kv]

    # Cluster verification
    genesis_hash = env("EXPECTED_GENESIS_HASH")
    if genesis_hash:
        args += ["--expected-genesis-hash", genesis_hash]
    shred_version = env("EXPECTED_SHRED_VERSION")
    if shred_version:
        args += ["--expected-shred-version", shred_version]

    # Metrics — just needs to be in the environment, agave reads it directly
    # (env var is already set, nothing to pass as arg)

    # Gossip host / TVU address
    gossip_host = env("GOSSIP_HOST")
    if gossip_host:
        args += ["--gossip-host", gossip_host]
    elif env("PUBLIC_TVU_ADDRESS"):
        args += ["--public-tvu-address", env("PUBLIC_TVU_ADDRESS")]

    # Jito flags
    if env("JITO_ENABLE") == "true":
        log.info("Jito MEV enabled")
        jito_flags: list[tuple[str, str]] = [
            ("JITO_TIP_PAYMENT_PROGRAM", "--tip-payment-program-pubkey"),
            ("JITO_DISTRIBUTION_PROGRAM", "--tip-distribution-program-pubkey"),
            ("JITO_MERKLE_ROOT_AUTHORITY", "--merkle-root-upload-authority"),
            ("JITO_COMMISSION_BPS", "--commission-bps"),
            ("JITO_BLOCK_ENGINE_URL", "--block-engine-url"),
            ("JITO_SHRED_RECEIVER_ADDR", "--shred-receiver-address"),
        ]
        for env_name, flag in jito_flags:
            val = env(env_name)
            if val:
                args += [flag, val]

    return args


def build_rpc_args() -> list[str]:
    """Build agave-validator args for RPC (non-voting) mode."""
    args = build_common_args()
    args += [
        "--no-voting",
        "--log", f"{LOG_DIR}/validator.log",
        "--full-rpc-api",
        "--enable-rpc-transaction-history",
        "--rpc-pubsub-enable-block-subscription",
        "--enable-extended-tx-metadata-storage",
        "--no-wait-for-vote-to-start-leader",
    ]

    # Public vs private RPC
    public_rpc = env("PUBLIC_RPC_ADDRESS")
    if public_rpc:
        args += ["--public-rpc-address", public_rpc]
    else:
        args += ["--private-rpc", "--allow-private-addr", "--only-known-rpc"]

    # Jito relayer URL (RPC mode doesn't use it, but validator mode does —
    # handled in build_validator_args)

    return args


def build_validator_args() -> list[str]:
    """Build agave-validator args for voting validator mode."""
    vote_keypair = env("VOTE_ACCOUNT_KEYPAIR",
                       "/data/config/vote-account-keypair.json")

    # Identity must be mounted for validator mode
    if not os.path.isfile(IDENTITY_FILE):
        log.error("Validator identity keypair not found at %s", IDENTITY_FILE)
        log.error("Mount your validator keypair to %s", IDENTITY_FILE)
        sys.exit(1)

    # Vote account keypair must exist
    if not os.path.isfile(vote_keypair):
        log.error("Vote account keypair not found at %s", vote_keypair)
        log.error("Mount your vote account keypair or set VOTE_ACCOUNT_KEYPAIR")
        sys.exit(1)

    # Print vote account pubkey
    result = subprocess.run(
        ["solana-keygen", "pubkey", vote_keypair],
        capture_output=True, text=True, check=False,
    )
    if result.returncode == 0:
        log.info("Vote account: %s", result.stdout.strip())

    args = build_common_args()
    args += [
        "--vote-account", vote_keypair,
        "--log", "-",
    ]

    # Jito relayer URL (validator-only)
    relayer_url = env("JITO_RELAYER_URL")
    if env("JITO_ENABLE") == "true" and relayer_url:
        args += ["--relayer-url", relayer_url]

    return args


def append_extra_args(args: list[str]) -> list[str]:
    """Append EXTRA_ARGS passthrough flags."""
    extra = env("EXTRA_ARGS")
    if extra:
        args += extra.split()
    return args


# -- Graceful shutdown --------------------------------------------------------

# Timeout for graceful exit via admin RPC. Leave 30s margin for k8s
# terminationGracePeriodSeconds (300s).
GRACEFUL_EXIT_TIMEOUT = 270


def graceful_exit(child: subprocess.Popen[bytes], reason: str = "SIGTERM") -> None:
    """Request graceful shutdown via the admin RPC Unix socket.

    Runs ``agave-validator exit --force --ledger /data/ledger`` which connects
    to the admin RPC socket at ``/data/ledger/admin.rpc`` and sets the
    validator's exit flag. The validator flushes all I/O and exits cleanly,
    avoiding the io_uring/ZFS deadlock.

    If the admin RPC exit fails or the child doesn't exit within the timeout,
    falls back to SIGTERM then SIGKILL.
    """
    log.info("%s — requesting graceful exit via admin RPC", reason)
    try:
        result = subprocess.run(
            ["agave-validator", "exit", "--force", "--ledger", LEDGER_DIR],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            log.info("Admin RPC exit requested successfully")
        else:
            log.warning(
                "Admin RPC exit returned %d: %s",
                result.returncode, result.stderr.strip(),
            )
    except subprocess.TimeoutExpired:
        log.warning("Admin RPC exit command timed out after 30s")
    except FileNotFoundError:
        log.warning("agave-validator binary not found for exit command")

    # Wait for child to exit
    try:
        child.wait(timeout=GRACEFUL_EXIT_TIMEOUT)
        log.info("Validator exited cleanly with code %d", child.returncode)
        return
    except subprocess.TimeoutExpired:
        log.warning(
            "Validator did not exit within %ds — sending SIGTERM",
            GRACEFUL_EXIT_TIMEOUT,
        )

    # Fallback: SIGTERM
    child.terminate()
    try:
        child.wait(timeout=15)
        log.info("Validator exited after SIGTERM with code %d", child.returncode)
        return
    except subprocess.TimeoutExpired:
        log.warning("Validator did not exit after SIGTERM — sending SIGKILL")

    # Last resort: SIGKILL
    child.kill()
    child.wait()
    log.info("Validator killed with SIGKILL, code %d", child.returncode)


# -- Serve subcommand ---------------------------------------------------------


def _gap_monitor(
    child: subprocess.Popen[bytes],
    leapfrog: threading.Event,
    shutting_down: threading.Event,
) -> None:
    """Background thread: poll slot gap and trigger leapfrog if too far behind.

    Waits for a grace period (SNAPSHOT_MONITOR_GRACE, default 600s) before
    monitoring — the validator needs time to extract snapshots and catch up.
    Then polls every SNAPSHOT_MONITOR_INTERVAL (default 30s). If the gap
    exceeds SNAPSHOT_LEAPFROG_SLOTS (default 5000) for SNAPSHOT_LEAPFROG_CHECKS
    (default 3) consecutive checks, triggers graceful shutdown and sets the
    leapfrog event so cmd_serve loops back to download a fresh incremental.
    """
    threshold = int(env("SNAPSHOT_LEAPFROG_SLOTS", "5000"))
    required_checks = int(env("SNAPSHOT_LEAPFROG_CHECKS", "3"))
    interval = int(env("SNAPSHOT_MONITOR_INTERVAL", "30"))
    grace = int(env("SNAPSHOT_MONITOR_GRACE", "600"))
    rpc_port = env("RPC_PORT", "8899")
    local_url = f"http://127.0.0.1:{rpc_port}"

    # Grace period — don't monitor during initial catch-up
    if shutting_down.wait(grace):
        return

    consecutive = 0
    while not shutting_down.is_set():
        local_slot = rpc_get_slot(local_url, timeout=5)
        mainnet_slot = rpc_get_slot(MAINNET_RPC, timeout=10)

        if local_slot is not None and mainnet_slot is not None:
            gap = mainnet_slot - local_slot
            if gap > threshold:
                consecutive += 1
                log.warning("Gap %d > %d (%d/%d consecutive)",
                            gap, threshold, consecutive, required_checks)
                if consecutive >= required_checks:
                    log.warning("Leapfrog triggered: gap %d", gap)
                    leapfrog.set()
                    graceful_exit(child, reason="Leapfrog")
                    return
            else:
                if consecutive > 0:
                    log.info("Gap %d within threshold, resetting counter", gap)
                consecutive = 0

        shutting_down.wait(interval)


def cmd_serve() -> None:
    """Main serve flow: snapshot download, run validator, monitor gap, leapfrog.

    Python stays as PID 1. On each iteration:
      1. Download full + incremental snapshots (if needed)
      2. Start agave-validator as child process
      3. Monitor slot gap in background thread
      4. If gap exceeds threshold → graceful stop → loop back to step 1
      5. If SIGTERM → graceful stop → exit
      6. If validator crashes → exit with its return code
    """
    mode = env("AGAVE_MODE", "test")
    log.info("AGAVE_MODE=%s", mode)

    if mode == "test":
        os.execvp("start-test.sh", ["start-test.sh"])

    if mode not in ("rpc", "validator"):
        log.error("Unknown AGAVE_MODE: %s (valid: test, rpc, validator)", mode)
        sys.exit(1)

    # One-time setup
    dirs = [CONFIG_DIR, LEDGER_DIR, ACCOUNTS_DIR, SNAPSHOTS_DIR]
    if mode == "rpc":
        dirs.append(LOG_DIR)
    ensure_dirs(*dirs)

    if not env_bool("SKIP_IP_ECHO_PREFLIGHT"):
        script_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(script_dir))
        from ip_echo_preflight import main as ip_echo_main
        if ip_echo_main() != 0:
            sys.exit(1)

    if mode == "rpc":
        ensure_identity_rpc()
    print_identity()

    if mode == "rpc":
        args = build_rpc_args()
    else:
        args = build_validator_args()
    args = append_extra_args(args)

    # Main loop: download → run → monitor → leapfrog if needed
    while True:
        maybe_download_snapshot(SNAPSHOTS_DIR)

        Path("/tmp/entrypoint-start").write_text(str(time.time()))
        log.info("Starting agave-validator with %d arguments", len(args))
        child = subprocess.Popen(["agave-validator"] + args)

        shutting_down = threading.Event()
        leapfrog = threading.Event()

        signal.signal(signal.SIGUSR1,
                      lambda _sig, _frame: child.send_signal(signal.SIGUSR1))

        def _on_sigterm(_sig: int, _frame: object) -> None:
            shutting_down.set()
            threading.Thread(
                target=graceful_exit, args=(child,), daemon=True,
            ).start()

        signal.signal(signal.SIGTERM, _on_sigterm)

        # Start gap monitor
        monitor = threading.Thread(
            target=_gap_monitor,
            args=(child, leapfrog, shutting_down),
            daemon=True,
        )
        monitor.start()

        child.wait()

        if leapfrog.is_set():
            log.info("Leapfrog: restarting with fresh incremental")
            continue

        sys.exit(child.returncode)


# -- Probe subcommand ---------------------------------------------------------


def cmd_probe() -> None:
    """Liveness probe: check local RPC slot vs mainnet.

    Exit 0 = healthy, exit 1 = unhealthy.

    Grace period: PROBE_GRACE_SECONDS (default 600) — probe always passes
    during grace period to allow for snapshot unpacking and initial replay.
    """
    grace_seconds = int(env("PROBE_GRACE_SECONDS", "600"))
    max_lag = int(env("PROBE_MAX_SLOT_LAG", "20000"))

    # Check grace period
    start_file = Path("/tmp/entrypoint-start")
    if start_file.exists():
        try:
            start_time = float(start_file.read_text().strip())
            elapsed = time.time() - start_time
            if elapsed < grace_seconds:
                # Within grace period — always healthy
                sys.exit(0)
        except (ValueError, OSError):
            pass
    else:
        # No start file — serve hasn't started yet, within grace
        sys.exit(0)

    # Query local RPC
    rpc_port = env("RPC_PORT", "8899")
    local_url = f"http://127.0.0.1:{rpc_port}"
    local_slot = rpc_get_slot(local_url, timeout=5)
    if local_slot is None:
        # Local RPC unreachable after grace period — unhealthy
        sys.exit(1)

    # Query mainnet
    mainnet_slot = rpc_get_slot(MAINNET_RPC, timeout=10)
    if mainnet_slot is None:
        # Can't reach mainnet to compare — assume healthy (don't penalize
        # the validator for mainnet RPC being down)
        sys.exit(0)

    lag = mainnet_slot - local_slot
    if lag > max_lag:
        sys.exit(1)

    sys.exit(0)


# -- Main ----------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    subcmd = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if subcmd == "serve":
        cmd_serve()
    elif subcmd == "probe":
        cmd_probe()
    else:
        log.error("Unknown subcommand: %s (valid: serve, probe)", subcmd)
        sys.exit(1)


if __name__ == "__main__":
    main()
