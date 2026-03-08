#!/usr/bin/env python3
"""Listen on UDP port and report the first packet received."""
import socket
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
TIMEOUT = int(sys.argv[2]) if len(sys.argv) > 2 else 15

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", PORT))
s.settimeout(TIMEOUT)
print(f"LISTENING on UDP {PORT}", flush=True)

try:
    data, addr = s.recvfrom(256)
    print(f"OK {len(data)} bytes from {addr[0]}:{addr[1]}: {data!r}")
except socket.timeout:
    print("TIMEOUT no UDP received")
    sys.exit(1)
finally:
    s.close()
