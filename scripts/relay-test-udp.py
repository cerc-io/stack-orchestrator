#!/usr/bin/env python3
"""UDP sport 8001 round trip via DNS query to 8.8.8.8."""
import socket
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", PORT))

# DNS query: txn ID 0x1234, standard query for example.com A
query = (
    b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
    b"\x07example\x03com\x00\x00\x01\x00\x01"
)
s.sendto(query, ("8.8.8.8", 53))
s.settimeout(5)

try:
    resp, addr = s.recvfrom(512)
    print(f"OK {len(resp)} bytes from {addr[0]}:{addr[1]}")
except socket.timeout:
    print("TIMEOUT")
    sys.exit(1)
except Exception as e:
    print(f"ERROR {e}")
    sys.exit(1)
finally:
    s.close()
