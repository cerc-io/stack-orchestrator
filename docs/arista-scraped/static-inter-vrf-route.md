<!-- Source: https://www.arista.com/en/um-eos/eos-static-inter-vrf-route -->
<!-- Scraped: 2026-03-06T20:43:17.977Z -->

# Static Inter-VRF Route


The Static Inter-VRF Route feature adds support for static inter-VRF routes. This enables the configuration of routes to destinations in one ingress VRF with an ability to specify a next-hop in a different egress VRF through a static configuration.


You can configure static inter-VRF routes in default and non-default VRFs. A different
egress VRF is achieved by “tagging” the **next-hop** or **forwarding
via** with a reference to an egress VRF (different from the source
VRF) in which that next-hop should be evaluated. Static inter-VRF routes
with ECMP next-hop sets in the same egress VRF or heterogenous egress VRFs
can be specified.


The Static Inter-VRF Route feature is independent and complementary to other mechanisms that can be used to setup local inter-VRF routes. The other supported mechanisms in EOS and the broader use-cases they support are documented here:

- [Inter-VRF Local Route Leaking using BGP VPN](/um-eos/eos-inter-vrf-local-route-leaking#xx1348142)

- [Inter-VRF Local Route Leaking using VRF-leak Agent](/um-eos/eos-inter-vrf-local-route-leaking#xx1346287)


## Configuration


The configuration to setup static-Inter VRF routes in an ingress (source) VRF to forward IP traffic to a different egress (target) VRF can be done in the following modes:

- This command creates a static route in one ingress VRF that points to a next-hop
in a different egress VRF.
ip | ipv6
route [vrf
vrf-name
destination-prefix [egress-vrf
egress-next-hop-vrf-name]
next-hop]


## Show Commands


Use the **show ip route vrf** to display the egress VRF name if it
differs from the source VRF.


**Example**
```
`switch# **show ip route vrf vrf1**

VRF: vrf1
Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B - BGP, B I - iBGP, B E - eBGP,
       R - RIP, I L1 - IS-IS level 1, I L2 - IS-IS level 2,
       O3 - OSPFv3, A B - BGP Aggregate, A O - OSPF Summary,
       NG - Nexthop Group Static Route, V - VXLAN Control Service,
       DH - DHCP client installed default route, M - Martian,
       DP - Dynamic Policy Route, L - VRF Leaked

Gateway of last resort is not set

 S        1.0.1.0/24 [1/0] via 1.0.0.2, Vlan2180 (egress VRF default)
 S        1.0.7.0/24 [1/0] via 1.0.6.2, Vlan2507 (egress VRF vrf3)`
```






## Limitations





            - For bidirectional traffic to work correctly between a pair of VRFs, static inter-VRF
                routes in both VRFs must be configured.

            - Static Inter-VRF routing is supported only in multi-agent routing protocol mode.
