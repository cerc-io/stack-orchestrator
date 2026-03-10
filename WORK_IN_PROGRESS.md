# Work in Progress: Biscayne TVU Shred Relay

## Overview

Biscayne's agave validator was shred-starved (~1.7 slots/sec replay vs ~2.5 mainnet).
Root cause: not enough turbine shreds arriving. Solution: advertise a TVU address in
Ashburn (dense validator population, better turbine tree neighbors) and relay shreds
to biscayne in Miami over the laconic backbone.

### Architecture

```
Turbine peers (hundreds of validators)
       |
       v UDP shreds to port 20000
laconic-was-sw01 Et1/1 (64.92.84.81, Ashburn)
       |  ASIC receives on front-panel interface
       |  EOS monitor session mirrors matched packets to CPU
       v
mirror0 interface (Linux userspace)
       |  socat reads raw frames, sends as UDP
       v  172.16.1.188 -> 186.233.184.235:9100  (Et4/1 backbone, 25.4ms)
laconic-mia-sw01 Et4/1 (172.16.1.189, Miami)
       |  forwards via default route (Et1/1, same metro)
       v  0.13ms
biscayne:9100 (186.233.184.235, Miami)
       |  shred-unwrap.py strips IP+UDP headers
       v  clean shred payload to localhost:9000
agave-validator TVU port
```

Total one-way relay latency: ~12.8ms

### Results

Before relay: ~1.7 slots/sec replay, falling behind ~0.8 slots/sec.
After relay: ~3.32 slots/sec replay, catching up ~0.82 slots/sec.

---

## Changes by Host

### laconic-was-sw01 (Ashburn) — `install@137.239.200.198`

All changes are ephemeral (not persisted, lost on reboot).

**1. EOS monitor session (running-config, not in startup-config)**

Mirrors inbound UDP port 20000 traffic on Et1/1 to a CPU-accessible `mirror0` interface.
Required because the Arista 7280CR3A ASIC handles front-panel traffic without punting to
Linux userspace — regular sockets cannot receive packets on front-panel IPs.

```
monitor session 1 source Ethernet1/1 rx
monitor session 1 ip access-group SHRED-RELAY
monitor session 1 destination Cpu
```

**2. EOS ACL (running-config, not in startup-config)**

```
ip access-list SHRED-RELAY
   10 permit udp any any eq 20000
```

**3. EOS static route (running-config, not in startup-config)**

```
ip route 186.233.184.235/32 172.16.1.189
```

Routes biscayne traffic via Et4/1 backbone to laconic-mia-sw01 instead of the default
route (64.92.84.80, Cogent public internet).

**4. Linux kernel static route (ephemeral, `ip route add`)**

```
ip route add 186.233.184.235/32 via 172.16.1.189 dev et4_1
```

Required because socat runs in Linux userspace. The EOS static route programs the ASIC
but does not always sync to the Linux kernel routing table. Without this, socat's UDP
packets egress via the default route (et1_1, public internet).

**5. socat relay process (foreground, pts/5)**

```bash
sudo socat -u INTERFACE:mirror0,type=2 UDP-SENDTO:186.233.184.235:9100
```

Reads raw L2 frames from mirror0 (SOCK_DGRAM strips ethernet header, leaving IP+UDP+payload).
Sends each frame as a UDP datagram to biscayne:9100. Runs as root (raw socket access to mirror0).

PID: 27743 (child of sudo PID 27742)

---

### laconic-mia-sw01 (Miami) — `install@209.42.167.130`

**No changes made.** MIA already reaches biscayne at 0.13ms via its default route
(`209.42.167.132` on Et1/1, same metro). Relay traffic from WAS arrives on Et4/1
(`172.16.1.189`) and MIA forwards to `186.233.184.235` natively.

Key interfaces for reference:
- Et1/1: `209.42.167.133/31` (public uplink, default route via 209.42.167.132)
- Et4/1: `172.16.1.189/31` (backbone link to WAS, peer 172.16.1.188)
- Et8/1: `172.16.1.192/31` (another backbone link, not used for relay)

---

### biscayne (Miami) — `rix@biscayne.vaasl.io`

**1. Custom agave image: `laconicnetwork/agave:tvu-relay`**

Stock agave v3.1.9 with cherry-picked commit 9f4b3ae from anza master (adds
`--public-tvu-address` flag, from anza PR #6778). Built in `/tmp/agave-tvu-patch/`,
transferred via `docker save | scp | docker load | kind load docker-image`.

**2. K8s deployment changes**

Namespace: `laconic-laconic-70ce4c4b47e23b85`
Deployment: `laconic-70ce4c4b47e23b85-deployment`

Changes from previous deployment:
- Image: `laconicnetwork/agave:local` -> `laconicnetwork/agave:tvu-relay`
- Added env: `PUBLIC_TVU_ADDRESS=64.92.84.81:20000`
- Set: `JITO_ENABLE=false` (stock agave has no Jito flags)
- Strategy: changed to `Recreate` (hostNetwork port conflicts prevent RollingUpdate)

The validator runs with `--public-tvu-address 64.92.84.81:20000`, causing it to
advertise the Ashburn switch IP as its TVU address in gossip. Turbine tree peers
send shreds to Ashburn instead of directly to Miami.

**3. shred-unwrap.py (foreground process, PID 2497694)**

```bash
python3 /tmp/shred-unwrap.py 9100 127.0.0.1 9000
```

Listens on UDP port 9100, strips IP+UDP headers from mirrored packets (variable-length
IP header via IHL field + 8-byte UDP header), forwards clean shred payloads to
localhost:9000 (the validator's TVU port). Running as user `rix`.

Script location: `/tmp/shred-unwrap.py`

**4. agave-stack repo changes (uncommitted)**

- `stack-orchestrator/container-build/laconicnetwork-agave/start-rpc.sh`:
  Added `PUBLIC_TVU_ADDRESS` to header docs and
  `[ -n "${PUBLIC_TVU_ADDRESS:-}" ] && ARGS+=(--public-tvu-address "$PUBLIC_TVU_ADDRESS")`

- `stack-orchestrator/compose/docker-compose-agave-rpc.yml`:
  Added `PUBLIC_TVU_ADDRESS: ${PUBLIC_TVU_ADDRESS:-}` to environment section

---

## What's NOT Production-Ready

### Ephemeral processes
- socat on laconic-was-sw01: foreground process in a terminal session
- shred-unwrap.py on biscayne: foreground process, running from /tmp
- Both die if the terminal disconnects or the host reboots
- Need systemd units for both

### Ephemeral switch config
- Monitor session, ACL, and static routes on was-sw01 are in running-config only
- Not saved to startup-config (`write memory` was run but the route didn't persist)
- Linux kernel route (`ip route add`) is completely ephemeral
- All lost on switch reboot

### No monitoring
- No alerting on relay health (socat crash, shred-unwrap crash, packet loss)
- No metrics on relay throughput vs direct turbine throughput
- No comparison of before/after slot gap trends

### Validator still catching up
- ~50k slots behind as of initial relay activation
- Catching up at ~0.82 slots/sec (~2,950 slots/hour)
- ~17 hours to catch up from current position, or reset with fresh snapshot (~15-30 min)

---

## Key Details

| Item | Value |
|------|-------|
| Biscayne validator identity | `4WeLUxfQghbhsLEuwaAzjZiHg2VBw87vqHc4iZrGvKPr` |
| Biscayne IP | `186.233.184.235` |
| laconic-was-sw01 public IP | `64.92.84.81` (Et1/1) |
| laconic-was-sw01 backbone IP | `172.16.1.188` (Et4/1) |
| laconic-was-sw01 SSH | `install@137.239.200.198` |
| laconic-mia-sw01 backbone IP | `172.16.1.189` (Et4/1) |
| laconic-mia-sw01 SSH | `install@209.42.167.130` |
| Biscayne SSH | `rix@biscayne.vaasl.io` (via ProxyJump abernathy) |
| Backbone RTT (WAS-MIA) | 25.4ms (Et4/1 ↔ Et4/1, 0.01ms jitter) |
| Relay one-way latency | ~12.8ms |
| Agave image | `laconicnetwork/agave:tvu-relay` (v3.1.9 + commit 9f4b3ae) |
| EOS version | 4.34.0F |
