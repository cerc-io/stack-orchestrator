# Bug: Ashburn Relay — 137.239.194.65 Not Routable from Public Internet

## Summary

`--gossip-host 137.239.194.65` correctly advertises the Ashburn relay IP in
ContactInfo for all sockets (gossip, TVU, repair, TPU). However, 137.239.194.65
is a DoubleZero overlay IP (137.239.192.0/19, IS-IS only) that is NOT announced
via BGP to the public internet. Public peers cannot route to it, so TVU shreds,
repair requests, and TPU traffic never arrive at was-sw01.

## Evidence

- Gossip traffic arrives on `doublezero0` interface:
  ```
  doublezero0 In  IP 64.130.58.70.8001 > 137.239.194.65.8001: UDP, length 132
  ```
- Zero TVU/repair traffic arrives:
  ```
  tcpdump -i doublezero0 'dst host 137.239.194.65 and udp and not port 8001'
  0 packets captured
  ```
- ContactInfo correctly advertises all sockets on 137.239.194.65:
  ```json
  {
    "gossip": "137.239.194.65:8001",
    "tvu": "137.239.194.65:9000",
    "serveRepair": "137.239.194.65:9011",
    "tpu": "137.239.194.65:9002"
  }
  ```
- Outbound gossip from biscayne exits via `doublezero0` with source
  137.239.194.65 — SNAT and routing work correctly in the outbound direction.

## Root Cause

**137.239.194.0/24 is not routable from the public internet.** The prefix
belongs to DoubleZero's overlay address space (137.239.192.0/19, Momentum
Telecom, WHOIS OriginAS: empty). It is advertised only via IS-IS within the
DoubleZero switch mesh. There is no eBGP session on was-sw01 to advertise it
to the ISP — all BGP peers are iBGP AS 65342 (DoubleZero internal).

When the validator advertises `tvu: 137.239.194.65:9000` in ContactInfo,
public internet peers attempt to send turbine shreds to that IP, but the
packets have no route through the global BGP table to reach was-sw01. Only
DoubleZero-connected peers could potentially reach it via the overlay.

The old shred relay pipeline worked because it used `--public-tvu-address
64.92.84.81:20000` — was-sw01's Et1/1 ISP uplink IP, which IS publicly
routable. The `--gossip-host 137.239.194.65` approach advertises a
DoubleZero-only IP for ALL sockets, making TVU/repair/TPU unreachable from
non-DoubleZero peers.

The original hypothesis (ACL/PBR port filtering) was wrong. The tunnel and
switch routing work correctly — the problem is upstream: traffic never arrives
at was-sw01 in the first place.

## Impact

The validator cannot receive turbine shreds or serve repair requests via the
low-latency Ashburn path. It falls back to the Miami public IP (186.233.184.235)
for all shred/repair traffic, negating the benefit of `--gossip-host`.

## Fix Options

1. **Use 64.92.84.81 (was-sw01 Et1/1) for ContactInfo sockets.** This is the
   publicly routable Ashburn IP. Requires `--gossip-host 64.92.84.81` (or
   equivalent `--bind-address` config) and DNAT/forwarding on was-sw01 to relay
   traffic through the backbone → mia-sw01 → Tunnel500 → biscayne. The old
   `--public-tvu-address` pipeline used this IP successfully.

2. **Get DoubleZero to announce 137.239.194.0/24 via eBGP to the ISP.** This
   would make the current `--gossip-host 137.239.194.65` setup work, but
   requires coordination with DoubleZero operations.

3. **Hybrid approach**: Use 64.92.84.81 for public-facing sockets (TVU, repair,
   TPU) and 137.239.194.65 for gossip (which works via DoubleZero overlay).
   Requires agave to support per-protocol address binding, which it does not
   (`--gossip-host` sets ALL sockets to the same IP).

## Previous Workaround

The old `--public-tvu-address` pipeline used socat + shred-unwrap.py to relay
shreds from 64.92.84.81:20000 to the validator. That pipeline is not persistent
across reboots and was superseded by the `--gossip-host` approach (which turned
out to be broken for non-DoubleZero peers).
