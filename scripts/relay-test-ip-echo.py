#!/usr/bin/env python3
"""Full ip_echo protocol test with UDP probe listener.

Sends the correct ip_echo protocol message to a Solana entrypoint,
which triggers the entrypoint to probe our UDP ports. Then listens
for those probe datagrams to verify inbound UDP reachability.

Protocol (from agave source):
  Request:  4 null bytes + bincode(IpEchoServerMessage) + '\n'
  Response: 4 null bytes + bincode(IpEchoServerResponse)

  IpEchoServerMessage { tcp_ports: [u16; 4], udp_ports: [u16; 4] }
  IpEchoServerResponse { address: IpAddr, shred_version: Option<u16> }

The entrypoint sends a single [0] byte to peer_addr.ip() on each
non-zero UDP port, then responds AFTER all probes complete (5s timeout).
"""
import socket
import struct
import sys
import threading
import time

ENTRYPOINT_IP = sys.argv[1] if len(sys.argv) > 1 else "34.83.231.102"
GOSSIP_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8001

# Build ip_echo request
# bincode for [u16; 4]: 4 little-endian u16 values, no length prefix (fixed array)
tcp_ports = struct.pack("<4H", 0, 0, 0, 0)  # no TCP probes
udp_ports = struct.pack("<4H", GOSSIP_PORT, 0, 0, 0)  # probe our gossip port
header = b"\x00" * 4
message = header + tcp_ports + udp_ports + b"\n"

print(f"Connecting to {ENTRYPOINT_IP}:{GOSSIP_PORT} for ip_echo")
print(f"Request: {message.hex()} ({len(message)} bytes)")

# Start UDP listener on gossip port BEFORE sending ip_echo
udp_received = []

def udp_listener():
    us = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    us.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    us.bind(("0.0.0.0", GOSSIP_PORT))
    us.settimeout(10)
    try:
        while True:
            data, addr = us.recvfrom(64)
            udp_received.append((data, addr))
            print(f"UDP PROBE received: {len(data)} bytes from {addr[0]}:{addr[1]}")
    except socket.timeout:
        pass
    finally:
        us.close()

listener = threading.Thread(target=udp_listener, daemon=True)
listener.start()

# Give listener time to bind
time.sleep(0.1)

# Send ip_echo request via TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(15)  # entrypoint probes take up to 5s each

try:
    s.connect((ENTRYPOINT_IP, GOSSIP_PORT))
    print(f"OK TCP connected to {ENTRYPOINT_IP}:{GOSSIP_PORT}")
    s.sendall(message)
    print("OK ip_echo request sent, waiting for probes + response...")

    # Read response (comes AFTER probes complete)
    resp = b""
    while len(resp) < 4:
        chunk = s.recv(256)
        if not chunk:
            break
        resp += chunk

    if len(resp) >= 4:
        print(f"OK ip_echo response: {len(resp)} bytes: {resp.hex()}")
        # Parse: 4 null bytes + bincode IpEchoServerResponse
        # IpEchoServerResponse { address: IpAddr, shred_version: Option<u16> }
        # bincode IpAddr: enum tag (u32) + data
        if len(resp) >= 12:
            payload = resp[4:]
            ip_enum = struct.unpack("<I", payload[:4])[0]
            if ip_enum == 0:  # V4
                ip_bytes = payload[4:8]
                ip = socket.inet_ntoa(ip_bytes)
                print(f"OK entrypoint sees us as {ip}")
            else:
                print(f"OK ip_enum={ip_enum} (IPv6?)")
    else:
        print(f"ERROR incomplete response: {len(resp)} bytes: {resp.hex()}")
except socket.timeout:
    print("TIMEOUT waiting for ip_echo response")
    sys.exit(1)
except ConnectionRefusedError:
    print(f"REFUSED by {ENTRYPOINT_IP}:{GOSSIP_PORT}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR {e}")
    sys.exit(1)
finally:
    s.close()

# Wait for listener to finish
listener.join(timeout=2)

# Summary
print(f"\nUDP probes received: {len(udp_received)}")
if udp_received:
    print("OK inbound UDP reachability CONFIRMED")
else:
    print("FAIL no UDP probes received — inbound UDP is broken")
    sys.exit(1)
