#!/usr/bin/env python3
"""TCP dport 8001 round trip — connect to a Solana entrypoint (ip_echo path).

The mangle rule matches -p tcp --dport 8001, so connecting TO port 8001
on any host triggers SNAT to the relay IP. The entrypoint responds with
ip_echo (4 bytes: our IP in network order).
"""
import socket
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
HOST = sys.argv[2] if len(sys.argv) > 2 else "34.83.231.102"  # entrypoint.mainnet-beta.solana.com

# Resolve hostname
try:
    addr = socket.getaddrinfo(HOST, PORT, socket.AF_INET)[0][4][0]
except socket.gaierror:
    addr = HOST

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)

try:
    s.connect((addr, PORT))
    print(f"OK TCP handshake to {addr}:{PORT}")
    # ip_echo: peer sends our IP back as 4 bytes
    s.settimeout(2)
    try:
        data = s.recv(64)
        if len(data) >= 4:
            ip = socket.inet_ntoa(data[:4])
            print(f"OK ip_echo says we are {ip}")
        else:
            print(f"OK got {len(data)} bytes: {data.hex()}")
    except socket.timeout:
        print("NOTE: no ip_echo response (handshake succeeded)")
except socket.timeout:
    print("TIMEOUT")
    sys.exit(1)
except ConnectionRefusedError:
    print(f"OK connection refused by {addr}:{PORT} (host reachable)")
except Exception as e:
    print(f"ERROR {e}")
    sys.exit(1)
finally:
    s.close()
