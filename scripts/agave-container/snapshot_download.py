#!/usr/bin/env python3
"""Download Solana snapshots using aria2c for parallel multi-connection downloads.

Discovers snapshot sources by querying getClusterNodes for all RPCs in the
cluster, probing each for available snapshots, benchmarking download speed,
and downloading from the fastest source using aria2c (16 connections by default).

Based on the discovery approach from etcusr/solana-snapshot-finder but replaces
the single-connection wget download with aria2c parallel chunked downloads.

Usage:
    # Download to /srv/kind/solana/snapshots (mainnet, 16 connections)
    ./snapshot_download.py -o /srv/kind/solana/snapshots

    # Dry run — find best source, print URL
    ./snapshot_download.py --dry-run

    # Custom RPC for cluster discovery + 32 connections
    ./snapshot_download.py -r https://api.mainnet-beta.solana.com -n 32

    # Testnet
    ./snapshot_download.py -c testnet -o /data/snapshots

    # Programmatic use from entrypoint.py:
    from snapshot_download import download_best_snapshot
    ok = download_best_snapshot("/data/snapshots")

Requirements:
    - aria2c (apt install aria2)
    - python3 >= 3.10 (stdlib only, no pip dependencies)
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http.client import HTTPResponse
from pathlib import Path
from urllib.request import Request

log: logging.Logger = logging.getLogger("snapshot-download")

CLUSTER_RPC: dict[str, str] = {
    "mainnet-beta": "https://api.mainnet-beta.solana.com",
    "testnet": "https://api.testnet.solana.com",
    "devnet": "https://api.devnet.solana.com",
}

# Snapshot filenames:
#   snapshot-<slot>-<hash>.tar.zst
#   incremental-snapshot-<base_slot>-<slot>-<hash>.tar.zst
FULL_SNAP_RE: re.Pattern[str] = re.compile(
    r"^snapshot-(\d+)-([A-Za-z0-9]+)\.tar\.(zst|bz2)$"
)
INCR_SNAP_RE: re.Pattern[str] = re.compile(
    r"^incremental-snapshot-(\d+)-(\d+)-([A-Za-z0-9]+)\.tar\.(zst|bz2)$"
)


@dataclass
class SnapshotSource:
    """A snapshot file available from a specific RPC node."""

    rpc_address: str
    # Full redirect paths as returned by the server (e.g. /snapshot-123-hash.tar.zst)
    file_paths: list[str] = field(default_factory=list)
    slots_diff: int = 0
    latency_ms: float = 0.0
    download_speed: float = 0.0  # bytes/sec


# -- JSON-RPC helpers ----------------------------------------------------------


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Handler that captures redirect Location instead of following it."""

    def redirect_request(
        self,
        req: Request,
        fp: HTTPResponse,
        code: int,
        msg: str,
        headers: dict[str, str],  # type: ignore[override]
        newurl: str,
    ) -> None:
        return None


def rpc_post(url: str, method: str, params: list[object] | None = None,
             timeout: int = 25) -> object | None:
    """JSON-RPC POST. Returns parsed 'result' field or None on error."""
    payload: bytes = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": method, "params": params or [],
    }).encode()
    req = Request(url, data=payload,
                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data: dict[str, object] = json.loads(resp.read())
            return data.get("result")
    except (urllib.error.URLError, json.JSONDecodeError, OSError, TimeoutError) as e:
        log.debug("rpc_post %s %s failed: %s", url, method, e)
        return None


def head_no_follow(url: str, timeout: float = 3) -> tuple[str | None, float]:
    """HEAD request without following redirects.

    Returns (Location header value, latency_sec) if the server returned a
    3xx redirect. Returns (None, 0.0) on any error or non-redirect response.
    """
    opener: urllib.request.OpenerDirector = urllib.request.build_opener(_NoRedirectHandler)
    req = Request(url, method="HEAD")
    try:
        start: float = time.monotonic()
        resp: HTTPResponse = opener.open(req, timeout=timeout)  # type: ignore[assignment]
        latency: float = time.monotonic() - start
        # Non-redirect (2xx) — server didn't redirect, not useful for discovery
        location: str | None = resp.headers.get("Location")
        resp.close()
        return location, latency
    except urllib.error.HTTPError as e:
        # 3xx redirects raise HTTPError with the redirect info
        latency = time.monotonic() - start  # type: ignore[possibly-undefined]
        location = e.headers.get("Location")
        if location and 300 <= e.code < 400:
            return location, latency
        return None, 0.0
    except (urllib.error.URLError, OSError, TimeoutError):
        return None, 0.0


# -- Discovery -----------------------------------------------------------------


def get_current_slot(rpc_url: str) -> int | None:
    """Get current slot from RPC."""
    result: object | None = rpc_post(rpc_url, "getSlot")
    if isinstance(result, int):
        return result
    return None


def get_cluster_rpc_nodes(rpc_url: str, version_filter: str | None = None) -> list[str]:
    """Get all RPC node addresses from getClusterNodes."""
    result: object | None = rpc_post(rpc_url, "getClusterNodes")
    if not isinstance(result, list):
        return []

    rpc_addrs: list[str] = []
    for node in result:
        if not isinstance(node, dict):
            continue
        if version_filter is not None:
            node_version: str | None = node.get("version")
            if node_version and not node_version.startswith(version_filter):
                continue
        rpc: str | None = node.get("rpc")
        if rpc:
            rpc_addrs.append(rpc)
    return list(set(rpc_addrs))


def _parse_snapshot_filename(location: str) -> tuple[str, str | None]:
    """Extract filename and full redirect path from Location header.

    Returns (filename, full_path). full_path includes any path prefix
    the server returned (e.g. '/snapshots/snapshot-123-hash.tar.zst').
    """
    # Location may be absolute URL or relative path
    if location.startswith("http://") or location.startswith("https://"):
        # Absolute URL — extract path
        from urllib.parse import urlparse
        path: str = urlparse(location).path
    else:
        path = location

    filename: str = path.rsplit("/", 1)[-1]
    return filename, path


def probe_rpc_snapshot(
    rpc_address: str,
    current_slot: int,
) -> SnapshotSource | None:
    """Probe a single RPC node for available snapshots.

    Discovery only — no filtering. Returns a SnapshotSource with all available
    info so the caller can decide what to keep. Filtering happens after all
    probes complete, so rejected sources are still visible for debugging.
    """
    full_url: str = f"http://{rpc_address}/snapshot.tar.bz2"

    # Full snapshot is required — every source must have one
    full_location, full_latency = head_no_follow(full_url, timeout=2)
    if not full_location:
        return None

    latency_ms: float = full_latency * 1000

    full_filename, full_path = _parse_snapshot_filename(full_location)
    fm: re.Match[str] | None = FULL_SNAP_RE.match(full_filename)
    if not fm:
        return None

    full_snap_slot: int = int(fm.group(1))
    slots_diff: int = current_slot - full_snap_slot

    file_paths: list[str] = [full_path]

    # Also check for incremental snapshot
    inc_url: str = f"http://{rpc_address}/incremental-snapshot.tar.bz2"
    inc_location, _ = head_no_follow(inc_url, timeout=2)
    if inc_location:
        inc_filename, inc_path = _parse_snapshot_filename(inc_location)
        m: re.Match[str] | None = INCR_SNAP_RE.match(inc_filename)
        if m:
            inc_base_slot: int = int(m.group(1))
            # Incremental must be based on this source's full snapshot
            if inc_base_slot == full_snap_slot:
                file_paths.append(inc_path)

    return SnapshotSource(
        rpc_address=rpc_address,
        file_paths=file_paths,
        slots_diff=slots_diff,
        latency_ms=latency_ms,
    )


def discover_sources(
    rpc_url: str,
    current_slot: int,
    max_age_slots: int,
    max_latency_ms: float,
    threads: int,
    version_filter: str | None,
) -> list[SnapshotSource]:
    """Discover all snapshot sources, then filter.

    Probing and filtering are separate: all reachable sources are collected
    first so we can report what exists even if filters reject everything.
    """
    rpc_nodes: list[str] = get_cluster_rpc_nodes(rpc_url, version_filter)
    if not rpc_nodes:
        log.error("No RPC nodes found via getClusterNodes")
        return []

    log.info("Found %d RPC nodes, probing for snapshots...", len(rpc_nodes))

    all_sources: list[SnapshotSource] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as pool:
        futures: dict[concurrent.futures.Future[SnapshotSource | None], str] = {
            pool.submit(probe_rpc_snapshot, addr, current_slot): addr
            for addr in rpc_nodes
        }
        done: int = 0
        for future in concurrent.futures.as_completed(futures):
            done += 1
            if done % 200 == 0:
                log.info("  probed %d/%d nodes, %d reachable",
                         done, len(rpc_nodes), len(all_sources))
            try:
                result: SnapshotSource | None = future.result()
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                log.debug("Probe failed for %s: %s", futures[future], e)
                continue
            if result:
                all_sources.append(result)

    log.info("Discovered %d reachable sources", len(all_sources))

    # Apply filters
    filtered: list[SnapshotSource] = []
    rejected_age: int = 0
    rejected_latency: int = 0
    for src in all_sources:
        if src.slots_diff > max_age_slots or src.slots_diff < -100:
            rejected_age += 1
            continue
        if src.latency_ms > max_latency_ms:
            rejected_latency += 1
            continue
        filtered.append(src)

    if rejected_age or rejected_latency:
        log.info("Filtered: %d rejected by age (>%d slots), %d by latency (>%.0fms)",
                 rejected_age, max_age_slots, rejected_latency, max_latency_ms)

    if not filtered and all_sources:
        # Show what was available so the user can adjust filters
        all_sources.sort(key=lambda s: s.slots_diff)
        best = all_sources[0]
        log.warning("All %d sources rejected by filters. Best available: "
                     "%s (age=%d slots, latency=%.0fms). "
                     "Try --max-snapshot-age %d --max-latency %.0f",
                     len(all_sources), best.rpc_address,
                     best.slots_diff, best.latency_ms,
                     best.slots_diff + 500,
                     max(best.latency_ms * 1.5, 500))

    log.info("Found %d sources after filtering", len(filtered))
    return filtered


# -- Speed benchmark -----------------------------------------------------------


def measure_speed(rpc_address: str, measure_time: int = 7) -> float:
    """Measure download speed from an RPC node. Returns bytes/sec."""
    url: str = f"http://{rpc_address}/snapshot.tar.bz2"
    req = Request(url)
    try:
        with urllib.request.urlopen(req, timeout=measure_time + 5) as resp:
            start: float = time.monotonic()
            total: int = 0
            while True:
                elapsed: float = time.monotonic() - start
                if elapsed >= measure_time:
                    break
                chunk: bytes = resp.read(81920)
                if not chunk:
                    break
                total += len(chunk)
            elapsed = time.monotonic() - start
            if elapsed <= 0:
                return 0.0
            return total / elapsed
    except (urllib.error.URLError, OSError, TimeoutError):
        return 0.0


# -- Incremental probing -------------------------------------------------------


def probe_incremental(
    fast_sources: list[SnapshotSource],
    full_snap_slot: int,
) -> tuple[str | None, list[str]]:
    """Probe fast sources for the best incremental matching full_snap_slot.

    Returns (filename, mirror_urls) or (None, []) if no match found.
    The "best" incremental is the one with the highest slot (closest to head).
    """
    best_filename: str | None = None
    best_slot: int = 0
    best_source: SnapshotSource | None = None
    best_path: str | None = None

    for source in fast_sources:
        inc_url: str = f"http://{source.rpc_address}/incremental-snapshot.tar.bz2"
        inc_location, _ = head_no_follow(inc_url, timeout=2)
        if not inc_location:
            continue
        inc_fn, inc_fp = _parse_snapshot_filename(inc_location)
        m: re.Match[str] | None = INCR_SNAP_RE.match(inc_fn)
        if not m:
            continue
        if int(m.group(1)) != full_snap_slot:
            log.debug("  %s: incremental base slot %s != full %d, skipping",
                      source.rpc_address, m.group(1), full_snap_slot)
            continue
        inc_slot: int = int(m.group(2))
        if inc_slot > best_slot:
            best_slot = inc_slot
            best_filename = inc_fn
            best_source = source
            best_path = inc_fp

    if best_filename is None or best_source is None or best_path is None:
        return None, []

    # Build mirror list — check other sources for the same filename
    mirror_urls: list[str] = [f"http://{best_source.rpc_address}{best_path}"]
    for other in fast_sources:
        if other.rpc_address == best_source.rpc_address:
            continue
        other_loc, _ = head_no_follow(
            f"http://{other.rpc_address}/incremental-snapshot.tar.bz2", timeout=2)
        if other_loc:
            other_fn, other_fp = _parse_snapshot_filename(other_loc)
            if other_fn == best_filename:
                mirror_urls.append(f"http://{other.rpc_address}{other_fp}")

    return best_filename, mirror_urls


# -- Download ------------------------------------------------------------------


def download_aria2c(
    urls: list[str],
    output_dir: str,
    filename: str,
    connections: int = 16,
) -> bool:
    """Download a file using aria2c with parallel connections.

    When multiple URLs are provided, aria2c treats them as mirrors of the
    same file and distributes chunks across all of them.
    """
    num_mirrors: int = len(urls)
    total_splits: int = max(connections, connections * num_mirrors)
    cmd: list[str] = [
        "aria2c",
        "--file-allocation=none",
        "--continue=false",
        f"--max-connection-per-server={connections}",
        f"--split={total_splits}",
        "--min-split-size=50M",
        # aria2c retries individual chunk connections on transient network
        # errors (TCP reset, timeout). This is transport-level retry analogous
        # to TCP retransmit, not application-level retry of a failed operation.
        "--max-tries=5",
        "--retry-wait=5",
        "--timeout=60",
        "--connect-timeout=10",
        "--summary-interval=10",
        "--console-log-level=notice",
        f"--dir={output_dir}",
        f"--out={filename}",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        *urls,
    ]

    log.info("Downloading %s", filename)
    log.info("  aria2c: %d connections x %d mirrors (%d splits)",
             connections, num_mirrors, total_splits)

    start: float = time.monotonic()
    result: subprocess.CompletedProcess[bytes] = subprocess.run(cmd)
    elapsed: float = time.monotonic() - start

    if result.returncode != 0:
        log.error("aria2c failed with exit code %d", result.returncode)
        return False

    filepath: Path = Path(output_dir) / filename
    if not filepath.exists():
        log.error("aria2c reported success but %s does not exist", filepath)
        return False

    size_bytes: int = filepath.stat().st_size
    size_gb: float = size_bytes / (1024 ** 3)
    avg_mb: float = size_bytes / elapsed / (1024 ** 2) if elapsed > 0 else 0
    log.info("  Done: %.1f GB in %.0fs (%.1f MiB/s avg)", size_gb, elapsed, avg_mb)
    return True


# -- Public API ----------------------------------------------------------------


def download_best_snapshot(
    output_dir: str,
    *,
    cluster: str = "mainnet-beta",
    rpc_url: str | None = None,
    connections: int = 16,
    threads: int = 500,
    max_snapshot_age: int = 10000,
    max_latency: float = 500,
    min_download_speed: int = 20,
    measurement_time: int = 7,
    max_speed_checks: int = 15,
    version_filter: str | None = None,
    full_only: bool = False,
    convergence_slots: int = 500,
) -> bool:
    """Download the best available snapshot to output_dir.

    This is the programmatic API — called by entrypoint.py for automatic
    snapshot download. Returns True on success, False on failure.

    All parameters have sensible defaults matching the CLI interface.
    """
    resolved_rpc: str = rpc_url or CLUSTER_RPC[cluster]

    if not shutil.which("aria2c"):
        log.error("aria2c not found. Install with: apt install aria2")
        return False

    log.info("Cluster: %s | RPC: %s", cluster, resolved_rpc)
    current_slot: int | None = get_current_slot(resolved_rpc)
    if current_slot is None:
        log.error("Cannot get current slot from %s", resolved_rpc)
        return False
    log.info("Current slot: %d", current_slot)

    sources: list[SnapshotSource] = discover_sources(
        resolved_rpc, current_slot,
        max_age_slots=max_snapshot_age,
        max_latency_ms=max_latency,
        threads=threads,
        version_filter=version_filter,
    )
    if not sources:
        log.error("No snapshot sources found")
        return False

    # Sort by latency (lowest first) for speed benchmarking
    sources.sort(key=lambda s: s.latency_ms)

    # Benchmark top candidates
    log.info("Benchmarking download speed on top %d sources...", max_speed_checks)
    fast_sources: list[SnapshotSource] = []
    checked: int = 0
    min_speed_bytes: int = min_download_speed * 1024 * 1024

    for source in sources:
        if checked >= max_speed_checks:
            break
        checked += 1

        speed: float = measure_speed(source.rpc_address, measurement_time)
        source.download_speed = speed
        speed_mib: float = speed / (1024 ** 2)

        if speed < min_speed_bytes:
            log.info("  %s: %.1f MiB/s (too slow, need >=%d MiB/s)",
                     source.rpc_address, speed_mib, min_download_speed)
            continue

        log.info("  %s: %.1f MiB/s (latency: %.0fms, age: %d slots)",
                 source.rpc_address, speed_mib,
                 source.latency_ms, source.slots_diff)
        fast_sources.append(source)

    if not fast_sources:
        log.error("No source met minimum speed requirement (%d MiB/s)",
                  min_download_speed)
        return False

    # Use the fastest source as primary, collect mirrors for each file
    best: SnapshotSource = fast_sources[0]
    file_paths: list[str] = best.file_paths
    if full_only:
        file_paths = [fp for fp in file_paths
                      if fp.rsplit("/", 1)[-1].startswith("snapshot-")]

    # Build mirror URL lists
    download_plan: list[tuple[str, list[str]]] = []
    for fp in file_paths:
        filename: str = fp.rsplit("/", 1)[-1]
        mirror_urls: list[str] = [f"http://{best.rpc_address}{fp}"]
        for other in fast_sources[1:]:
            for other_fp in other.file_paths:
                if other_fp.rsplit("/", 1)[-1] == filename:
                    mirror_urls.append(f"http://{other.rpc_address}{other_fp}")
                    break
        download_plan.append((filename, mirror_urls))

    speed_mib: float = best.download_speed / (1024 ** 2)
    log.info("Best source: %s (%.1f MiB/s), %d mirrors total",
             best.rpc_address, speed_mib, len(fast_sources))
    for filename, mirror_urls in download_plan:
        log.info("  %s (%d mirrors)", filename, len(mirror_urls))

    # Download — full snapshot first, then re-probe for fresh incremental
    os.makedirs(output_dir, exist_ok=True)
    total_start: float = time.monotonic()

    # Separate full and incremental from the initial plan
    full_downloads: list[tuple[str, list[str]]] = []
    for filename, mirror_urls in download_plan:
        if filename.startswith("snapshot-"):
            full_downloads.append((filename, mirror_urls))

    # Download full snapshot(s)
    for filename, mirror_urls in full_downloads:
        filepath: Path = Path(output_dir) / filename
        if filepath.exists() and filepath.stat().st_size > 0:
            log.info("Skipping %s (already exists: %.1f GB)",
                     filename, filepath.stat().st_size / (1024 ** 3))
            continue
        if not download_aria2c(mirror_urls, output_dir, filename, connections):
            log.error("Failed to download %s", filename)
            return False

    # After full snapshot download, rolling incremental download loop.
    # The initial incremental is stale by now (full download takes 10+ min).
    # Re-probe repeatedly until we find one close enough to head.
    if not full_only:
        full_filename: str = full_downloads[0][0]
        fm_post: re.Match[str] | None = FULL_SNAP_RE.match(full_filename)
        if fm_post:
            full_snap_slot: int = int(fm_post.group(1))
            log.info("Rolling incremental download (base slot %d, convergence %d slots)...",
                     full_snap_slot, convergence_slots)
            prev_inc_filename: str | None = None
            loop_start: float = time.monotonic()
            max_convergence_time: float = 1800.0  # 30 min wall-clock limit

            while True:
                if time.monotonic() - loop_start > max_convergence_time:
                    if prev_inc_filename:
                        log.warning("Convergence timeout (%.0fs) — using %s",
                                    max_convergence_time, prev_inc_filename)
                    else:
                        log.warning("Convergence timeout (%.0fs) — no incremental downloaded",
                                    max_convergence_time)
                    break
                inc_fn, inc_mirrors = probe_incremental(fast_sources, full_snap_slot)
                if inc_fn is None:
                    if prev_inc_filename is None:
                        log.error("No matching incremental found for base slot %d "
                                  "— validator will replay from full snapshot", full_snap_slot)
                    else:
                        log.info("No newer incremental available, using %s", prev_inc_filename)
                    break

                # Parse the incremental slot from the filename
                m_inc: re.Match[str] | None = INCR_SNAP_RE.match(inc_fn)
                assert m_inc is not None  # probe_incremental already validated
                inc_slot: int = int(m_inc.group(2))

                # Check convergence against current mainnet slot
                head_slot: int | None = get_current_slot(resolved_rpc)
                if head_slot is None:
                    log.warning("Cannot get current slot — downloading best available incremental")
                    gap: int = convergence_slots + 1  # force download, then break
                else:
                    gap = head_slot - inc_slot

                # Skip download if we already have this exact incremental
                if inc_fn == prev_inc_filename:
                    if gap <= convergence_slots:
                        log.info("Incremental %s already downloaded (gap %d slots, converged)", inc_fn, gap)
                        break
                    log.info("No newer incremental yet (slot %d, gap %d slots), waiting...",
                             inc_slot, gap)
                    time.sleep(10)
                    continue

                # Delete previous incremental before downloading the new one
                if prev_inc_filename is not None:
                    old_path: Path = Path(output_dir) / prev_inc_filename
                    if old_path.exists():
                        log.info("Removing superseded incremental %s", prev_inc_filename)
                        old_path.unlink()

                log.info("Downloading incremental %s (%d mirrors, slot %d, gap %d slots)",
                         inc_fn, len(inc_mirrors), inc_slot, gap)
                if not download_aria2c(inc_mirrors, output_dir, inc_fn, connections):
                    log.error("Failed to download incremental %s", inc_fn)
                    break

                prev_inc_filename = inc_fn

                if gap <= convergence_slots:
                    log.info("Converged: incremental slot %d is %d slots behind head", inc_slot, gap)
                    break

                if head_slot is None:
                    break

                log.info("Not converged (gap %d > %d), re-probing in 10s...", gap, convergence_slots)
                time.sleep(10)

    total_elapsed: float = time.monotonic() - total_start
    log.info("All downloads complete in %.0fs", total_elapsed)
    for filename, _ in download_plan:
        fp_path: Path = Path(output_dir) / filename
        if fp_path.exists():
            log.info("  %s (%.1f GB)", fp_path.name, fp_path.stat().st_size / (1024 ** 3))

    return True


# -- Main (CLI) ----------------------------------------------------------------


def main() -> int:
    p: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Download Solana snapshots with aria2c parallel downloads",
    )
    p.add_argument("-o", "--output", default="/srv/kind/solana/snapshots",
                   help="Snapshot output directory (default: /srv/kind/solana/snapshots)")
    p.add_argument("-c", "--cluster", default="mainnet-beta",
                   choices=list(CLUSTER_RPC),
                   help="Solana cluster (default: mainnet-beta)")
    p.add_argument("-r", "--rpc", default=None,
                   help="RPC URL for cluster discovery (default: public RPC)")
    p.add_argument("-n", "--connections", type=int, default=16,
                   help="aria2c connections per download (default: 16)")
    p.add_argument("-t", "--threads", type=int, default=500,
                   help="Threads for parallel RPC probing (default: 500)")
    p.add_argument("--max-snapshot-age", type=int, default=10000,
                   help="Max snapshot age in slots (default: 10000)")
    p.add_argument("--max-latency", type=float, default=500,
                   help="Max RPC probe latency in ms (default: 500)")
    p.add_argument("--min-download-speed", type=int, default=20,
                   help="Min download speed in MiB/s (default: 20)")
    p.add_argument("--measurement-time", type=int, default=7,
                   help="Speed measurement duration in seconds (default: 7)")
    p.add_argument("--max-speed-checks", type=int, default=15,
                   help="Max nodes to benchmark before giving up (default: 15)")
    p.add_argument("--version", default=None,
                   help="Filter nodes by version prefix (e.g. '2.2')")
    p.add_argument("--convergence-slots", type=int, default=500,
                   help="Max slot gap for incremental convergence (default: 500)")
    p.add_argument("--full-only", action="store_true",
                   help="Download only full snapshot, skip incremental")
    p.add_argument("--dry-run", action="store_true",
                   help="Find best source and print URL, don't download")
    p.add_argument("--post-cmd",
                   help="Shell command to run after successful download "
                        "(e.g. 'kubectl scale deployment ... --replicas=1')")
    p.add_argument("-v", "--verbose", action="store_true")
    args: argparse.Namespace = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    # Dry-run uses the original inline flow (needs access to sources for URL printing)
    if args.dry_run:
        rpc_url: str = args.rpc or CLUSTER_RPC[args.cluster]
        current_slot: int | None = get_current_slot(rpc_url)
        if current_slot is None:
            log.error("Cannot get current slot from %s", rpc_url)
            return 1

        sources: list[SnapshotSource] = discover_sources(
            rpc_url, current_slot,
            max_age_slots=args.max_snapshot_age,
            max_latency_ms=args.max_latency,
            threads=args.threads,
            version_filter=args.version,
        )
        if not sources:
            log.error("No snapshot sources found")
            return 1

        sources.sort(key=lambda s: s.latency_ms)
        best = sources[0]
        for fp in best.file_paths:
            print(f"http://{best.rpc_address}{fp}")
        return 0

    ok: bool = download_best_snapshot(
        args.output,
        cluster=args.cluster,
        rpc_url=args.rpc,
        connections=args.connections,
        threads=args.threads,
        max_snapshot_age=args.max_snapshot_age,
        max_latency=args.max_latency,
        min_download_speed=args.min_download_speed,
        measurement_time=args.measurement_time,
        max_speed_checks=args.max_speed_checks,
        version_filter=args.version,
        full_only=args.full_only,
        convergence_slots=args.convergence_slots,
    )

    if ok and args.post_cmd:
        log.info("Running post-download command: %s", args.post_cmd)
        result: subprocess.CompletedProcess[bytes] = subprocess.run(
            args.post_cmd, shell=True,
        )
        if result.returncode != 0:
            log.error("Post-download command failed with exit code %d",
                      result.returncode)
            return 1
        log.info("Post-download command completed successfully")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
