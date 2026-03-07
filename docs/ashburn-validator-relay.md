# Ashburn Validator Relay — Full Traffic Redirect

## Overview

All validator traffic (gossip, repair, TVU, TPU) enters and exits from
`137.239.194.65` (laconic-was-sw01, Ashburn). Peers see the validator as an
Ashburn node. This improves repair peer count and slot catchup rate by reducing
RTT to the TeraSwitch/Pittsburgh cluster from ~30ms (direct Miami) to ~5ms
(Ashburn).

Supersedes the previous TVU-only shred relay (see `tvu-shred-relay.md`).

## Architecture

```
                 OUTBOUND (validator → peers)
agave-validator (kind pod, ports 8001, 9000-9025)
       ↓ Docker bridge → host FORWARD chain
biscayne host (186.233.184.235)
       ↓ mangle PREROUTING: fwmark 100 on sport 8001,9000-9025 from 172.20.0.0/16
       ↓ nat POSTROUTING: SNAT → src 137.239.194.65
       ↓ policy route: fwmark 100 → table ashburn → via 169.254.7.6 dev doublezero0
laconic-mia-sw01 (209.42.167.133, Miami)
       ↓ traffic-policy VALIDATOR-OUTBOUND: src 137.239.194.65 → nexthop 172.16.1.188
       ↓ backbone Et4/1 (25.4ms)
laconic-was-sw01 Et4/1 (Ashburn)
       ↓ default route via 64.92.84.80 out Et1/1
Internet (peers see src 137.239.194.65)

                 INBOUND (peers → validator)
Solana peers → 137.239.194.65:8001,9000-9025
       ↓ internet routing to was-sw01
laconic-was-sw01 Et1/1 (Ashburn)
       ↓ traffic-policy VALIDATOR-RELAY: ASIC redirect, line rate
       ↓ nexthop 172.16.1.189 via Et4/1 backbone (25.4ms)
laconic-mia-sw01 Et4/1 (Miami)
       ↓ L3 forward → biscayne via doublezero0 GRE or ISP routing
biscayne (186.233.184.235)
       ↓ nat PREROUTING: DNAT dst 137.239.194.65:* → 172.20.0.2:* (kind node)
       ↓ Docker bridge → validator pod
agave-validator
```

RPC traffic (port 8899) is NOT relayed — clients connect directly to biscayne.

## Switch Config: laconic-was-sw01

SSH: `install@137.239.200.198`

### Pre-change

```
configure checkpoint save pre-validator-relay
```

Rollback: `rollback running-config checkpoint pre-validator-relay` then `write memory`.

### Config session with auto-revert

```
configure session validator-relay

! Loopback for 137.239.194.65 (do NOT touch Loopback100 which has .64)
interface Loopback101
   ip address 137.239.194.65/32

! ACL covering all validator ports
ip access-list VALIDATOR-RELAY-ACL
   10 permit udp any any eq 8001
   20 permit udp any any range 9000 9025
   30 permit tcp any any eq 8001

! Traffic-policy: ASIC redirect to backbone (mia-sw01)
traffic-policy VALIDATOR-RELAY
   match VALIDATOR-RELAY-ACL
      set nexthop 172.16.1.189

! Replace old SHRED-RELAY on Et1/1
interface Ethernet1/1
   no traffic-policy input SHRED-RELAY
   traffic-policy input VALIDATOR-RELAY

! system-rule overriding-action redirect (already present from SHRED-RELAY)

show session-config diffs
commit timer 00:05:00
```

After verification: `configure session validator-relay commit` then `write memory`.

### Cleanup (after stable)

Old SHRED-RELAY policy and ACL can be removed once VALIDATOR-RELAY is confirmed:

```
configure session cleanup-shred-relay
no traffic-policy SHRED-RELAY
no ip access-list SHRED-RELAY-ACL
show session-config diffs
commit
write memory
```

## Switch Config: laconic-mia-sw01

### Pre-flight checks

Before applying config, verify:

1. Which EOS interface terminates the doublezero0 GRE from biscayne
   (endpoint 209.42.167.133). Check with `show interfaces tunnel` or
   `show ip interface brief | include Tunnel`.

2. Whether `system-rule overriding-action redirect` is already configured.
   Check with `show running-config | include system-rule`.

3. Whether EOS traffic-policy works on tunnel interfaces. If not, apply on
   the physical interface where GRE packets arrive (likely Et<X> facing
   biscayne's ISP network or the DZ infrastructure).

### Config session

```
configure checkpoint save pre-validator-outbound

configure session validator-outbound

! ACL matching outbound validator traffic (source = Ashburn IP)
ip access-list VALIDATOR-OUTBOUND-ACL
   10 permit ip 137.239.194.65/32 any

! Redirect to was-sw01 via backbone
traffic-policy VALIDATOR-OUTBOUND
   match VALIDATOR-OUTBOUND-ACL
      set nexthop 172.16.1.188

! Apply on the interface where biscayne GRE traffic arrives
! Replace Tunnel<X> with the actual interface from pre-flight check #1
interface Tunnel<X>
   traffic-policy input VALIDATOR-OUTBOUND

! Add system-rule if not already present (pre-flight check #2)
system-rule overriding-action redirect

show session-config diffs
commit timer 00:05:00
```

After verification: commit + `write memory`.

## Host Config: biscayne

Automated via ansible playbook `playbooks/ashburn-validator-relay.yml`.

### Manual equivalent

```bash
# 1. Accept packets destined for 137.239.194.65
sudo ip addr add 137.239.194.65/32 dev lo

# 2. Inbound DNAT to kind node (172.20.0.2)
sudo iptables -t nat -A PREROUTING -p udp -d 137.239.194.65 --dport 8001 \
  -j DNAT --to-destination 172.20.0.2:8001
sudo iptables -t nat -A PREROUTING -p tcp -d 137.239.194.65 --dport 8001 \
  -j DNAT --to-destination 172.20.0.2:8001
sudo iptables -t nat -A PREROUTING -p udp -d 137.239.194.65 --dport 9000:9025 \
  -j DNAT --to-destination 172.20.0.2

# 3. Outbound: mark validator traffic
sudo iptables -t mangle -A PREROUTING -s 172.20.0.0/16 -p udp --sport 8001 \
  -j MARK --set-mark 100
sudo iptables -t mangle -A PREROUTING -s 172.20.0.0/16 -p udp --sport 9000:9025 \
  -j MARK --set-mark 100
sudo iptables -t mangle -A PREROUTING -s 172.20.0.0/16 -p tcp --sport 8001 \
  -j MARK --set-mark 100

# 4. Outbound: SNAT to Ashburn IP (INSERT before Docker MASQUERADE)
sudo iptables -t nat -I POSTROUTING 1 -m mark --mark 100 \
  -j SNAT --to-source 137.239.194.65

# 5. Policy routing table
echo "100 ashburn" | sudo tee -a /etc/iproute2/rt_tables
sudo ip rule add fwmark 100 table ashburn
sudo ip route add default via 169.254.7.6 dev doublezero0 table ashburn

# 6. Persist
sudo netfilter-persistent save
# ip rule + ip route persist via /etc/network/if-up.d/ashburn-routing
```

### Docker NAT port preservation

**Must verify before going live:** Docker masquerade must preserve source ports
for kind's hostNetwork pods. If Docker rewrites the source port, the mangle
PREROUTING match on `--sport 8001,9000-9025` will miss traffic.

Test: `tcpdump -i br-cf46a62ab5b2 -nn 'udp src port 8001'` — if you see
packets with sport 8001 from 172.20.0.2, port preservation works.

If Docker does NOT preserve ports, the mark must be set inside the kind node
container (on the pod's veth) rather than on the host.

## Execution Order

1. **was-sw01**: checkpoint → config session with 5min auto-revert → verify counters → commit
2. **biscayne**: add 137.239.194.65/32 to lo, add inbound DNAT rules
3. **Verify inbound**: `ping 137.239.194.65` from external host, check DNAT counters
4. **mia-sw01**: pre-flight checks → config session with 5min auto-revert → commit
5. **biscayne**: add outbound fwmark + policy routing + SNAT rules
6. **Test outbound**: from biscayne, send UDP from port 8001, verify src 137.239.194.65 on was-sw01
7. **Verify**: traffic-policy counters on both switches, iptables hit counts on biscayne
8. **Restart validator** if needed (gossip should auto-refresh, but restart ensures clean state)
9. **was-sw01 + mia-sw01**: `write memory` to persist
10. **Cleanup**: remove old SHRED-RELAY and 64.92.84.81:20000 DNAT after stable

## Verification

1. `show traffic-policy counters` on was-sw01 — VALIDATOR-RELAY-ACL matches
2. `show traffic-policy counters` on mia-sw01 — VALIDATOR-OUTBOUND-ACL matches
3. `sudo iptables -t nat -L -v -n` on biscayne — DNAT and SNAT hit counts
4. `sudo iptables -t mangle -L -v -n` on biscayne — fwmark hit counts
5. `ip rule show` on biscayne — fwmark 100 lookup ashburn
6. Validator gossip ContactInfo shows 137.239.194.65 for ALL addresses (gossip, repair, TVU, TPU)
7. Repair peer count increases (target: 20+ peers)
8. Slot catchup rate improves from ~0.9 toward ~2.5 slots/sec
9. `traceroute --sport=8001 <remote_peer>` from biscayne routes via doublezero0/was-sw01

## Rollback

### biscayne

```bash
sudo ip addr del 137.239.194.65/32 dev lo
sudo iptables -t nat -D PREROUTING -p udp -d 137.239.194.65 --dport 8001 -j DNAT --to-destination 172.20.0.2:8001
sudo iptables -t nat -D PREROUTING -p tcp -d 137.239.194.65 --dport 8001 -j DNAT --to-destination 172.20.0.2:8001
sudo iptables -t nat -D PREROUTING -p udp -d 137.239.194.65 --dport 9000:9025 -j DNAT --to-destination 172.20.0.2
sudo iptables -t mangle -D PREROUTING -s 172.20.0.0/16 -p udp --sport 8001 -j MARK --set-mark 100
sudo iptables -t mangle -D PREROUTING -s 172.20.0.0/16 -p udp --sport 9000:9025 -j MARK --set-mark 100
sudo iptables -t mangle -D PREROUTING -s 172.20.0.0/16 -p tcp --sport 8001 -j MARK --set-mark 100
sudo iptables -t nat -D POSTROUTING -m mark --mark 100 -j SNAT --to-source 137.239.194.65
sudo ip rule del fwmark 100 table ashburn
sudo ip route del default table ashburn
sudo netfilter-persistent save
```

### was-sw01

```
rollback running-config checkpoint pre-validator-relay
write memory
```

### mia-sw01

```
rollback running-config checkpoint pre-validator-outbound
write memory
```

## Key Details

| Item | Value |
|------|-------|
| Ashburn relay IP | `137.239.194.65` (Loopback101 on was-sw01) |
| Ashburn LAN block | `137.239.194.64/29` on was-sw01 Et1/1 |
| Biscayne IP | `186.233.184.235` |
| Kind node IP | `172.20.0.2` (Docker bridge br-cf46a62ab5b2) |
| Validator ports | 8001 (gossip), 9000-9025 (TVU/repair/TPU) |
| Excluded ports | 8899 (RPC), 8900 (WebSocket) — direct to biscayne |
| GRE tunnel | doublezero0: 169.254.7.7 ↔ 169.254.7.6, remote 209.42.167.133 |
| Backbone | was-sw01 Et4/1 172.16.1.188/31 ↔ mia-sw01 Et4/1 172.16.1.189/31 |
| Policy routing table | 100 ashburn |
| Fwmark | 100 |
| was-sw01 SSH | `install@137.239.200.198` |
| EOS version | 4.34.0F |
