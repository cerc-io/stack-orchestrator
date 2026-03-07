# Bug: Ashburn Relay — Outbound Gossip Dropped by DZ Agent ACL

## Summary

`--gossip-host 137.239.194.65` correctly advertises the Ashburn relay IP in
ContactInfo for all sockets (gossip, TVU, repair, TPU). The inbound path
works end-to-end (proven with kelce UDP tests through every hop). However,
outbound gossip from biscayne (src 137.239.194.65) is dropped by the
DoubleZero agent's ACL on mia-sw01's Tunnel500, preventing ContactInfo from
propagating to the cluster. Peers never learn our TVU address.

## Evidence

- Inbound path confirmed hop by hop (kelce → was-sw01 → mia-sw01 → Tunnel500
  → biscayne doublezero0 → DNAT → kind bridge → kind node eth0):
  ```
  01:04:12.136633 IP 69.112.108.72.58856 > 172.20.0.2.9000: UDP, length 13
  ```
- Outbound gossip leaves biscayne correctly (src 137.239.194.65:8001 on
  doublezero0), enters mia-sw01 via Tunnel500, hits SEC-USER-500-IN ACL:
  ```
  60 deny ip any any [match 26355968 packets, 0:00:02 ago]
  ```
  The ACL only permits src 186.233.184.235 and 169.254.7.7 — not 137.239.194.65.
- Validator not visible in public RPC getClusterNodes (gossip not propagating)
- Validator sees 775 nodes vs 5,045 on public RPC

## Root Cause

The `doublezero-agent` daemon on mia-sw01 manages Tunnel500 and its ACL
(SEC-USER-500-IN). The agent periodically reconciles the ACL to its expected
state, overwriting any custom entries we add. We cannot modify the ACL
without the agent reverting it.

137.239.194.65 is from the was-sw01 LAN block (137.239.194.64/29), routed
by the ISP to was-sw01 via the WAN link. It IS publicly routable (confirmed
by kelce ping/UDP tests). The earlier hypothesis that it was unroutable was
wrong — the IP reaches was-sw01, gets forwarded to mia-sw01 via backbone,
and reaches biscayne through Tunnel500 (inbound ACL direction is fine).

The problem is outbound only: the Tunnel500 ingress ACL (traffic FROM
biscayne TO mia-sw01) drops src 137.239.194.65.

## Fix

Create a dedicated GRE tunnel (Tunnel100) between biscayne and mia-sw01
that bypasses the DZ-managed Tunnel500 entirely:

- **mia-sw01 Tunnel100**: src 209.42.167.137 (free LAN IP), dst 186.233.184.235
  (biscayne), link 169.254.100.0/31, ACL SEC-VALIDATOR-100-IN (we control)
- **biscayne gre-ashburn**: src 186.233.184.235, dst 209.42.167.137,
  link 169.254.100.1/31

Traffic flow unchanged except the tunnel:
- Inbound: was-sw01 → backbone → mia-sw01 → Tunnel100 → biscayne → DNAT → agave
- Outbound: agave → SNAT 137.239.194.65 → Tunnel100 → mia-sw01 → backbone → was-sw01

See:
- `playbooks/ashburn-relay-mia-sw01.yml` (Tunnel100 + ACL + routes)
- `playbooks/ashburn-relay-biscayne.yml` (gre-ashburn + DNAT + SNAT + policy routing)
- `playbooks/ashburn-relay-was-sw01.yml` (static route, unchanged)
