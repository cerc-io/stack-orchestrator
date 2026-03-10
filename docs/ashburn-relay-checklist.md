# Ashburn Relay / ip_echo Port Reachability Checklist

The validator exits when it can't verify UDP ports (8001, 9000, 9002, 9003) are
reachable from entrypoint servers. The ip_echo protocol: validator TCP-connects
to entrypoint on port 8001, entrypoint sees source IP, sends UDP probes back to
that IP on the validator's ports. If probes don't arrive, validator crashes.

## Layer 1: Biscayne outbound path

Validator's outbound ip_echo TCP (dport 8001) must exit via GRE tunnel so
entrypoints see `137.239.194.65`, not biscayne's real IP via Docker MASQUERADE.

```
[ ] 1.1  Mangle rules (4 rules in mangle PREROUTING):
         - udp sport 8001        (gossip outbound)
         - udp sport 9000:9025   (TVU/repair outbound)
         - tcp sport 8001        (gossip TCP outbound)
         - tcp dport 8001        (ip_echo outbound — THE CRITICAL ONE)

[ ] 1.2  SNAT rule at position 1 (before Docker MASQUERADE):
         POSTROUTING -m mark --mark 100 -j SNAT --to-source 137.239.194.65

[ ] 1.3  Policy routing rule:
         fwmark 0x64 lookup ashburn

[ ] 1.4  Ashburn routing table default route:
         default via 169.254.100.0 dev gre-ashburn

[ ] 1.5  Mangle counters incrementing (pkts/bytes on tcp dport 8001 rule)
```

## Layer 2: GRE tunnel (biscayne ↔ mia-sw01)

```
[ ] 2.1  Tunnel exists and UP:
         gre-ashburn with 169.254.100.1/31

[ ] 2.2  Tunnel peer reachable:
         ping 169.254.100.0

[ ] 2.3  Ashburn IP on loopback:
         137.239.194.65/32 dev lo
```

## Layer 3: Biscayne inbound path (DNAT + DOCKER-USER)

Entrypoint UDP probes arrive at `137.239.194.65` and must reach kind node
`172.20.0.2`.

```
[ ] 3.1  DNAT rules at position 1 in nat PREROUTING
         (before Docker's ADDRTYPE LOCAL rule):
         - udp dport 8001       → 172.20.0.2:8001
         - tcp dport 8001       → 172.20.0.2:8001
         - udp dport 9000:9025  → 172.20.0.2

[ ] 3.2  DOCKER-USER ACCEPT rules (3 rules):
         - udp dport 8001       → ACCEPT
         - tcp dport 8001       → ACCEPT
         - udp dport 9000:9025  → ACCEPT

[ ] 3.3  DNAT counters incrementing
```

## Layer 4: mia-sw01

```
[ ] 4.1  Tunnel100 UP in VRF relay
         src 209.42.167.137, dst 186.233.184.235, link 169.254.100.0/31

[ ] 4.2  VRF relay default route:
         0.0.0.0/0 egress-vrf default 172.16.1.188

[ ] 4.3  Default VRF route to relay IP:
         137.239.194.65/32 egress-vrf relay 169.254.100.1

[ ] 4.4  ACL SEC-VALIDATOR-100-IN permits all needed traffic

[ ] 4.5  Backbone Et4/1 UP (172.16.1.189/31)
```

## Layer 5: was-sw01

```
[ ] 5.1  Static route: 137.239.194.65/32 via 172.16.1.189

[ ] 5.2  Backbone Et4/1 UP (172.16.1.188/31)

[ ] 5.3  No Loopback101 (removed to avoid absorbing traffic locally)
```

## Layer 6: Persistence

```
[ ] 6.1  ashburn-relay.service enabled and active (runs After=docker.service)

[ ] 6.2  /usr/local/sbin/ashburn-relay-setup.sh exists
```

## Layer 7: End-to-end tests

All tests run via Ansible playbooks. The test scripts in `scripts/` are
utilities invoked by the playbooks — never run them manually via SSH.

```
[ ] 7.1  relay-test-tcp-dport.py (via ashburn-relay-check.yml or ad-hoc play)
         Tests: outbound tcp dport 8001 mangle → SNAT → tunnel
         Pass:  entrypoint sees 137.239.194.65
         Fail:  entrypoint sees 186.233.184.235 (Docker MASQUERADE)

[ ] 7.2  relay-test-ip-echo.py (via ashburn-relay-check.yml or ad-hoc play)
         Tests: FULL END-TO-END (outbound SNAT + inbound DNAT + DOCKER-USER)
         Pass:  UDP probe received from entrypoint
         Fail:  no UDP probes — inbound path broken

[ ] 7.3  relay-inbound-udp-test.yml (cross-inventory: biscayne + kelce)
         Tests: inbound UDP from external host → DNAT → kind node
         Pass:  UDP arrives in kind netns
```

## Playbooks

```bash
# Read-only check of all relay state (biscayne + both switches):
ansible-playbook -i inventory-switches/switches.yml \
  -i inventory/biscayne.yml playbooks/ashburn-relay-check.yml

# Apply all biscayne relay rules (idempotent):
ansible-playbook -i inventory/biscayne.yml playbooks/ashburn-relay-biscayne.yml

# Apply outbound only (the ip_echo fix):
ansible-playbook -i inventory/biscayne.yml \
  playbooks/ashburn-relay-biscayne.yml -t outbound

# Apply inbound only (DNAT + DOCKER-USER):
ansible-playbook -i inventory/biscayne.yml \
  playbooks/ashburn-relay-biscayne.yml -t inbound

# Apply mia-sw01 config:
ansible-playbook -i inventory-switches/switches.yml \
  playbooks/ashburn-relay-mia-sw01.yml

# Apply was-sw01 config:
ansible-playbook -i inventory-switches/switches.yml \
  playbooks/ashburn-relay-was-sw01.yml

# Cross-inventory inbound UDP test (biscayne + kelce):
ansible-playbook -i inventory/biscayne.yml -i inventory/kelce.yml \
  playbooks/relay-inbound-udp-test.yml
```

## Historical root causes

1. **TCP dport 8001 mangle rule missing** — ip_echo TCP exits via Docker
   MASQUERADE, entrypoint sees wrong IP, UDP probes go to wrong address.

2. **DOCKER-USER ACCEPT rules missing** — DNAT'd traffic hits Docker's FORWARD
   DROP policy, never reaches kind node.

3. **DNAT rule position wrong** — Docker's `ADDRTYPE LOCAL` rule in PREROUTING
   catches traffic to loopback IPs before our DNAT rules. Must use `-I
   PREROUTING 1`.

4. **mia-sw01 egress-vrf route with interface specified** — silently fails in
   EOS (accepted in config, never installed in RIB). Must use nexthop-only form.

5. **was-sw01 Loopback101 absorbing traffic** — local delivery instead of
   forwarding to mia-sw01 via backbone.
