#!/usr/bin/env python3
"""Strip IP+UDP headers from mirrored packets and forward raw UDP payload."""
import socket
import sys

LISTEN_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9100
FORWARD_HOST = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
FORWARD_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 9000

sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_in.bind(("0.0.0.0", LISTEN_PORT))

sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

count = 0
while True:
    data, addr = sock_in.recvfrom(65535)
    if len(data) < 28:
        continue
    # IP header: first nibble is version (4), second nibble is IHL (words)
    if (data[0] >> 4) != 4:
        continue
    ihl = (data[0] & 0x0F) * 4
    # Protocol should be UDP (17)
    if data[9] != 17:
        continue
    # Payload starts after IP header + 8-byte UDP header
    offset = ihl + 8
    payload = data[offset:]
    if payload:
        sock_out.sendto(payload, (FORWARD_HOST, FORWARD_PORT))
        count += 1
        if count % 10000 == 0:
            print(f"Forwarded {count} shreds", flush=True)
