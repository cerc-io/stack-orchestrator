# TVU Shred Relay — Data-Plane Redirect

## Overview

Biscayne's agave validator advertises `64.92.84.81:20000` (laconic-was-sw01 Et1/1) as its TVU
address. Turbine shreds arrive as normal UDP to the switch's front-panel IP. The 7280CR3A ASIC
handles front-panel traffic without punting to Linux userspace — it sees a local interface IP
with no service and drops at the hardware level.

### Previous approach (monitor + socat)

EOS monitor session mirrored matched packets to CPU (mirror0 interface). socat read from mirror0
and relayed to biscayne. shred-unwrap.py on biscayne stripped encapsulation headers.

Fragile: socat ran as a foreground process, died on disconnect.

### New approach (traffic-policy redirect)

EOS `traffic-policy` with `set nexthop` and `system-rule overriding-action redirect` overrides
the ASIC's "local IP, handle myself" decision. The ASIC forwards matched packets to the
specified next-hop at line rate. Pure data plane, no CPU involvement, persists in startup-config.

Available since EOS 4.28.0F on R3 platforms. Confirmed on 4.34.0F.

## Architecture

```
Turbine peers (hundreds of validators)
       |
       v UDP shreds to 64.92.84.81:20000
laconic-was-sw01 Et1/1 (Ashburn)
       |  ASIC matches traffic-policy SHRED-RELAY
       |  Redirects to nexthop 172.16.1.189 (data plane, line rate)
       v  Et4/1 backbone (25.4ms)
laconic-mia-sw01 Et4/1 (Miami)
       |  forwards via default route (same metro)
       v  0.13ms
biscayne (186.233.184.235, Miami)
       |  iptables DNAT: dst 64.92.84.81:20000 -> 127.0.0.1:9000
       v
agave-validator TVU port (localhost:9000)
```

## Production Config: laconic-was-sw01

### Pre-change safety

```
configure checkpoint save pre-shred-relay
```

Rollback: `rollback running-config checkpoint pre-shred-relay` then `write memory`.

### Config session with auto-revert

```
configure session shred-relay

! ACL for traffic-policy match
ip access-list SHRED-RELAY-ACL
   10 permit udp any any eq 20000

! Traffic policy: redirect matched packets to backbone next-hop
traffic-policy SHRED-RELAY
   match SHRED-RELAY-ACL
      set nexthop 172.16.1.189

! Override ASIC punt-to-CPU for redirected traffic
system-rule overriding-action redirect

! Apply to Et1/1 ingress
interface Ethernet1/1
   traffic-policy input SHRED-RELAY

! Remove old monitor session and its ACL
no monitor session 1
no ip access-list SHRED-RELAY

! Review before committing
show session-config diffs

! Commit with 5-minute auto-revert safety net
commit timer 00:05:00
```

After verification: `configure session shred-relay commit` then `write memory`.

### Linux cleanup on was-sw01

```bash
# Kill socat relay (PID 27743)
kill 27743
# Remove Linux kernel route
ip route del 186.233.184.235/32
```

The EOS static route `ip route 186.233.184.235/32 172.16.1.189` stays (general reachability).

## Production Config: biscayne

### iptables DNAT

Traffic-policy sends normal L3-forwarded UDP packets (no mirror encapsulation). Packets arrive
with dst `64.92.84.81:20000` containing clean shred payloads directly in the UDP body.

```bash
sudo iptables -t nat -A PREROUTING -p udp -d 64.92.84.81 --dport 20000 \
  -j DNAT --to-destination 127.0.0.1:9000

# Persist across reboot
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

### Cleanup

```bash
# Kill shred-unwrap.py (PID 2497694)
kill 2497694
rm /tmp/shred-unwrap.py
```

## Verification

1. `show traffic-policy interface Ethernet1/1` — policy applied
2. `show traffic-policy counters` — packets matching and redirected
3. `sudo iptables -t nat -L PREROUTING -v -n` — DNAT rule with packet counts
4. Validator logs: slot replay rate should maintain ~3.3 slots/sec
5. `ss -unp | grep 9000` — validator receiving on TVU port

## What was removed

| Component | Host |
|-----------|------|
| monitor session 1 | was-sw01 |
| SHRED-RELAY ACL (old) | was-sw01 |
| socat relay process | was-sw01 |
| Linux kernel static route | was-sw01 |
| shred-unwrap.py | biscayne |

## What was added

| Component | Host | Persistent? |
|-----------|------|-------------|
| traffic-policy SHRED-RELAY | was-sw01 | Yes (startup-config) |
| SHRED-RELAY-ACL | was-sw01 | Yes (startup-config) |
| system-rule overriding-action redirect | was-sw01 | Yes (startup-config) |
| iptables DNAT rule | biscayne | Yes (iptables-persistent) |

## Key Details

| Item | Value |
|------|-------|
| Biscayne validator identity | `4WeLUxfQghbhsLEuwaAzjZiHg2VBw87vqHc4iZrGvKPr` |
| Biscayne IP | `186.233.184.235` |
| laconic-was-sw01 public IP | `64.92.84.81` (Et1/1) |
| laconic-was-sw01 backbone IP | `172.16.1.188` (Et4/1) |
| laconic-was-sw01 SSH | `install@137.239.200.198` |
| laconic-mia-sw01 backbone IP | `172.16.1.189` (Et4/1) |
| Backbone RTT (WAS-MIA) | 25.4ms |
| EOS version | 4.34.0F |
