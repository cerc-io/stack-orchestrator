<!-- Source: https://www.arista.com/en/um-eos/eos-inter-vrf-local-route-leaking -->
<!-- Scraped: 2026-03-06T20:43:28.363Z -->

# Inter-VRF Local Route Leaking


Inter-VRF local route leaking allows the leaking of routes from one VRF (the source VRF) to
another VRF (the destination VRF) on the same router.
Inter-VRF routes can exist in any VRF (including the
default VRF) on the system. Routes can be leaked using the
following methods:

- Inter-VRF Local Route Leaking using BGP
VPN

- Inter-VRF Local Route Leaking using VRF-leak
Agent


## Inter-VRF Local Route Leaking using BGP VPN


Inter-VRF local route leaking allows the user to export and import routes from one VRF to another
on the same device. This is implemented by exporting routes from a VRF to the local VPN table
using the route target extended community list and importing the same route target extended
community lists from the local VPN table into the target VRF. VRF route leaking is supported
on VPN-IPv4, VPN-IPv6, and EVPN types.


Figure 1. Inter-VRF Local Route Leaking using Local VPN Table


### Accessing Shared Resources Across VPNs


To access shared resources across VPNs, all the routes from the shared services VRF must be
leaked into each of the VPN VRFs, and customer routes must be leaked into the shared
services VRF for return traffic. Accessing shared resources allows the route target of the
shared services VRF to be exported into all customer VRFs, and allows the shared services
VRF to import route targets from customers A and B. The following figure shows how to
provide customers, corresponding to multiple VPN domains, access to services like DHCP
available in the shared VRF.


Route leaking across the VRFs is supported
on VPN-IPv4, VPN-IPv6, and EVPN.


Figure 2. Accessing Shared Resources Across VPNs


### Configuring Inter-VRF Local Route Leaking


Inter-VRF local route leaking is configured using VPN-IPv4, VPN-IPv6, and EVPN. Prefixes can be
exported and imported using any of the configured VPN types. Ensure that the same VPN
type that is exported is used while importing.


Leaking unicast IPv4 or IPv6 prefixes is supported and achieved by exporting prefixes locally to
the VPN table and importing locally from the VPN table into the target VRF on the same
device as shown in the figure titled **Inter-VRF Local Route Leaking using Local VPN
Table** using the **route-target** command.


Exporting or importing the routes to or from the EVPN table is accomplished with the following
two methods:

- Using VXLAN for encapsulation

- Using MPLS for encapsulation


#### Using VXLAN for Encapsulation


To use VXLAN encapsulation type, make sure that VRF to VNI mapping is present and the interface
status for the VXLAN interface is up. This is the default encapsulation type for
EVPN.


**Example**


The configuration for VXLAN encapsulation type is as
follows:
```
`switch(config)# **router bgp 65001**
switch(config-router-bgp)# **address-family evpn**
switch(config-router-bgp-af)# **neighbor default encapsulation VXLAN next-hop-self source-interface Loopback0**
switch(config)# **hardware tcam**
switch(config-hw-tcam)# **system profile VXLAN-routing**
switch(config-hw-tcam)# **interface VXLAN1**
switch(config-hw-tcam-if-Vx1)# **VXLAN source-interface Loopback0**
switch(config-hw-tcam-if-Vx1)# **VXLAN udp-port 4789**
switch(config-hw-tcam-if-Vx1)# **VXLAN vrf vrf-blue vni 20001**
switch(config-hw-tcam-if-Vx1)# **VXLAN vrf vrf-red vni 10001**`
```


#### Using MPLS for Encapsulation


To use MPLS encapsulation type to export
to the EVPN table, MPLS needs to be enabled globally on the device and
the encapsulation method needs to be changed from default type, that
is VXLAN to MPLS under the EVPN address-family sub-mode.


**Example**
```
`switch(config)# **router bgp 65001**
switch(config-router-bgp)# **address-family evpn**
switch(config-router-bgp-af)# **neighbor default encapsulation mpls next-hop-self source-interface Loopback0**`
```


### Route-Distinguisher


Route-Distinguisher (RD) uniquely identifies routes from a particular VRF.
Route-Distinguisher is configured for every VRF from which routes are exported from or
imported into.


The following commands are used to configure Route-Distinguisher for a VRF.


```
`switch(config-router-bgp)# **vrf vrf-services**
switch(config-router-bgp-vrf-vrf-services)# **rd 1.0.0.1:1**

switch(config-router-bgp)# **vrf vrf-blue**
switch(config-router-bgp-vrf-vrf-blue)# **rd 2.0.0.1:2**`
```


### Exporting Routes from a VRF


Use the **route-target export** command to export routes from a VRF to the
local VPN or EVPN table using the route target
extended community list.


**Examples**

- These commands export routes from
**vrf-red** to the local VPN
table.
```
`switch(config)# **service routing protocols model multi-agent**
switch(config)# **mpls ip**
switch(config)# **router bgp 65001**
switch(config-router-bgp)# **vrf vrf-red**
switch(config-router-bgp-vrf-vrf-red)# **rd 1:1**
switch(config-router-bgp-vrf-vrf-red)# **route-target export vpn-ipv4 10:10**
switch(config-router-bgp-vrf-vrf-red)# **route-target export vpn-ipv6 10:20**`
```

- These commands export routes from
**vrf-red** to the EVPN
table.
```
`switch(config)# **router bgp 65001**
switch(config-router-bgp)# **vrf vrf-red**
switch(config-router-bgp-vrf-vrf-red)# **rd 1:1**
switch(config-router-bgp-vrf-vrf-red)# **route-target export evpn 10:1**`
```


### Importing Routes into a VRF


Use the **route-target import** command to import the exported routes from
the local VPN or EVPN table to the target VRF
using the route target extended community
list.


**Examples**

- These commands import routes from the VPN
table to
**vrf-blue**.
```
`switch(config)# **service routing protocols model multi-agent**
switch(config)# **mpls ip**
switch(config)# **router bgp 65001**
switch(config-router-bgp)# **vrf vrf-blue**
switch(config-router-bgp-vrf-vrf-blue)# **rd 2:2**
switch(config-router-bgp-vrf-vrf-blue)# **route-target import vpn-ipv4 10:10**
switch(config-router-bgp-vrf-vrf-blue)# **route-target import vpn-ipv6 10:20**`
```

- These commands import routes from the EVPN
table to
**vrf-blue**.
```
`switch(config)# **router bgp 65001**
switch(config-router-bgp)# **vrf vrf-blue**
switch(config-router-bgp-vrf-vrf-blue)# **rd 2:2**
switch(config-router-bgp-vrf-vrf-blue)# **route-target import evpn 10:1**`
```


### Exporting and Importing Routes using Route
Map


To manage VRF route leaking, control the export and import prefixes with route-map export or
import commands. The route map is effective only if the VRF or the VPN
paths are already candidates for export or import. The route-target
export or import commandmust be configured first. Setting BGP
attributes using route maps is effective only on the export end.


Note: Prefixes that are leaked are not re-exported to the VPN table from the target VRF.

**Examples**

- These commands export routes from
**vrf-red** to the local VPN
table.
```
`switch(config)# **service routing protocols model multi-agent**
switch(config)# **mpls ip**
switch(config)# **router bgp 65001**
switch(config-router-bgp)# **vrf vrf-red**
switch(config-router-bgp-vrf-vrf-red)# **rd 1:1**
switch(config-router-bgp-vrf-vrf-red)# **route-target export vpn-ipv4 10:10**
switch(config-router-bgp-vrf-vrf-red)# **route-target export vpn-ipv6 10:20**
switch(config-router-bgp-vrf-vrf-red)# **route-target export vpn-ipv4 route-map EXPORT_V4_ROUTES_T0_VPN_TABLE**
switch(config-router-bgp-vrf-vrf-red)# **route-target export vpn-ipv6 route-map EXPORT_V6_ROUTES_T0_VPN_TABLE**`
```

- These commands export routes to from
**vrf-red** to the EVPN
table.
```
`switch(config)# **router bgp 65001**
switch(config-router-bgp)# **vrf vrf-red**
switch(config-router-bgp-vrf-vrf-red)# **rd 1:1**
switch(config-router-bgp-vrf-vrf-red)# **route-target export evpn 10:1**
switch(config-router-bgp-vrf-vrf-red)# **route-target export evpn route-map EXPORT_ROUTES_T0_EVPN_TABLE**`
```

- These commands import routes from the VPN table to
**vrf-blue**.
```
`switch(config)# **service routing protocols model multi-agent**
switch(config)# **mpls ip**
switch(config)# **router bgp 65001**
switch(config-router-bgp)# **vrf vrf-blue**
switch(config-router-bgp-vrf-vrf-blue)# **rd 1:1**
switch(config-router-bgp-vrf-vrf-blue)# **route-target import vpn-ipv4 10:10**
switch(config-router-bgp-vrf-vrf-blue)# **route-target import vpn-ipv6 10:20**
switch(config-router-bgp-vrf-vrf-blue)# **route-target import vpn-ipv4 route-map IMPORT_V4_ROUTES_VPN_TABLE**
switch(config-router-bgp-vrf-vrf-blue)# **route-target import vpn-ipv6 route-map IMPORT_V6_ROUTES_VPN_TABLE**`
```

- These commands import routes from the EVPN table to
**vrf-blue**.
```
`switch(config)# **router bgp 65001**
switch(config-router-bgp)# **vrf vrf-blue**
switch(config-router-bgp-vrf-vrf-blue)# **rd 2:2**
switch(config-router-bgp-vrf-vrf-blue)# **route-target import evpn 10:1**
switch(config-router-bgp-vrf-vrf-blue)# **route-target import evpn route-map IMPORT_ROUTES_FROM_EVPN_TABLE**`
```


## Inter-VRF Local Route Leaking using VRF-leak
Agent


Inter-VRF local route leaking allows routes to leak from one VRF to another using a route
map as a VRF-leak agent. VRFs are leaked based on the preferences assigned to each
VRF.


### Configuring Route Maps


To leak routes from one VRF to another using a route map, use the [router general](/um-eos/eos-evpn-and-vcs-commands#xx1351777) command to enter Router-General
Configuration Mode, then enter the VRF submode for the destination VRF, and use the
[leak routes](/um-eos/eos-evpn-and-vcs-commands#reference_g2h_2z3_hwb) command to specify the source
VRF and the route map to be used. Routes in the source VRF that match the policy in the
route map will then be considered for leaking into the configuration-mode VRF. If two or
more policies specify leaking the same prefix to the same destination VRF, the route
with a higher (post-set-clause) distance and preference is chosen.


**Example**


These commands configure a route map to leak routes from **VRF1**
to **VRF2** using route map
**RM1**.
```
`switch(config)# **router general**
switch(config-router-general)# **vrf VRF2**
switch(config-router-general-vrf-VRF2)# **leak routes source-vrf VRF1 subscribe-policy RM1**
switch(config-router-general-vrf-VRF2)#`
```
