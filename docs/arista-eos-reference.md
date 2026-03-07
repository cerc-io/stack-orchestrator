# Arista EOS Reference Notes

Collected from live switch CLI (`?` help) and Arista documentation search
results. Switch platform: 7280CR3A, EOS 4.34.0F.

## PBR (Policy-Based Routing)

EOS uses `policy-map type pbr` — NOT `traffic-policy` (which is a different
feature for ASIC-level traffic policies, not available on all platforms/modes).

### Syntax

```
! ACL to match traffic
ip access-list <ACL-NAME>
   10 permit <proto> <src> <dst> [ports]

! Class-map referencing the ACL
class-map type pbr match-any <CLASS-NAME>
   match ip access-group <ACL-NAME>

! Policy-map with nexthop redirect
policy-map type pbr <POLICY-NAME>
   class <CLASS-NAME>
      set nexthop <A.B.C.D>          ! direct nexthop IP
      set nexthop recursive <A.B.C.D> ! recursive resolution
      ! set nexthop-group <NAME>      ! nexthop group
      ! set ttl <value>               ! TTL override

! Apply on interface
interface <INTF>
   service-policy type pbr input <POLICY-NAME>
```

### PBR `set` options (from CLI `?`)

```
set ?
  nexthop        Next hop IP address for forwarding
  nexthop-group  next hop group name
  ttl            TTL effective with nexthop/nexthop-group
```

```
set nexthop ?
  A.B.C.D          next hop IP address
  A:B:C:D:E:F:G:H  next hop IPv6 address
  recursive        Enable Recursive Next hop resolution
```

**No VRF qualifier on `set nexthop`.** The nexthop must be reachable in the
VRF where the policy is applied. For cross-VRF PBR, use a static inter-VRF
route to make the nexthop reachable (see below).

## Static Inter-VRF Routes

Source: [EOS 4.34.0F - Static Inter-VRF Route](https://www.arista.com/en/um-eos/eos-static-inter-vrf-route)

Allows configuring a static route in one VRF with a nexthop evaluated in a
different VRF. Uses the `egress-vrf` keyword.

### Syntax

```
ip route vrf <ingress-vrf> <prefix>/<mask> egress-vrf <egress-vrf> <nexthop-ip>
ip route vrf <ingress-vrf> <prefix>/<mask> egress-vrf <egress-vrf> <interface>
```

### Examples (from Arista docs)

```
! Route in vrf1 with nexthop resolved in default VRF
ip route vrf vrf1 1.0.1.0/24 egress-vrf default 1.0.0.2

! show ip route vrf vrf1 output:
! S 1.0.1.0/24 [1/0] via 1.0.0.2, Vlan2180 (egress VRF default)
```

### Key points

- For bidirectional traffic, static inter-VRF routes must be configured in
  both VRFs.
- ECMP next-hop sets across same or heterogeneous egress VRFs are supported.
- The `show ip route vrf` output displays the egress VRF name when it differs
  from the source VRF.

## Inter-VRF Local Route Leaking

Source: [EOS 4.35.1F - Inter-VRF Local Route Leaking](https://www.arista.com/en/um-eos/eos-inter-vrf-local-route-leaking)

An alternative to static inter-VRF routes that leaks routes dynamically from
one VRF (source) to another VRF (destination) on the same router.

## Config Sessions

```
configure session <name>           ! enter named session
show session-config diffs          ! MUST be run from inside the session
commit timer HH:MM:SS              ! commit with auto-revert timer
abort                              ! discard session
```

From enable mode:
```
configure session <name> commit    ! finalize a pending session
```

## Checkpoints and Rollback

```
configure checkpoint save <name>
rollback running-config checkpoint <name>
write memory
```
