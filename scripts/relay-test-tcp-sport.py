#!/usr/bin/env python3
"""TCP sport 8001 round trip via HTTP HEAD to 1.1.1.1."""
import socket
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", PORT))

try:
    s.connect(("1.1.1.1", 80))
    s.sendall(b"HEAD / HTTP/1.0\r\nHost: 1.1.1.1\r\n\r\n")
    resp = s.recv(256)
    if b"HTTP" in resp:
        print("OK HTTP response received")
    else:
        print(f"OK {len(resp)} bytes (non-HTTP)")
except socket.timeout:
    print("TIMEOUT")
    sys.exit(1)
except Exception as e:
    print(f"ERROR {e}")
    sys.exit(1)
finally:
    s.close()
