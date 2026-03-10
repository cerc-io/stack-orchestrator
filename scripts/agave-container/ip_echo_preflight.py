#!/usr/bin/env python3
"""ip_echo preflight — verify UDP port reachability before starting the validator.

Implements the Solana ip_echo client protocol exactly:
1. Bind UDP sockets on the ports the validator will use
2. TCP connect to entrypoint gossip port, send IpEchoServerMessage
3. Parse IpEchoServerResponse (our IP as seen by entrypoint)
4. Wait for entrypoint's UDP probes on each port
5. Exit 0 if all ports reachable, exit 1 if any fail

Wire format (from agave net-utils/src/):
  Request:  4 null bytes + [u16; 4] tcp_ports LE + [u16; 4] udp_ports LE + \n
  Response: 4 null bytes + bincode IpAddr (variant byte + addr) + optional shred_version

Called from entrypoint.py before snapshot download. Prevents wasting hours
downloading a snapshot only to crash-loop on port reachability.
"""

from __future__ import annotations

import logging
import os
import socket
import struct
import sys
import threading
import time

log = logging.getLogger("ip_echo_preflight")

HEADER = b"\x00\x00\x00\x00"
TERMINUS = b"\x0a"
RESPONSE_BUF = 27
IO_TIMEOUT = 5.0
PROBE_TIMEOUT = 10.0
MAX_RETRIES = 3
RETRY_DELAY = 2.0


def build_request(tcp_ports: list[int], udp_ports: list[int]) -> bytes:
    """Build IpEchoServerMessage: header + [u16;4] tcp + [u16;4] udp + newline."""
    tcp = (tcp_ports + [0, 0, 0, 0])[:4]
    udp = (udp_ports + [0, 0, 0, 0])[:4]
    return HEADER + struct.pack("<4H", *tcp) + struct.pack("<4H", *udp) + TERMINUS


def parse_response(data: bytes) -> tuple[str, int | None]:
    """Parse IpEchoServerResponse → (ip_string, shred_version | None).

    Wire format (bincode):
      4 bytes   header (\0\0\0\0)
      4 bytes   IpAddr enum variant (u32 LE: 0=IPv4, 1=IPv6)
      4|16 bytes  address octets
      1 byte    Option tag (0=None, 1=Some)
      2 bytes   shred_version (u16 LE, only if Some)
    """
    if len(data) < 8:
        raise ValueError(f"response too short: {len(data)} bytes")
    if data[:4] == b"HTTP":
        raise ValueError("got HTTP response — not an ip_echo server")
    if data[:4] != HEADER:
        raise ValueError(f"unexpected header: {data[:4].hex()}")
    variant = struct.unpack("<I", data[4:8])[0]
    if variant == 0:  # IPv4
        if len(data) < 12:
            raise ValueError(f"IPv4 response truncated: {len(data)} bytes")
        ip = socket.inet_ntoa(data[8:12])
        rest = data[12:]
    elif variant == 1:  # IPv6
        if len(data) < 24:
            raise ValueError(f"IPv6 response truncated: {len(data)} bytes")
        ip = socket.inet_ntop(socket.AF_INET6, data[8:24])
        rest = data[24:]
    else:
        raise ValueError(f"unknown IpAddr variant: {variant}")
    shred_version = None
    if len(rest) >= 3 and rest[0] == 1:
        shred_version = struct.unpack("<H", rest[1:3])[0]
    return ip, shred_version


def _listen_udp(port: int, results: dict, stop: threading.Event) -> None:
    """Bind a UDP socket and wait for a probe packet."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        sock.settimeout(0.5)
        try:
            while not stop.is_set():
                try:
                    _data, addr = sock.recvfrom(64)
                    results[port] = ("ok", addr)
                    return
                except socket.timeout:
                    continue
        finally:
            sock.close()
    except OSError as exc:
        results[port] = ("bind_error", str(exc))


def ip_echo_check(
    entrypoint_host: str,
    entrypoint_port: int,
    udp_ports: list[int],
) -> tuple[str, dict[int, bool]]:
    """Run one ip_echo exchange and return (seen_ip, {port: reachable}).

    Raises on TCP failure (caller retries).
    """
    udp_ports = [p for p in udp_ports if p != 0][:4]

    # Start UDP listeners before sending the TCP request
    results: dict[int, tuple] = {}
    stop = threading.Event()
    threads = []
    for port in udp_ports:
        t = threading.Thread(target=_listen_udp, args=(port, results, stop), daemon=True)
        t.start()
        threads.append(t)
    time.sleep(0.1)  # let listeners bind

    # TCP: send request, read response
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(IO_TIMEOUT)
    try:
        sock.connect((entrypoint_host, entrypoint_port))
        sock.sendall(build_request([], udp_ports))
        resp = sock.recv(RESPONSE_BUF)
    finally:
        sock.close()

    seen_ip, shred_version = parse_response(resp)
    log.info(
        "entrypoint %s:%d sees us as %s (shred_version=%s)",
        entrypoint_host, entrypoint_port, seen_ip, shred_version,
    )

    # Wait for UDP probes
    deadline = time.monotonic() + PROBE_TIMEOUT
    while time.monotonic() < deadline:
        if all(p in results for p in udp_ports):
            break
        time.sleep(0.2)

    stop.set()
    for t in threads:
        t.join(timeout=1)

    port_ok: dict[int, bool] = {}
    for port in udp_ports:
        if port not in results:
            log.error("port %d: no probe received within %.0fs", port, PROBE_TIMEOUT)
            port_ok[port] = False
        else:
            status, detail = results[port]
            if status == "ok":
                log.info("port %d: probe received from %s", port, detail)
                port_ok[port] = True
            else:
                log.error("port %d: %s: %s", port, status, detail)
                port_ok[port] = False

    return seen_ip, port_ok


def run_preflight(
    entrypoint_host: str,
    entrypoint_port: int,
    udp_ports: list[int],
    expected_ip: str = "",
) -> bool:
    """Run ip_echo check with retries. Returns True if all ports pass."""
    for attempt in range(1, MAX_RETRIES + 1):
        log.info("ip_echo attempt %d/%d → %s:%d, ports %s",
                 attempt, MAX_RETRIES, entrypoint_host, entrypoint_port, udp_ports)
        try:
            seen_ip, port_ok = ip_echo_check(entrypoint_host, entrypoint_port, udp_ports)
        except Exception as exc:
            log.error("attempt %d TCP failed: %s", attempt, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            continue

        if expected_ip and seen_ip != expected_ip:
            log.error(
                "IP MISMATCH: entrypoint sees %s, expected %s (GOSSIP_HOST). "
                "Outbound mangle/SNAT path is broken.",
                seen_ip, expected_ip,
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            continue

        reachable = [p for p, ok in port_ok.items() if ok]
        unreachable = [p for p, ok in port_ok.items() if not ok]

        if not unreachable:
            log.info("PASS: all ports reachable %s, seen as %s", reachable, seen_ip)
            return True

        log.error(
            "attempt %d: unreachable %s, reachable %s, seen as %s",
            attempt, unreachable, reachable, seen_ip,
        )
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    log.error("FAIL: ip_echo preflight exhausted %d attempts", MAX_RETRIES)
    return False


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Parse entrypoint — VALIDATOR_ENTRYPOINT is "host:port"
    raw = os.environ.get("VALIDATOR_ENTRYPOINT", "")
    if not raw and len(sys.argv) > 1:
        raw = sys.argv[1]
    if not raw:
        log.error("set VALIDATOR_ENTRYPOINT or pass host:port as argument")
        return 1

    if ":" in raw:
        host, port_str = raw.rsplit(":", 1)
        ep_port = int(port_str)
    else:
        host = raw
        ep_port = 8001

    gossip_port = int(os.environ.get("GOSSIP_PORT", "8001"))
    dynamic_range = os.environ.get("DYNAMIC_PORT_RANGE", "9000-10000")
    range_start = int(dynamic_range.split("-")[0])
    expected_ip = os.environ.get("GOSSIP_HOST", "")

    # Test gossip + first 3 ports from dynamic range (4 max per ip_echo message)
    udp_ports = [gossip_port, range_start, range_start + 2, range_start + 3]

    ok = run_preflight(host, ep_port, udp_ports, expected_ip)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
