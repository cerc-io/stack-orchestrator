# DoubleZero Agent — Managed Configuration

The `doublezero-agent` daemon runs on both mia-sw01 and was-sw01. It manages
GRE tunnels, ACLs, BGP neighbors, and route-maps via EOS config sessions
(named `doublezero-agent-<timestamp>`). It periodically creates pending
sessions and commits them, overwriting any manual changes to the objects
it manages.

**Do NOT modify any of the items listed below.** The agent will silently
overwrite your changes.

## mia-sw01

### Tunnel interfaces (all DZ-managed)

| Interface  | Description     | VRF     | Peer            | ACL                          |
|------------|-----------------|---------|-----------------|------------------------------|
| Tunnel500  | USER-UCAST-500  | vrf1    | 186.233.184.235 | SEC-USER-500-IN              |
| Tunnel501  | USER-MCAST-501  | default | 186.233.185.50  | SEC-USER-SUB-MCAST-IN        |
| Tunnel502  | USER-UCAST-502  | vrf1    | 155.138.213.71  | SEC-USER-502-IN              |
| Tunnel503  | USER-MCAST-503  | default | 155.138.213.71  | SEC-USER-PUB-MCAST-IN        |
| Tunnel504  | (empty)         |         |                 |                              |
| Tunnel505  | USER-UCAST-505  | vrf1    | 186.233.185.50  | SEC-USER-505-IN              |
| Tunnel506  | (exists)        |         |                 |                              |

### ACLs (DZ-managed — do NOT modify)

- `SEC-DIA-IN` — ingress ACL on Et1/1 (bogon/RFC1918 filter)
- `SEC-USER-500-IN` — ingress ACL on Tunnel500
- `SEC-USER-502-IN` — ingress ACL on Tunnel502
- `SEC-USER-505-IN` — ingress ACL on Tunnel505
- `SEC-USER-SUB-MCAST-IN` — ingress ACL on Tunnel501
- `SEC-USER-PUB-MCAST-IN` — ingress ACL on Tunnel503
- `SEC-USER-MCAST-BOUNDARY-501-OUT` — multicast boundary on Tunnel501
- `SEC-USER-MCAST-BOUNDARY-503-OUT` — multicast boundary on Tunnel503

### VRF (DZ-managed)

- `vrf1` — used by Tunnel500, Tunnel502, Tunnel505 (unicast tunnels)
- `ip route vrf vrf1 0.0.0.0/0 egress-vrf default Ethernet4/1 172.16.1.188`

### BGP (DZ-managed)

- `router bgp 65342` — iBGP mesh with DZ fabric switches (ny7, sea001, ld4, etc.)
- BGP neighbors on tunnel link IPs (169.254.x.x) with `RM-USER-*` route-maps
- All `RM-USER-*-IN` and `RM-USER-*-OUT` route-maps

### Loopbacks (DZ-managed)

- `Loopback255`, `Loopback256` — BGP update sources for iBGP mesh

## was-sw01

### ACLs (DZ-managed)

- `SEC-DIA-IN` — ingress ACL on Et1/1
- `SEC-USER-PUB-MCAST-IN`
- `SEC-USER-SUB-MCAST-IN`

### Daemons

- `doublezero-agent` — config management
- `doublezero-telemetry` — metrics (writes to influxdb `doublezero-mainnet-beta`)

## Safe to modify (NOT managed by DZ agent)

### mia-sw01

- `Tunnel100` — our dedicated validator relay tunnel (VRF relay)
- `SEC-VALIDATOR-100-IN` — our ACL on Tunnel100
- `Loopback101` — tunnel source IP (209.42.167.137)
- VRF `relay` — our outbound isolation VRF
- `ip route 137.239.194.65/32 egress-vrf relay 169.254.100.1`
- `ip route vrf relay 0.0.0.0/0 egress-vrf default 172.16.1.188`
- Backbone `Ethernet4/1` — physical interface, not DZ-managed

### was-sw01

- `ip route 137.239.194.65/32 172.16.1.189` — our static route
- Backbone `Ethernet4/1` — physical interface, not DZ-managed
