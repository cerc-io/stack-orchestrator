#!/usr/bin/env python3
"""Send a UDP probe packet to a target host:port."""
import socket
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "137.239.194.65"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8001

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b"PROBE", (HOST, PORT))
print(f"OK sent 5 bytes to {HOST}:{PORT}")
s.close()
