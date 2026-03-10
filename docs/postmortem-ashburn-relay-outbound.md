# Post-Mortem: Ashburn Relay Outbound Path Failure

**Date resolved**: 2026-03-10
**Duration of impact**: Unknown — likely since firewalld was enabled (post-reboot
2026-03-09 ~21:24 UTC). The relay worked before this with firewalld disabled.
**Symptoms**: Validator CrashLoopBackOff on ip_echo port reachability check.
Entrypoint never receives the validator's outbound TCP connection, so it can't
verify UDP port reachability and the validator refuses to start.

## Timeline

### Session d02959a7 (2026-03-06 to 2026-03-08)

Initial relay infrastructure build-out. Multi-day effort across three repos.

1. **Validator deployed**, replaying at 0.24 slots/sec. RTT between Miami and
   peers (~150ms per repair round-trip) identified as the bottleneck. Ashburn
   relay identified as the fix.

2. **GRE tunnel created** (gre-ashburn: biscayne 186.233.184.235 ↔ mia-sw01
   209.42.167.137). Tunnel100 on mia-sw01 in VRF relay. Policy routing with
   fwmark 0x64 routes validator traffic through the tunnel.

3. **Inbound path debugged end-to-end**:
   - Cross-VRF routing on mia-sw01 investigated (egress-vrf route form, hardware
     FIB programming, TCAM profile).
   - GRE decapsulation on biscayne verified (kernel source read to understand
     ip_tunnel_lookup matching logic).
   - **DOCKER chain drop rule found**: Docker's FORWARD chain only had ACCEPT
     for TCP 6443/443/80. DNAT'd relay UDP was dropped. Fix: DOCKER-USER
     ACCEPT rules for UDP 8001 and 9000-9025.
   - Inbound UDP relay test passed (kelce → was-sw01 → mia-sw01 → Tunnel100 →
     biscayne → DNAT → kind node).

4. **Outbound path partially verified**: Relay test scripts confirmed TCP and
   UDP traffic from the kind container exits via gre-ashburn with correct SNAT.
   But the **validator's own ip_echo check was never end-to-end verified** with
   a successful startup. The validator entered CrashLoopBackOff after the
   DOCKER-USER fix for unrelated reasons (monitoring container crashes, log path
   issues).

5. **Ashburn relay checklist** written at `docs/ashburn-relay-checklist.md` —
   7 layers covering the full path. All items remained unchecked.

### Session 0b5908a4 (2026-03-09)

Container rebuild, graceful shutdown implementation, ZFS upgrade, storage
migration. The validator was **running and catching up from a ~5,649 slot gap**,
confirming the relay was working. Then:

- io_uring/ZFS deadlock from ungraceful shutdown (ZFS 2.2.2, fixed in 2.2.8+)
- Reboot required to clear zombie processes
- **Firewalld was enabled/started on the reboot** (previously disabled)

### Session cc6c8c55 (2026-03-10, this session)

User asked to review session d02959a7 to confirm the ip_echo problem was
actually solved. It wasn't.

1. **ip_echo preflight tool written** (`scripts/agave-container/ip_echo_preflight.py`)
   — reimplements the Solana ip_echo client protocol in Python, called from
   `entrypoint.py` before snapshot download. Tested successfully against live
   entrypoints from the host.

2. **Tested from kind netns** — TCP to entrypoint:8001 returns "No route to
   host". Mangle PREROUTING counter increments (marking works) but SNAT
   POSTROUTING counter stays at 0 (packets never reach POSTROUTING).

3. **Misdiagnoses**:
   - `src_valid_mark=0` suspected as root cause. Set to 1, no change. The
     `ip route get X from Y mark Z` command was misleading — it simulates
     locally-originated traffic, not forwarded. The correct test is
     `ip route get X from Y iif <iface> mark Z`, which showed routing works.
   - Firewalld nftables backend not setting `src_valid_mark` was a red herring.

4. **Root cause found**: Firewalld's nftables `filter_FORWARD` chain (priority
   filter+10) rejects forwarded traffic between interfaces not in known zones.
   Docker bridges and gre-ashburn were not in any firewalld zone. The chain's
   `filter_FORWARD_POLICIES` only had rules for eno1, eno2, and mesh.
   Traffic from br-cf46a62ab5b2 to gre-ashburn fell through to
   `reject with icmpx admin-prohibited`.

   ```
   # The reject that was killing outbound relay traffic:
   chain filter_FORWARD {
       ...
       jump filter_FORWARD_POLICIES
       reject with icmpx admin-prohibited   ← packets from unknown interfaces
   }
   ```

5. **Fix applied**:
   - Docker bridges (br-cf46a62ab5b2, docker0, br-4fb6f6795448) → `docker` zone
   - gre-ashburn → `trusted` zone
   - New `docker-to-relay` policy: docker → trusted, ACCEPT
   - All permanent (`firewall-cmd --permanent` + reload)

6. **Verified**: ip_echo from kind netns returns `seen_ip=137.239.194.65
   shred_version=50093`. Full outbound path works.

## Root Cause

**Firewalld was enabled on biscayne after a reboot. Its nftables FORWARD chain
rejected forwarded traffic from Docker bridges to gre-ashburn because neither
interface was assigned to a firewalld zone.**

The relay worked before because firewalld was disabled. The iptables rules
(mangle marks, SNAT, DNAT, DOCKER-USER) operated without interference. When
firewalld was enabled, its nftables filter_FORWARD chain (priority filter+10)
added a second layer of forwarding policy enforcement that the iptables rules
couldn't bypass.

### Why Docker outbound to the internet still worked

Docker's outbound traffic to eno1 was accepted by firewalld because eno1 IS in
the `public` zone. The `filter_FWD_public_allow` chain has `oifname "eno1"
accept`. Only traffic to gre-ashburn (not in any zone) was rejected.

### Why iptables rules alone weren't enough

Linux netfilter processes hooks in priority order. At the FORWARD hook:

1. **Priority filter (0)**: iptables `FORWARD` chain — Docker's DOCKER-USER
   and DOCKER-FORWARD chains. These accept the traffic.
2. **Priority filter+10**: nftables `filter_FORWARD` chain — firewalld's zone
   policies. These reject the traffic if interfaces aren't in known zones.

Both chains must accept for the packet to pass. The iptables acceptance at
priority 0 is overridden by the nftables rejection at priority filter+10.

## Architecture After Fix

Firewalld manages forwarding policy. Iptables handles Docker-specific rules
that firewalld can't replace (DNAT ordering, DOCKER-USER chain, mangle marks,
SNAT). Both coexist because they operate at different netfilter priorities.

```
Firewalld (permanent, survives reboots):
  docker zone: br-cf46a62ab5b2, docker0, br-4fb6f6795448
  trusted zone: mesh, gre-ashburn
  docker-forwarding policy: ANY → docker, ACCEPT (existing)
  docker-to-relay policy: docker → trusted, ACCEPT (new)

Systemd service (ashburn-relay.service, After=docker+firewalld):
  GRE tunnel creation (iproute2)
  Ashburn IP on loopback (iproute2)
  DNAT rules at PREROUTING position 1 (iptables, before Docker's chain)
  DOCKER-USER ACCEPT rules (iptables, for Docker's FORWARD chain)
  Mangle marks for policy routing (iptables)
  SNAT for marked traffic (iptables)
  ip rule + ip route for ashburn table (iproute2)
```

## Lessons

1. **Firewalld with nftables backend and Docker iptables coexist but don't
   coordinate.** Adding an interface that Docker uses to forward traffic
   requires explicitly assigning it to a firewalld zone. Docker's iptables
   ACCEPT is necessary but not sufficient.

2. **`ip route get X from Y mark Z` is misleading for forwarded traffic.**
   It simulates local origination and fails on source address validation. Use
   `ip route get X from Y iif <iface> mark Z` to simulate forwarded packets.
   This wasted significant debugging time.

3. **SNAT counter = 0 means packets die before POSTROUTING, but the cause
   could be in either the routing decision OR a filter chain between PREROUTING
   and POSTROUTING.** The nftables filter_FORWARD chain was invisible when only
   checking iptables rules.

4. **The validator passed ip_echo and ran successfully before.** That prior
   success was the strongest evidence that the infrastructure was correct and
   something changed. The change was firewalld being enabled.

## Related Documents

- `docs/ashburn-relay-checklist.md` — 7-layer checklist for relay verification
- `docs/bug-ashburn-tunnel-port-filtering.md` — prior DOCKER chain drop bug
- `.claude/skills/biscayne-relay-debugging/SKILL.md` — debugging skill
- `playbooks/ashburn-relay-biscayne.yml` — migrated playbook (firewalld + iptables)
- `scripts/agave-container/ip_echo_preflight.py` — preflight diagnostic tool

## Related Sessions

- `d02959a7-2ec6-4d27-8326-1bc4aaf3ebf1` (2026-03-06): Initial relay build,
  DOCKER-USER fix, inbound path verified, outbound not end-to-end verified
- `0b5908a4-eff7-46de-9024-a11440bd68a8` (2026-03-09): Relay working (validator
  catching up), then reboot introduced firewalld
- `cc6c8c55-fb4c-4482-b161-332ddf175300` (2026-03-10): Root cause found and
  fixed (firewalld zone assignment)
