<!-- Source: https://www.arista.com/en/um-eos/eos-ipv4 -->
<!-- Scraped: 2026-03-06T20:51:21.912Z -->

# IPv4


Arista switches support Internet Protocol version 4 (IPv4) and Internet Protocol version 6 (IPv6)
for routing packets across network boundaries. This section describes
Arista’s implementation of IPv4 and includes these topics:

- IPv4 Addressing

- IPv4 Routing

- IPv4 Multicast Counters

- Route Management

- IPv4 Route Scale

- IP Source Guard

- DHCP Server

- DHCP Relay Global Configuration Mode

- DHCP Relay Across VRF

- DHCP Relay in VXLAN EVPN

- DHCP
Snooping with Bridging

- TCP MSS Clamping

- IPv4 GRE Tunneling

- GRE Tunneling Support

- BfRuntime to Use Non-default VRFs

- IPv4 Commands


## IPv4 Addressing


Each IPv4 network device is assigned a 32-bit IP address that identifies its network location.
These sections describe IPv4 address formats, data structures, configuration tasks, and
display options:

- IPv4 Address Formats

- IPv4 Address Configuration

- Address Resolution Protocol (ARP)

- Displaying ARP Entries


### IPv4 Address Formats


IPv4 addresses are composed of 32 bits, expressed in dotted decimal notation by four decimal
numbers, each ranging from **0** to
**255**. A subnet is identified by an IP address and an address
space defined by a routing prefix. The switch supports the following subnet formats:

- **IP address and subnet mask:** The subnet mask is a 32-bit number (dotted decimal
notation) that specifies the subnet address space. The subnet address space is calculated
by performing an AND operation between the IP address and subnet mask.

- **IP address and wildcard mask:** The wildcard mask is a 32-bit number (dotted
decimal notation) that specifies the subnet address space. Wildcard masks differ from
subnet masks in that the bits are inverted. Some commands use wildcard masks instead of
subnet masks.

- **CIDR notation:** CIDR notation specifies the scope of the subnet space by using a
decimal number to identify the number of leading ones in the routing prefix. When
referring to wildcard notation, CIDR notation specifies the number of leading zeros in the
routing prefix.


**Examples**

- These subnets (subnet mask and CIDR notation) are calculated
identically:
```
`10.24.154.13 255.255.255.0
10.24.154.13/24`
```

- The defined space includes all addresses between **10.24.154.0**
and **10.24.154.255**. These subnets (wildcard mask and CIDR
notation) are calculated
identically:
```
`124.17.3.142 0.0.0.15
124.17.3.142/28`
```


The defined space includes all addresses between
**124.17.3.128** and
**124.17.3.143**.


### IPv4 Address Configuration


#### Assigning an IPv4 Address to an
Interface


The [ip
address](/um-eos/eos-data-plane-security#xx1144036) command specifies the
IPv4 address of an interface and the mask for the subnet to
which the interface is
connected.

**Example**These commands configure
an IPv4 address with subnet mask for **VLAN
200**:
```
`switch(config)# **interface vlan 200**
switch(config-if-Vl200)# **ip address 10.0.0.1/24**
switch(config-if-Vl200)#`
```


#### Assigning an IPv4 Class E Address to an Interface


The ipvr
routable 240.0.0.0/4command
assigns a class E addresses to an interface. When
configured, the class E address traffic are routed through
BGP, OSPF, ISIS, RIP, static routes and programmed to the
FIB and kernel. By default, this command is disabled.


**Example**

- These commands configure an IPv4 Class E
(**240/4**) address to an
interface.
```
`switch(config)# **router general**
switch(config-router-general)# **ipv4 routable 240.0.0.0/4**`
```


#### Assigning a Secondary IPv4 Address to an Interface


The [**ip
address secondary**](/um-eos/eos-data-plane-security#xx1144036) command
assigns a secondary IPv4 address to an interface. Each
interface can have multiple secondary IPv4 addresses
assigned to it.


**Example**


- Use the following commands to enter Ethernet Interface
Configuration Mode and add a secondary IP address,
192.168.168.25/32, to Ethernet interface,
Ethernet7/30/2:

```
`switch(config)# **interface Ethernet7/30/2**
switch(config-if-Et7/30/2)# **ip address 192.168.168.25/32 secondary**
switch(config-if-Et7/30/2)#`
```


#### Detecting Duplicate IP Addresses on an Interface


The **ip address duplicate detection
disabled** command detects any
duplicate IP address on the interface. When the switch
detects the duplicate IP address, EOS generates a syslog
message. It helps the network operator to identify IP
addresses misconfiguration. By default, this feature is
enabled.


Note: This feature supports detecting
duplicate virtual IP, VARP, and VRRP addresses.


**Examples**

- This command disables the feature on the
switch.
```
`switch(config)# **ip address duplicate detection disabled**`
```

- This command enables the
feature.
```
`switch(config)# **ip address duplicate detection logging**`
```

Note: Use
the commands in global configuration mode and not
per VRF.


This is an example of a Syslog message, when a duplicate IP address
is detected.


```
`Mar 24 16:41:57 cd290 Arp: %INTF-4-DUPLICATE_ADDRESS_WITH_HOST: IP address 100.1.1.2
configured on interface Ethernet1/1 is in use by a host with
MAC address 00:00:01:01:00:00 on interface Ethernet1/1 in VRF default`
```


### Address Resolution Protocol
(ARP)


Address Resolution Protocol (ARP) maps IP addresses to MAC addresses recognized by
the local network devices. The ARP cache consists of a table that stores the
correlated addresses of the devices that the router facilitates data
transmissions.


After receiving a packet, routers use ARP to find the device MAC address assigned to
the packet destination IP address. If the ARP cache contains both addresses, the
router sends the packet to the specified port. If the ARP cache does not contain
the addresses, ARP broadcasts a request packet to all devices in the subnet. The
device at the requested IP address responds and provides its MAC address. ARP
updates the ARP cache with a dynamic entry and forwards the packet to the
responding device. Add static ARP entries to the cache using the CLI.


#### Proxy ARP



Proxy ARP enables a network device (proxy) to respond to ARP requests for network addresses on a
different network with its MAC address. Traffic to the destination directs
to the proxy device which then routes the traffic toward the ultimate
destination.


#### Configuring ARP


The switch uses ARP cache entries to correlate 32-bit IP addresses to 48-bit hardware addresses.
The arp aging
timeout command specifies the duration of
dynamic address entries in the Address Resolution Protocol (ARP) cache for
addresses learned through the Layer 3 interface. The default duration is
**14400** seconds (four hours).



Entries refresh and expire at a random time within the range of
**80%-100%** of the cache expiry time. The
refresh attempts three times at an interval of **2%**
of the configured timeout.


Static ARP entries never time out and
must be removed from the table manually.


**Example**


This command specifies an ARP cache duration of **7200**
seconds (two hours) for dynamic addresses added to the ARP cache learned
through **VLAN
200**.
```
`switch(config)# **interface vlan 200**
switch(config-if-Vl200)# **arp aging timeout 7200**
switch(config-if-Vl200)# **show active**
interface Vlan200
   arp aging timeout 7200
switch(config-if-Vl200)#`
```


The **arp** command adds a static entry to an
Address Resolution Protocol (ARP) cache.


**Example**


This command adds a static entry to the ARP cache in the default
VRF.
```
`switch(config)# **arp 172.22.30.52 0025.900e.c63c arpa**
switch(config)#`
```


The arp proxy
max-delay command enables delaying proxy ARP
requests on the configuration mode interface. EOS disables Proxy ARP by
default. When enabled, the switch responds to all ARP requests, including
gratuitous ARP requests, with target IP addresses that match a route in the
routing table. When a switch receives a proxy ARP request, EOS performs a
check to send the response immediately or delay the response based on the
configured maximum delay in milliseconds (ms).


**Example**


Use the following command to set a delay of *500ms* before returning a
response to a proxy ARP
request.
```
`switch(config)# **arp proxy max-delay 500ms**`
```


#### Gratuitous ARP


EOS broadcasts gratuitous ARP packets using a device in response to an internal change rather
than as a response to an ARP request. The gratuitous ARP packet consists of
a request packet (no reply expected) that supplies an unrequested update of
ARP information. In a gratuitous ARP packet, both the source and destination
IP addresses use the IP of the sender, and the destination MAC address uses
the broadcast address (**ff:ff:ff:ff:ff:ff**).


Gratuitous ARP packets generate to update ARP tables after an IPv4 address or a MAC address
change occurs.


##### Configuring Gratuitous ARP


By default, Arista switch interfaces reject gratuitous ARP request packets. The arp gratuitous
accept command configures an L3
interface to accept the gratuitous ARP request packets sent from a
different device in the network and add the mappings to the ARP
table. Gratuitous ARP can be configured on Ethernet interfaces,
VLANs/SVI, or L3 port channels, but has no effect on L2
interfaces.


**Example**


These commands enable gratuitous ARP packet acceptance on
**interface ethernet
2/1**.
```
`switch (config)# **interface ethernet 2/1**
switch (config-if-Et2/1)# **arp gratuitous accept**`
```


### Displaying ARP Entries


The show ip arp command displays ARP cache entries that map an IP address
to a corresponding MAC address. The table displays addresses by their
host names when the command includes the
**resolve** argument.


**Examples**

- This command displays ARP cache entries that map MAC
addresses to IPv4
addresses.
```
`switch> **show ip arp**

Address         Age (min)  Hardware Addr   Interface
172.25.0.2              0  004c.6211.021e  Vlan101, Port-Channel2
172.22.0.1              0  004c.6214.3699  Vlan1000, Port-Channel1
172.22.0.2              0  004c.6219.a0f3  Vlan1000, Port-Channel1
172.22.0.3              0  0045.4942.a32c  Vlan1000, Ethernet33
172.22.0.5              0  f012.3118.c09d  Vlan1000, Port-Channel1
172.22.0.6              0  00e1.d11a.a1eb  Vlan1000, Ethernet5
172.22.0.7              0  004f.e320.cd23  Vlan1000, Ethernet6
172.22.0.8              0  0032.48da.f9d9  Vlan1000, Ethernet37
172.22.0.9              0  0018.910a.1fc5  Vlan1000, Ethernet29
172.22.0.11             0  0056.cbe9.8510  Vlan1000, Ethernet26

switch>`
```

- This command displays ARP cache entries that map MAC
addresses to IPv4 addresses. The output displays
host names assigned to IP addresses in place of
the
address.
```
`switch> **show ip arp resolve**

Address         Age (min)  Hardware Addr   Interface
green-vl101.new         0  004c.6211.021e  Vlan101, Port-Channel2
172.22.0.1              0  004c.6214.3699  Vlan1000, Port-Channel1
orange-vl1000.n         0  004c.6219.a0f3  Vlan1000, Port-Channel1
172.22.0.3              0  0045.4942.a32c  Vlan1000, Ethernet33
purple.newcompa         0  f012.3118.c09d  Vlan1000, Port-Channel1
pink.newcompany         0  00e1.d11a.a1eb  Vlan1000, Ethernet5
yellow.newcompa         0  004f.e320.cd23  Vlan1000, Ethernet6
172.22.0.8              0  0032.48da.f9d9  Vlan1000, Ethernet37
royalblue.newco         0  0018.910a.1fc5  Vlan1000, Ethernet29
172.22.0.11             0  0056.cbe9.8510  Vlan1000, Ethernet26

switch>`
```


#### ARP Inspection


The Address Resolution Protocol (ARP) inspection command ip arp
inspection vlan activates a
security feature that protects the network from ARP spoofing. EOS
intercepts ARP requests and responses on untrusted interfaces on
specified VLANs and verifies intercepted packets to ensure valid
IP-MAC address bindings. On trusted interfaces, all incoming ARP
packets process and forward without verification, and all invalid ARP
packets are dropped.


##### Enabling and Disabling ARP Inspection


By default, EOS disables ARP inspection on all VLANs.


**Examples**

- This command enables ARP inspection on VLANs
**1** through
**150**.
```
`switch(config)# **ip arp inspection vlan 1 - 150**
switch(config)#`
```

- This command disables ARP inspection on VLANs
**1** through
**150**.
```
`switch(config)# **no ip arp inspection vlan 1 - 150**
switch(config)#`
```

- This command sets the ARP inspection default
to VLANs **1** through
**150**.
```
`switch(config)# **default ip arp inspection vlan 1 - 150**
switch(config)#`
```

- This command enable ARP inspection on multiple
VLANs **1** through
**150** and
**200** through
**250**.
```
`switch(config)# **ip arp inspection vlan 1-150,200-250**
switch(config)#`
```


##### Syslog for Invalid ARP Packets
Dropped


After dropping an invalid ARP packet, EOS
displays the following syslog message appears. The log
severity level can be set higher if required.


```
`%SECURITY-4-ARP_PACKET_DROPPED: Dropped ARP packet on interface Ethernet28/1 Vlan
2121 because invalid mac and ip binding. Received: 00:0a:00:bc:00:de/1.1.1.1.`
```


##### Displaying ARP Inspection States


The command show ip arp inspection vlan displays the configuration and
operation state of ARP inspection. For a VLAN range
specified by **show ip arp inspection
vlan**displays only VLANs with ARP
inspection enabled. If you do not specify a VLAN, the output
displays all VLANs with ARP inspection enabled. The
operation state turns to **Active** when the hardware
traps ARP packets for inspection.


**Example**


This command displays the configuration and operation state of ARP
inspection for VLANs **1** through
**150**.
```
`switch(config)# **show ip arp inspection vlan 1 - 150**

VLAN 1
----------
Configuration
: Enabled
Operation State : Active
VLAN 2
----------
Configuration
: Enabled
Operation State : Active
{...}
VLAN 150
----------
Configuration
: Enabled
Operation State : Active

switch(config)#`
```


##### Displaying ARP Inspection Statistics


The command show ip arp inspection statistics displays the statistics
of inspected ARP packets. For a VLAN specified by
**show ip arp inspection
vlan**, the output displays only VLANs
with ARP inspection. If you do not specify a VLAN, the
output displays all VLANs with ARP inspection enabled.


The command clear arp inspection statistics clears ARP inspection.


**Examples**

- This command displays ARP inspection
statistics for **VLAN
1**.
```
`switch(config)# **show ip arp inspection statistics vlan 2**

Vlan : 2
------------
ARP Req Forwarded = 20
ARP Res Forwarded = 20
ARP Req Dropped = 1
ARP Res Dropped = 1

Last invalid ARP:
Time: 10:20:30 ( 5 minutes ago )
Reason: Bad IP/Mac match
Received on: Ethernet 3/1
Packet:
  Source MAC: 00:01:00:01:00:01
  Dest MAC: 00:02:00:02:00:02
  ARP Type: Request
  ARP Sender MAC: 00:01:00:01:00:01
  ARP Sender IP: 1.1.1

switch(config)#`
```

- This command displays ARP inspection
statistics for **ethernet interface
3/1**.
```
`switch(config)# **show ip arp inspection statistics ethernet interface 3/1**

Interface : 3/1
--------
ARP Req Forwarded = 10
ARP Res Forwarded = 10
ARP Req Dropped = 1
ARP Res Dropped = 1

Last invalid ARP:
Time: 10:20:30 ( 5 minutes ago )
Reason: Bad IP/Mac match
Received on: VLAN 10
Packet:
  Source MAC: 00:01:00:01:00:01
  Dest MAC: 00:02:00:02:00:02
  ARP Type: Request
  ARP Sender MAC: 00:01:00:01:00:01
  ARP Sender IP: 1.1.1

switch(config)#`
```

- This command clears ARP inspection
statistics.
```
`switch(config)# **clear arp inspection statistics**
switch(config)#`
```


##### Configuring Trust Interface


By default, all interfaces are untrusted. The command ip arp inspection trust
configures the trust state of an interface.


**Examples**

- This command configures the trust state of an
interface.
```
`switch(config)# **ip arp inspection trust**
switch(config)#`
```

- This command configures the trust state of an
interface to
untrusted.
```
`switch(config)# **no ip arp inspection trust**
switch(config)#`
```

- This command configures the trust state of an
interface to the
default.
```
`switch(config)# **default ip arp inspection trust**
switch(config)#`
```


##### Configuring Rate Limit


After enabling ARP inspection, EOS traps ARP packets to the CPU. When the incoming ARP rate
exceeds expectations, two actions can be taken. For
notification purposes, the command ip arp inspection logging
enables logging of incoming ARP packets. The command ip arp inspection limit
disables the interfaces and prevents a denial-of-service
attack..


**Examples**

- This command enables logging of incoming ARP
packets when the rate exceeds the configured value
and sets the rate to
**2048**, the upper limit
for the number of invalid ARP packets allowed per
second. Then, it sets the burst consecutive
interval to monitor interface for a high ARP rate
to **15** seconds.

```
`switch(config)# **ip arp inspection logging rate 2048 burst interval 15**
switch(config)#`
```

- This command configures the rate limit of
incoming ARP packets to disable the interface when
the incoming ARP rate exceeds the configured
value, and sets the rate to
**512**, the upper limit for
the number of invalid ARP packets allowed per
second. Then sets the burst consecutive interval
to monitor the interface for a high ARP rate to
**11** seconds.

```
`switch(config)# **ip arp inspection limit rate 512 burst interval 11**
switch(config)#`
```

- This command displays verification of the
interface specific configuration.

```
`switch(config)# **interface ethernet 3/1**
switch(config)# **ip arp inspection limit rate 20 burst interval 5**
switch(config)# **interface Ethernet 3/3**
switch(config)# **ip arp inspection trust**
switch(config)# **show ip arp inspection interfaces**

 Interface      Trust State  Rate (pps) Burst Interval
 -------------  -----------  ---------- --------------
 Et3/1          Untrusted    20         5
 Et3/3          Trusted      None       N/A

switch(config)#`
```


##### Disabling Errors Caused by ARP Inspection


If the incoming ARP packet rate on an interface exceeds the configured rate limit in burst
interval, EOS disables the interface by default. If
errdisabled, the interface remains in this state until you
intervene with the command **errdisable detect
cause arp-inspection**. For example,
after you perform a **shutdown** or
**no shutdown** of the
interface or it automatically recovers after a certain time
period. The command **errdisable recovery cause
arp-inspection** enables auto
recovery. The command **errdisable recovery
interval** enables sharing the auto
recovery interval among all disabled interfaces. See the
chapter [Data Transfer Introduction](/um-eos/eos-data-transfer#xx1133499) for information on all
**errdisable** commands.


**Examples**

- This command enables errdisable caused by an
ARP inspection
violation.
```
`switch(config)# **errdisable detect cause arp-inspection**
switch(config)#`
```

- This command disables errdisable caused by an
ARP inspection
violation.
```
`switch(config)# **no errdisable detect cause arp-inspection**
switch(config)#`
```

- This command enables auto
recovery.
```
`switch(config)# **errdisable recovery cause arp-inspection**
switch(config)#`
```

- This command disables auto
recovery.
```
`switch(config)# **no errdisable recovery cause arp-inspection**
switch(config)#`
```

- This command enables sharing the auto recovery
interval of **10** seconds
among all errdisable
interfaces.
```
`switch(config)# **errdisable recovery interval 10**
switch(config)#`
```

- This command disables sharing the auto
recovery interval of **10**
seconds among all errdisable
interfaces.
```
`switch(config)# **no errdisable recovery interval 10**
switch(config)#`
```

- This command displays the reason for a port
entering the errdisable
state.
```
`switch(config)# **show interfaces status errdisabled**

Port         Name         Status       Reason
------------ ------------ ------------ ---------------
Et3/2                     errdisabled  arp-inspection

switch(config)#`
```


##### Configuring Static IP MAC Binding


The ARP inspection command ip source binding allows you to add static
IP-MAC binding. If enabled, ARP inspection verifies incoming
ARP packets based on the configured IP-MAC bindings. The
static IP-MAC binding entry can only be configured on Layer
2 ports. By default, there is no binding entry on the
system.


**Examples**

- This command configures static IP-MAC binding
for IP address
**127.0.0.1,** MAC address
**0001.0001.0001**,
**vlan 1**, and Ethernet
interface **slot 4** and
**port
1**.
```
`switch(config)# **ip source binding 127.0.0.1 0001.0001.0001 vlan 1 interface
ethernet 4/1**
switch(config)#`
```

- This command configures static IP-MAC binding
for IP address
**127.0.0.1**, MAC address
**0001.0001.0001**,
**vlan 1**, and
**port-channel interface
20**.
```
`switch(config)# **ip source binding 127.0.0.1 0001.0001.0001 vlan 1 interface
port-channel 20**
switch(config)#`
```

- This command displays the configured IP-MAC
binding entries. Note that the Lease column
displays dynamic DHCP snooping binding entries.
For static binding entries, lease time displays as
infinite.
```
`switch(config)# **show ip source binding 127.0.0.1 0001.0001.0001 static vlan 1
interface port-channel 20**

MacAddress      IpAddress   Lease(sec)  Type   VLAN  Interface
--------------- ----------- ----------- ------ ----- --------------
0001.0001.0001  127.0.0.1   infinite    static 1     Port-Channel20

switch(config)#`
```


## IPv4 Routing


Internet Protocol version 4 (IPv4) is a communications protocol used for relaying network packets
across a set of connected networks using the Internet Protocol suite. Routing transmits
network layer data packets over connected independent subnets. Each subnet is assigned
an IP address range, and each device on the subnet is assigned an IP address from that
range. The connected subnets have IP address ranges that do not overlap.


A router is a network device that connects
multiple subnets. Routers forward inbound packets to the subnet whose
address range includes the packets’ destination address. IPv4 and IPv6
are internet layer protocols that define packet-switched internetworking,
including source-to-destination datagram transmission across multiple
networks.


These sections describe IPv4 routing and route creation options:

- Enabling IPv4 Routing

- Static and Default IPv4 Routes

- Dynamic IPv4 Routes

- Viewing IPv4 Routes and Network Components


### Enabling IPv4 Routing


When IPv4 routing is enabled, the switch attempts to deliver inbound packets to destination IPv4
addresses by forwarding them to interfaces or next-hop addresses specified
by the forwarding table.


The ip routing command enables IPv4 routing.


**Example**


This command enables IP
routing:
```
`switch(config)# **ip routing**
switch(config)#`
```


### Static and Default IPv4 Routes


Static routes are entered through the CLI and are typically used when dynamic protocols cannot
establish routes to a specified destination prefix. Static routes are also useful when dynamic
routing protocols are not available or appropriate. Creating a static route associates a
destination IP address with a local interface. The routing table refers to these routes as
connected routes available for redistribution into routing domains defined by dynamic routing
protocols.


The ip route command creates a static route. The destination is a network
segment; the next-hop is either an IP address or a routable interface port. When multiple
routes exist to a destination prefix, the route with the lowest administrative distance takes
precedence.


By default, the administrative distance assigned to static routes is **1**.
Assigning a higher administrative distance to a static route
configures it to be overridden by dynamic routing data. For example, a
static route with a distance value of **200** is
overridden by OSPF intra-area routes, which have a default distance of
**110**.


A route tag is a 32-bit number that is attached to a route. Route maps use tags to filter routes.
Static routes have a default tag value of **0**.


**Example**


This command creates a static
route:
```
`switch(config)#**ip route 172.17.252.0/24 vlan 500**
switch(config)#`
```


#### Creating Default IPv4 Routes


The default route denotes the packet forwarding
rule that takes effect when no other route is configured for a specified
IPv4 address. All packets with destinations that are not established
in the routing table are sent to the destination specified by the default
route.


The IPv4 destination prefix is **0.0.0.0/0**, and the next-hop is the
default gateway.




**Example**


This command creates a default route and establishes
**192.14.0.4** as the default
gateway
address:
```
`switch(config)#**ip route 0.0.0.0/0 192.14.0.4**
switch(config)#`
```


#### Resolution RIB Profiles for Static Routes


Specify a Resolution RIB Profile as a system-connected per next-hop for a
static route. System-connected describes a static route that only resolves if the next hop
can be reached over a connected route. If you do not specify a system-connected route, the
static route resolves if the next hop can be reached over any type of route in the FIB,
including a connected route or a tunnel RIB. route.


**Configuring Resolution RIB Profile for Static Routes**


Use the following command to configure a Resolution RIB Profile for static route, 10.0.0.0/24, and 10.1.0.0:


```
`switch(config)#**ip route vrf myVRF 10.0.0.0/24 10.1.0.0 resolution ribs system-connected**`
```


**Displaying Resolution Profiles for Static Routes**


Use the **show ip route** command:


```
`switch(config)#**show ip route**
interface Ethernet1
   mtu 1500
   no switchport
   ip address 10.1.1.1/24
 !
interface Ethernet2
   no switchport
   ip address 10.10.10.1/24

ip route 10.100.100.0/24 10.10.10.2 resolution ribs system-connected
 !
arp 10.1.1.2 00:22:33:44:55:66 arpa
arp 10.10.10.2 00:22:33:44:55:67 arpa
 !
mpls tunnel static st1 10.10.10.2/32 10.1.1.2 Ethernet1 label-stack 9000`
```


### Dynamic IPv4 Routes


Dynamic routing protocols establish dynamic routes. These protocols also maintain the routing
table and modify routes to adjust for topology or traffic changes. Routing protocols
assist the switch in communicating with other devices to exchange network information,
maintaining routing tables, and establishing data paths.


The switch supports these dynamic IPv4
routing protocols:


- [OSPFv2 Introduction](/um-eos/eos-open-shortest-path-first-version-2#xzx_XvxFOLC7zF)

- [Border Gateway Protocol (BGP)](/um-eos/eos-border-gateway-protocol-bgp)

- [Routing Information Protocol (RIP)](/um-eos/eos-routing-information-protocol-rip)

- [IS-IS](/um-eos/eos-is-is)


### Viewing IPv4 Routes and Network
Components


#### Displaying the FIB and Routing Table


The show ip route command displays routing table entries that are in the
forwarding information base (FIB), including static routes, routes to directly connected
networks, and dynamically learned routes. Multiple equal-cost paths to the same prefix are
displayed contiguously as a block, with the destination prefix displayed only on the first
line.


The **show running-config** command displays configured commands not in the
FIB. The show ip route summary command displays the number of
routes, categorized by source, in the routing table.


**Examples**

- This command displays IP routes learned through
BGP.
```
`switch> **show ip route bgp**

Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B I - iBGP, B E - eBGP,
       R - RIP, A - Aggregate

 B E    170.44.48.0/23 [20/0] via 170.44.254.78
 B E    170.44.50.0/23 [20/0] via 170.44.254.78
 B E    170.44.52.0/23 [20/0] via 170.44.254.78
 B E    170.44.54.0/23 [20/0] via 170.44.254.78
 B E    170.44.254.112/30 [20/0] via 170.44.254.78
 B E    170.53.0.34/32 [1/0] via 170.44.254.78
 B I    170.53.0.35/32 [1/0] via 170.44.254.2
                             via 170.44.254.13
                             via 170.44.254.20
                             via 170.44.254.67
                             via 170.44.254.35
                             via 170.44.254.98

switch>`
```

- This command displays a summary of routing table
contents.
```
`switch> **show ip route summary**

Route Source         Number Of Routes
-------------------------------------
connected                   15
static                       0
ospf                        74
  Intra-area: 32 Inter-area:33 External-1:0 External-2:9
  NSSA External-1:0 NSSA External-2:0
bgp                          7
  External: 6 Internal: 1
internal                    45
attached                    18
aggregate                    0

switch>`
```


#### Displaying the IP Route Age


The show ip route age command displays the time when the route for the
specified network was present in the routing table. It does not
account for changes in parameters like metrics, next hop etc.


**Example:**


This command displays the time since the last update to ip route
**172.17.0.0/20**.
```
`switch> **show ip route 172.17.0.0/20 age**

Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B I - iBGP, B E - eBGP,
       R - RIP, I - ISIS, A - Aggregate

 B E    172.17.0.0/20 via 172.25.0.1, **age 3d01h**

switch>`
```


#### Displaying Gateways


A gateway is a router that provides access to another network. The gateway of last resort, also
known as the default route, is the route that a packet uses when the route to its
destination address is unknown. The IPv4 default route in is
**0.0.0.0/0**.


The show ip route gateway command displays IP addresses of all gateways
(next hops) used by active routes.


**Example**


This command displays next hops used by active
routes.
```
`switch> **show ip route gateway**

The following gateways are in use:
   172.25.0.1 Vlan101
   172.17.253.2 Vlan2000
   172.17.254.2 Vlan2201
   172.17.254.11 Vlan2302
   172.17.254.13 Vlan2302
   172.17.254.17 Vlan2303
   172.17.254.20 Vlan2303
   172.17.254.66 Vlan2418
   172.17.254.67 Vlan2418
   172.17.254.68 Vlan2768
   172.17.254.29 Vlan3020

switch>`
```


#### Displaying Host Routes


The show ip route host command displays all host routes in the host
forwarding table. Host routes are those whose destination prefix is the entire address (mask
= **255.255.255.255** or prefix = **/32**). Each
displayed host route is labeled with its purpose:


- **F**      static routes from the FIB.

- **R**     routes defined because the IP address is an interface address.

- **B**      broadcast address.

- **A**      routes to any neighboring host for which the switch has an ARP
entry.


**Example**


This command displays all host routes in the host forwarding
table.
```
`switch# **show ip route host**

R - receive B - broadcast F - FIB, A - attached

F   127.0.0.1 to cpu
B   172.17.252.0 to cpu
A   172.17.253.2 on Vlan2000
R   172.17.253.3 to cpu
A   172.17.253.10 on Vlan2000
R   172.17.254.1 to cpu
A   172.17.254.2 on Vlan2901
B   172.17.254.3 to cpu
B   172.17.254.8 to cpu
A   172.17.254.11 on Vlan2902
R   172.17.254.12 to cpu

F   172.26.0.28 via 172.17.254.20 on Vlan3003
                via 172.17.254.67 on Vlan3008
                via 172.17.254.98 on Vlan3492
via 172.17.254.86 on Vlan3884
                via 172.17.253.2 on Vlan3000
F   172.26.0.29 via 172.25.0.1 on Vlan101
F   172.26.0.30 via 172.17.254.29 on Vlan3910
F   172.26.0.31 via 172.17.254.33 on Vlan3911
F   172.26.0.32 via 172.17.254.105 on Vlan3912

switch#`
```


## IPv4 Multicast Counters


IPv4 multicast counters allow
association of IPv4 multicast routes with a packet or byte counter.


This chapter contains the following sections.

- Multicast Counters Hardware Overview

- Multicast Counters iBGP and eBGP Configuration

- Configuring IPv4 Multicast Counters


### Multicast Counters Hardware
Overview


This section describes a hardware overview for multicast counters, and contains the following
sections.

- Platform Independent Requirements for Counters

- Policer Counter Overview

- BGP Functions Supported for Arista Switches

- Additional Requirements


#### Platform Independent Requirements
for Counters


The following platform independent requirements include:

- Enable/Disable counters.

- Clear counters.

- Show counters.

- Configure counter mode for byte (default) or frame mode.


#### Policer Counter Overview


The switch hardware has two policer banks, each with 4k entries, and each entry has one
32-bit entry1 and one 32-bit entry2, which can be used as either a packet counter or
byte counter.


In the pipeline, each bank can have one policer index coming from upstream blocks, which
means different features cannot update multiple policer entries in the same bank
simultaneously. Therefore, different features cannot share entries in the same bank.


Each FFU/BST entry points to a corresponding RAM in switch hardware routing. A policer
index is saved in the action ram, so when installing a multicast route into hardware,
the platform code will get a policer index and save it in the action field. A counter is
not added to the action field if a policer index is unavailable.


Switch hardware can have multiple features competing for the policer banks. It is
desirable to have a platform command to reserve policer banks dedicated to a certain
feature.


The following command reserves one or two policer banks to be used only by the named
feature:


**[no] platform fm6000 [nat|acl|qos|multicast] policer banks
<1|2>**


Available bank(s) are reserved for the feature. Otherwise the command will take effect at
the next reboot or FocalPointV2 agent restart. This reservation guarantees the
configured number of bank(s) for this feature. However, the feature can still possibly
obtain the other policer bank if it needs more, and the other bank is available.


If a feature has a pending reservation request which is not fulfilled because of
availability, and some other feature frees a bank, the bank will be allocated to the
pending feature.


#### BGP Functions Supported for
Arista Switches


Arista switches support these BGP functions:

- A single BGP instance

- Simultaneous internal (IBGP) and external (EBGP) peering

- Multiprotocol BGP

- BGP Confederations


#### Additional Requirements


On switch hardware, the following additional requirements include:

- Reservation of policer banks.

- Notification of policer bank availability when
a policer entry is freed by other features.


### Multicast Counters iBGP and
eBGP Configuration


This section describes the commands required to configure an iBGP and an eBGP topology, and
contains the following sections.

- Policer Usage


#### Policer Usage


There are two types of counters – those created by wildcard creation and by specific creation.
When a specific counter is required, and the hardware runs out
of policer entries, a wildcard counter is forced to give up its
policer entry.


Suppose the user configures a specific counter, and the Starter Group (SG) already has a
wildcard-created counter. In that case, this counter is upgraded
to a specific one, with no change in the hardware policer index.
If the user configures both a wildcard counter and a specific
counter for this SG and subsequently deletes the specific
counter, the counter for this SG is downgraded to a wildcard,
with no change in the hardware policer index. However, if
another specific counter is pending for a hardware policer
index, then this policer entry will be assigned to that counter
due to its higher precedence.


Even if a counter is configured by the user, in order to conserve the use
of hardware resources, do not allocate a policer entry until a
real route (G, S) is programmed into the Frame Filtering and
Forwarding Unit (FFU).


### Configuring IPv4 Multicast
Counters


Perform the following CLI steps
to configure IPv4 multicast counters on the FM6000 platform:


- Execute the global
configuration command:


- **no****|****default**
**ip multicast count**
**bytes****|**
**packets**


Enables wildcard counters. Also used to change bytes/packets mode. When
hardware runs of resources, specific creation has priority to preempt
counters from wildcard creation. The **bytes****|**
**packets** optional keyword enables the counter to be
in either bytes mode or packets mode. This mode applies to all counters. All
counter values will be reset to zero when the counter mode changes.


- **no****|****default**
**ip multicast count**
**<G> <S>**


This only takes effect when **ip multicast count** is
enabled. Either **<G> <S>** or
**bytes****|****packets**
optional keyword is used. They can not be used concurrently.


No | default Commands: (default is same
as no)


- **`no ip multicast count`** Deletes all multicast counters, including explicit
**<G> <S>** routes

- **`no ip multicast count`**
**<G> <S>** Removes
the config. Do not delete the counter because the
wildcard is still active.

- If no **<G, S>** is specified,
all multicast routes will have counters unless the hardware
runs out of resources. The creation of counters is referred
to as “wildcard creation.”

- If **<G, S>** is specified, only
**<G, S>** will get a
counter (and no other route). The creation of counters is
referred to as “specific creation.” By default, all mcast
routes will have counters allocated. This **<G,
S>** configuration is applicable when
the hardware runs out of resources. Specific
**<G, S>** creation has
priority to preempt counters from wildcard
creation.


The **byte****|****frame**
optional keyword enables the counter to be in either byte mode or frame
mode. This mode applies to all counters. When the counter mode changes, all
counter values will be reset to zero.


Either **<G, S>**, or
**byte****|****frame**
optional keywords are used but cannot be used together. All counters are
**byte****|****frame**.
The **byte****|****frame**
mode is global and not applicable on a **<G,
S>** basis.
- Execute clear
command:


```
`**clear ip multicast count <G> <S>**`
```
- Execute show
command:


```
`**show multicast fib ipv4 <G> count**`
```


This command currently exists but does not
show anything.


This show command is intended to display
the following (example):


```
`switch> **show multicast fib ipv4 count**
Activity poll time: 60 seconds
225.1.1.1 100.0.0.2
Byte: 123
Vlan100 (iif)
Vlan200
Activity 0:00:47 ago`
```


Total counts are the sum of counts from all sources in that group.


The count value can be **N/A** if a mroute does not have an associated
counter.


If the count value for any source in a **G** is **N/A**, then the total counts for **G** will be shown as **N/A**. However, the count values for other sources are still shown.


## Route Management


When enabling routing, the switch discovers the best route to a packet destination address by
exchanging routing information with other devices. EOS disables IP routing by
default.


The following sections describes routing features that EOS supports:

- Route Redistribution

- Equal Cost Multipath Routing (ECMP) and Load Sharing

- Unicast Reverse Path Forwarding (uRPF)

- Routing Tables / Virtual Routing and Forwarding (VRF)

- RIB Route Control


### Route Redistribution


Route redistribution advertises connected (static) routes or routes
established by other routing protocols into a dynamic routing
protocol routing domain. By default, the switch advertises only
routes in a routing domain established by the protocol that
defined the domain.


Route redistribution commands specify the scope of the redistribution
action. By default, all routes from a specified protocol, or all
static routes, advertise into the routing domain. Commands can
filter routes by applying a route map and defining the subset of
routes to advertise.


### Equal Cost Multipath Routing
(ECMP) and Load Sharing


Equal Cost Multi-Path (ECMP) provides a routing strategy to forward traffic over multiple paths
with equal routing metric values.


#### Configuring ECMP (IPv4)


EOS assigns all ECMP paths with the same tag value, and commands that
change the tag value of a path also change the tag value of all
paths in the ECMP route.


In a network topology using ECMP routing, hash polarization may result
when all switches perform identical hash calculations. Hash
polarization leads to uneven load distribution among the data paths.
Switches select different hash seeds to perform hash calculations
and avoid hash polarization.


The ip load-sharing command provides the hash seed with an algorithm for
distributing data streams among multiple equal-cost routes to a
specified subnet.


**Example**


This command sets the IPv4 load sharing hash seed to
**20**:
```
`switch(config)# **ip load-sharing fm6000 20**
switch(config)#`
```


#### Multicast Traffic Over ECMP


The switch attempts to spread outbound unicast and multicast traffic to all ECMP route paths
equally. To disable the sending of multicast traffic over ECMP, use
the [multipath none](/um-eos/eos-multicast-architecture#xx1151679)
command or the no version of the [multipath deterministic](/um-eos/eos-multicast-architecture#xx1216054) command.


#### Resilient ECMP


Resilient ECMP uses prefixes where routes are not desired for rehashing due to link flap,
typically where ECMP participates in load balancing. Resilient ECMP
configures a fixed number of next-hop entries in the hardware ECMP
table for all the routes within a specified IP address prefix.
Implementing fixed table entries for a specified next-hop address
allows the data flow hash to a valid next-hop number to remain
intact even when some next-hops go down or come back online.


Enable resilient ECMP for all routes within a specified prefix using the ip hardware fib ecmp resilience


command. The command specifies the maximum number of next-hop addresses
that the hardware ECMP table contains for the specified IP prefix
and configures a redundancy factor that facilitates the duplication
of next-hop addresses in the table. The fixed table space for the
address uses the maximum number of next hops multiplied by the
redundancy factor. When the table contains the maximum number of
next-hop addresses, the redundancy factor specifies the number of
times to list each address. When the table contains fewer than the
maximum number of next-hop addresses, the table space entries fill
with additional duplication of the next-hop addresses.


EOS supports resilient ECMP for IPv6 IP addresses.


**Example**


This command configures a hardware ECMP table space of 24 entries for the
IP address **10.14.2.2/24**. A maximum of six
next-hop addresses can be specified for the IP address. When the
table contains six next-hop addresses, each appears in the table
four times. When the table contains fewer than six next-hop
addresses, each address duplicates until filling all of the 24 table
entries.
```
`switch(config)# **ip hardware fib ecmp resilience 10.14.2.2/24 capacity 6 redundancy 4**
switch(config)#`
```


#### Unequal Cost Multipath (UCMP) for Static Routes


Unequal Cost Multipath (UCMP) for Static Routes provides a mechanism to forward traffic from a device on an ECMP route with the ratio of the
weights used for next-hops and program them into the Forwarding Information Database (FIB).


**Configuring UCMP for Static Routes**


Use the following commands to configure UCMP on the VRF, ***myVRF***,
with an FEC maximum size of 100:


```
`switch(config)# **router general**
switch(config-router-general)# **vrf myVRF**
switch(config-router-general-vrf-myVRF)# **route static ucmp forwarding fec maximum-size 100**`
```


#### Aggregate Group Monitoring (AGM) for ECMP


This feature allows the monitoring of packets and bytes traversing the members of the
configured ECMP groups on the switch with a high time resolution. Once enabled, AGM
collects data for the specified duration, writes it to the specified file on the switch
storage, and then stops.


**Supported Platforms**


- DCS-7260CX3

- DCS-7060X5

- DCS-7388

- DCS-7060X6


#### Configuring AGM for ECMP Groups


Note: You must have at least one ECMP Group configured on the switch.


To begin collecting data on the switch at 100 millisecond intervals for
1800 seconds, use the following command:


```
`switch(config)# **start snapshot counters ecmp poll interval 100 milliseconds duration 1800 seconds**`
```


Specify an optional URL to store the data. If not specified, the files
store in the non-persistent storage at
**/var/tmp/ecmpMonitor**.


If providing a URL, it must point to a valid file system. EOS allows the
following file systems:


- **file** - The path must start with
**/tmp** or
**/tmp**. The files store in
the non-persistent storage.

- **flash** - Files store in persistent
storage.


Use the following command to interrupt the snapshot before the end of the
configured duration:


```
`switch# **stop snapshot counters ecmp**`
```


To delete previous snapshots, use the following command:


```
`switch# **clear snapshot counters ecmp id_range**`
```


If you do not specify a range of IDs, then all previous snapshots delete
from the system.


#### Displaying AGM for ECMP Information


Use the **show snapshot counters ecmp history** to display information about the configuration.


```
`switch# **show snapshot counters ecmp history**
                                Request ID: 17
                                Output directory URL: file:/var/tmp/ecmpMonitor
                                Output file name(s): ecmpMonitor-17-adj1284.ctr, ecmpMonitor-17-adj1268.ctr
                                Complete: True
                                Poll interval: 1000 microseconds
                                Total poll count: 59216
                                Start time: 2024-06-17 17:58:36
                                Stop time: 2024-06-17 17:59:36

                                L2 Adjacency ID    Interfaces
                                --------------------- ----------------------------------------------------
                                1268                  Ethernet54/1, Ethernet41/1, Ethernet1/1, Ethernet57/1
                                1284                  Ethernet20/1, Ethernet35/1, Ethernet41/1, Ethernet8/1, Ethernet1/1`
```


The output displays the list of previous snapshots including any current ones as well as the following information:


- **Request ID** - Identifies the snapshot Request ID to use for the **clear**
command.

- **Output directory URL** - Identifies the snapshot storage location.

- **Complete** - Identifies the snapshot completion status.

- **Poll Interval** - Identifies the configured polling interval for the snapshot.

- **Total poll count** - Identifies the total number of hardware counters collected.d

- **Start time** and **Stopped time** - Identifies the system time when the snapshot
started and stopped.

- **L2 Adjacency ID** and
**Interfaces** - The summary
of the ECMP groups monitored by AGM.


#### Configuring IP-over-IP Hierarchical FEC


When the next hop of an IP route, the dependent route, resolves over another IP
route, the resolving route, the adjacency information of the FEC for
the resolving route duplicates into the dependent route FEC.
Configuring IP over IP Hierarchical FEC prevents duplication of the
adjacency information, and instead, the dependent route FEC points
to the resolving route FEC to form a hierarchical FEC for the
dependent route. This helps avoid unnecessary allocation of scarce
ECMP FECs in the case where the dependent route does not use ECMP,
but the resolving route does use ECMP.


Use the following commands to enable IP-over-IP HFEC:


```
`switch(config)# **router general**
switch(config-router-general)# **rib fib fec hierarchical resolution**`
```


#### Resilient Equal-Cost Multi-Path(RECMP) Deduping


Routes covered by a Resilient Equal-Cost Multi-Path (RECMP) prefix consists of routes
that use hardware tables dedicated for Equal-Cost Multi-Path (ECMP) routing. Resilient ECMP
(RECMP) deduping reduces the number of ECMP hardware table entries allocated by the switch to
force the routes with the same set of next hops but point to different hardware table entries
and point to the same hardware table entry when encountering high hardware resource utilization.
Forcing RECMP routes to change the hardware table entry that they point to may potentially cause
a traffic flow disruption for any existing flows going over that route. The deduping process
attempts to minimize the amount of potential traffic loss.
Each route needs to allocate
hardware table entries in the ASIC that contain forwarding information for the route, such as
the next-hops and egress links used by each next-hop uses. The network device uses these
hardware table entries when making forwarding decisions for a packet meant for a certain
route. These ECMP hardware tables have limited size and can fill up quickly if allocating a
large number of these hardware table entries. One option to ease the usage of these hardware
tables can force RECMP routes to share hardware table entries.


RECMP routes can point to
the same hardware table entry if they share the same set of next hops and the order of the
next-hops. However, RECMP routes may end up sharing the same set of next-hops, but the
next-hop ordering may be different between them, and the routes end up occupying different
hardware table entries in the ASIC. RECMP routing has a property where the current ordering of
next-hops for a given route can be influenced by the previous order. The ordering between the
routes can differ because these routes had a different set of next hops at some previous time
before they finally converged onto the same set of next-hops.


When the ECMP hardware
resource usage crosses the high threshold, the deduping process begins, and it lasts until the
ECMP hardware resource usage falls below the low threshold. Use the **ip hardware
fib next-hop resource optimization thresholds** command to modify the
thresholds.


##### Configuring Resilient ECMP Deduping


EOS disabled Resilient ECMP Deduping by default.

- Use the following command to disable all the hardware resource optimization
 features:
```
`switch(config)# **ip hardware fib next-hop resource optimization disabled**`
```

- Use the following command to re-enable the all hardware resource optimization
 features after disabling
 them:
```
`switch(config)# **no ip hardware fib next-hop resource optimization disabled**`
```

- Use the following command to configure the thresholds for starting and stopping the optimization:
```
`switch(config)# **ip hardware fib next-hop resource optimization thresholds low <20> high <80>**`
```




 Note:


 - The value specified for the threshold represents the percentage of resource
utilization, and uses an integer between **0** and
**100**.

 - Setting the high threshold to **80** indicates that
optimization starts when the resource utilization is above
**80%**. The default value of this threshold is
**90**.

 - Setting the low threshold to **20** indicates that
optimization stops when the resource utilization is below
**20%**. The default value of this threshold is
**85**.







##### Show Commands


- The **show ip hardware fib summary** command displays the statistics
of this RECMP
deduping:
**Example**


```
`switch# **show ip hardware fib summary**
Fib summary
-----------
Adjacency sharing: disabled
BFD peer event: enabled
Deletion Delay: 0
Protect default route: disabled
PBR: supported
URPF: supported
ICMP unreachable: enabled
Max Ale ECMP: 600
UCMP weight deviation: 0.0
Maximum number of routes: 0
Fib compression: disabled
**Resource optimization for adjacency programming: enabled
Adjacency resource optimization thresholds: low 20, high 80**`
```

The last two
lines of the output shows if RECMP deduping is enabled, and the corresponding threshold
values for starting and stopping the optimization process.

- The **show hardware capacity** command displays the utilization of
the hardware resources. The example below shows the multi-level hierarchy ECMP
resources:
```
`switch# **show hardware capacity**
Forwarding Resources Usage

Table    Feature         Chip    Used     Used    Free	Committed    Best Case    High
                                 Entries  (%)     Entries    Entries      Max          Watermark
                                                                                       Entries
------- --------------- ------- -------- ------- --------   ------------ ------------ ---------
ECMP                            0        0%     4095        0     	 4095         0
ECMP     Mpls                   0        0%     4095        0     	 4095         0
ECMP     Routing                0        0%     4095        0     	 4095         0
ECMP     VXLANOverlay           0        0%     4095        0     	 4095         0
ECMP     VXLANTunnel            0        0%     3891        0     	 3891         0`
```


##### Limitations


- With RECMP deduping, optimization of a sub-optimal ECMP route requires releasing and
reallocating hardware resources for the route. Therefore the process may increase overall
convergence time for route programming. It may not be desirable to always start the
optimization when the sufficent hardware resource existt. The threshold value for starting
the optimization should be adjusted based on the route scale of the network.

- The deduping of ECMP hardware resources may cause potential traffic flow disruption for
traffic flows going over RECMP routes with changing hardware table entries. While the
deduping process tries to minimize the amount of traffic flow disruption, it is still
sometimes inevitable.

- RECMP hardware table entries can only be deduped to other RECMP hardware table entries
that share the same set of nexthops. This puts a limit to the amount of RECMP hardware table
entries that can be reduced to the number of RECMP hardware table entries with unique
nexthop sets.


### Cluster Load Balancing


Cluster load balancing distributes incoming network traffic across a cluster of servers
to improve performance, increase reliability, and ensure high availability. By
preventing any single server from becoming overwhelmed by network traffic, cluster load
balancing optimizes resource utilization and minimizes response times.


The core networking capability of cluster load balancing uses a load balancer acting as a
limiting factor for a group of servers acting asa cluster. When a client request
arrives, the load balancer intercepts it and by using various algorithms, decides which
server in the cluster can best provide handling of the request. The decision can be
based on server health, current load, or a simple round-robin rotation. The selected
server then processes the request and sends the response back to the client.


The `**load-balance**` command specifies the hashing algorithm and
fields to use for Equal-Cost Multi-Path (ECMP) load balancing on a router. ECMP allows a
router to use multiple next-hop addresses for the same destination, distributing traffic
across these paths. The configuration determines which parts of the packet header, such
as source IP or destination IP, to use for hash value creation. This ensures that a
single flow, a stream of packets with the same header information, consistently uses the
same path, preventing packet reordering and improving performance for applications such
as TCP.s


Arista Cluster Load Balancing (CLB) optimizes traffic flows in data center clusters,
particularly for AI/ML workloads, using RoCE (Remote Direct Memory Access (RDMA) over
Converged Ethernet), and intelligently places flows in both directions to ensure
balanced traffic across all paths in a spine-leaf topology. By monitoring RoCE traffic
and making real-time adjustments to ensure consistent and high throughput communication
between Graphics Processing Units (GPU) servers, CLB eliminates bottlenecks and improves
overall network utilization.


#### Configuring Cluster Load Balancing


Access CLB commands in the Global Configuration mode and configure the fields used for
the hashing algorithm.


Use the following command to enter the CLB configuration
mode:
```
`switch(config)# **load-balance cluster**
switch(config-clb)#`
```


CLB supports VXLAN bridging and routed as the forwarding mode and encapsulation to deliver packets between Top of
Rack (TOR) switches over the uplinks.


Use the following command to configure VXLAN bridging as the forwarding mode:


```
`switch(config-clb)# **forwarding type bridged encapsulation vxlan**`
```


Use the following commands to configured the forwarding mode as routed:


```
`switch(config-clb)# **forwarding type routed**`
```


If configuring the CLB forwarding type as routed, you must add the prefix length to match
the length used for the network on each TOR with GPU addresses, and by default, supports
only one length. For example, if the GPUs on a TOR use IPv4 addresses from
`10.0.0.1` to `10.0.0.255`, then configure the prefix
length as `24`.


```
`switch(config-clb)# **destination grouping prefix length 24**`
```


Use the `**flow source**` parameter to add the method for learning
flows. By default, EOS only supports
`learning`:
```
`switch(config-clb)# **flow source learning**`
```


To load-balance traffic on the TORs, use the round-robin method. EOS does not support any other method of load-balancing traffic.


```
`switch(config-clb)# **load-balance method flow round-robin**`
```


By default, flow aging timeout has a value of 600 seconds with a minimum of 30 seconds. Setting the interval between bursts
of training job network communication below 30 seconds negatively impacts performance as flows can be incorrectly
aged out of the hardware. Use the following command to configure the interval to 60 seconds:


```
`switch(config-clb)# **flow source learning**
switch(config-clb-flow-learning)# **aging timeout 60 seconds**`
```


CLB requires identification of the ports connected to the same GPU server. Use the **port groups**
 to configure the ports and flows from the interfaces load-balance with each other. EOS does not limit the number of groups,
however, Arista Networks recommends using only one group per GPU server.


Use the following commands to add ***server1*** and interfaces,
***Et15/1,16/1,17/1,18/1***, to the port group:


```
`switch(config-clb)# **port group host server1**
switch(config-clb-portgroup-server1)# **member Et15/1,16/1,17/1,18/1**`
```


To limit the number of flows programmed for a port group and preserve hardware TCAM resources, use the following command to limit
the number of flows to 800:


```
`switch(config-clb-portGroup-server1)# **flow limit 800**`
```


Configure CLB flow match type as VXLAN bridging IPv4 traffic, and configure a VXLAN interface for the flow.


```
`switch(config)# **interface vxlan1**
switch(config)# **flow match encapsulation vxlan ipv4**`
```


You can also configure the default flow match type as a non-VXLAN IPv4 packet:


```
`switch(config)# **flow match encapsulation none ipv4**`
```


##### Displaying Cluster Load Balancing Information


Use the **show load-balance cluster status** to display the current status of CLB:


```
`switch# **show load-balance cluster status**
CLB Status: enabled
Port Group Name       Fallback DSCP    Fallback Traffic Class
--------------------- ------------------- ----------------------
group0                           46                         -
group1                            -                         3`
```


Use the **show load-balance cluster flows** to display all programmed flows:


```
`switch# **show load-balance cluster flows**
VRF       SA       DA          Queue Pair    Rx Intf       Flow Assignment
--------- -------- -------- ---------------- ------------- ---------------
default  10.98.0.1  10.99.0.1           1000    Et15/1        Et1/1 10.0.0.2
default  10.98.0.2  10.99.0.2           1001    Et16/1        Et2/1 10.1.0.2
default  10.98.0.3  10.99.0.3           1002    Et17/1        Et5/1 10.2.0.2
default  10.98.0.4  10.99.0.4           1003    Et18/1        Et6/1 10.3.0.2

Total flows: 4, displayed: 4`
```


#### Cluster Load Balancing for a Spine


Cluster Load Balancing on a Spine router ensures optimal load balancing flows used as
part ofGPU-based cluster communication in a network with multiple links connecting a
TOR router to a Spine router.


When enabled on a Spine, the router monitors RoCE traffic from a TOR and applies optimal
load balancing when forwarding traffic to the next TOR router host the destination GPU
server.


##### Configuring Cluster Load Balancing for a Spine


Note: Only the multi-agent routing model supports CLB.
Note: Perform the following commands only on a Spine router.
Use the following command to enter the CLB Configuration
Mode:
```
`switch(config)# **load-balance cluster**
switch(config-clb)#`
```


Configure the forwarding mode and encapsulation to forward packets on the Spine switch. EOS only supports
**`routed`** for IPv4:



```
`switch(config-clb)# forwarding type routed`
```


Enter the following command to configure flow learning for the Spine switch:


```
`switch(config)# **flow source learning**`
```


The **load-balance method** command configures load balancing flows and must be
entered on the Spine switch:


```
`switch(config-clb)# **load-balance method flow spine port-index**`
```


Configure the number of ports connecting the Spine to the Leaf switch. Every TOR connected to the Spine
must have the same number of ports connecting to the Spine.


```
`switch(config-clb)# **spine port group size 2**`
```


CLB requires configuring the identification of the port group that connect the Spine switch to a TOR. The following output
provides an example configuration of two port groups on TOR1 and TOR2, each with 2 ports:


```
`port group spine TOR1
    member 10 Ethernet12/1
    member 20 Ethernet1/1
...
port group spine TOR2
    member 10 Ethernet5/1
    member 20 Ethernet13/1`
```


The ports within a group display in order of increasing priority by the number assigned to each port. Ethernet1/1 and
Ethernet13/1 have the second position in the configuration.


To limit the number of flows programmed for a port group and preserve hardware TCAM resources, use the following command to limit
the number of flows to 800:


```
`switch(config-clb-portGroup-server1)# **flow limit 800**`
```


Configure CLB flow match type as VXLAN bridging IPv4 traffic, and configure a VXLAN interface for the flow.


```
`switch(config)# **interface vxlan1**
switch(config)# **flow match encapsulation vxlan ipv4**`
```


You can also configure the default flow match type as a non-VXLAN IPv4 packet:


```
`switch(config)# **flow match encapsulation none ipv4**`
```


### Unicast Reverse Path Forwarding
(uRPF)


Unicast Reverse Path Forwarding (uRPF) verifies the accessibility of source IP addresses
in forwarded packets from a switch. When uRPF determines that the routing table does not
contain an entry with a valid path to the packet source IP address, the switch drops the
packet.


IPv4 and IPv6 uRPF operate independently. Configure uRPF on a VRF. Commands that do not
specify a VRF utilize the default instance. uRPF does not affect multicast routing.


uRPF defines two operational modes:


- **Strict mode** - In strict mode, uRPF also verifies that a received packet on
the interface with the routing table entry uses that entry for the return
packet.

- **Loose mode** - uRPF validation does not verify the inbound packet ingress
interface.


#### uRPF Operation


Configure uRPF on interfaces. For packets arriving on a uRPF-enabled interface, the source IP
address examines the source and destination addresses of unicast routing table entries and
verifies it.


uRPF requires a reconfigured routing table to support IP address verification. When enabling uRPF
for the first time, unicast routing becomes briefly disabled to facilitate the routing table
reconfiguration. The initial enabling of uRPF does not affect multicast routing.


A packet fails uRPF verification if the table does not contain an entry whose source or
destination address that matches the packet’s source IP address. In strict mode, the uRPF also
fails when the matching entry’s outbound interface does not match the packet’s ingress
interface.


uRPF does not verify the following packets:

- DHCP with a source that uses **0.0.0.0** and a destination uses
**255.255.255.255**.

- IPv6 link local in the following format -**FE80::/10**.

- Multicast packets


##### ECMP uRPF


When verifying ECMP routes, strict mode checks all possible paths to determine the correct
interface receives the packet. ECMP groups with a maximum of eight routing table entries
support strict mode. The switch reverts to loose mode for ECMP groups that exceed eight
entries.


##### Default Routes


uRPF strict mode provides an **allow-default** option that accepts default
routes. On interfaces that enable allow-default and define a default route, uRPF strict mode
validates a packet even when the routing table does not contain an entry that matches the
packet’s source IP address. If not enabling allow-default, uRPF does not consider the
default route when verifying an inbound packet.


##### Null Routes


**NULL0** routes drop traffic destined to a specified prefix. When
enabling uRPF, traffic originating from null route prefixes drops in strict and loose modes.


#### uRPF Configuration


Enable Unicast Reverse Path Forwarding (uRPF) for IPv4 packets ingressing the configuration mode
interface using the ip verify command.


Note: uRPF cannot be enabled on interfaces with ECMP member FECs.

**Examples**

- This command enables uRPF loose mode on **interface vlan
17**.
```
`switch(config)# **interface vlan 17**
switch(config-if-Vl17)# **ip verify unicast source reachable-via any**
switch(config-if-Vl17)# **show active**
 interface Vlan17
   ip verify unicast source reachable-via any
switch(config-if-Vl17)#`
```

- This command enables uRPF strict mode on **interface vlan
18**.
```
`switch(config)# **interface vlan 18**
switch(config-if-Vl18)# **ip verify unicast source reachable-via rx**
switch(config-if-Vl18)# **show active**
 interface Vlan18
   ip verify unicast source reachable-via rx
switch(config-if-Vl18)#`
```


### Routing Tables / Virtual Routing
and Forwarding (VRF)


An IP routing table is a data table that lists the routes to network destinations and metrics (distances) associated with those routes. A routing table is also known as a Routing Information Base (RIB).


Virtual Routing and Forwarding (VRF) allows traffic separation by maintaining multiple routing
tables. Arista switches support multiple VRF instances:


- A default global VRF

- Multiple user-defined VRFs


The number of user-defined VRFs supported
varies by platform. VRFs can be used as management or data plane VRFs.

- Management VRFs have routing disabled and typically used for
management-related traffic.

- Dataplane VRFs have routing enabled and support routing protocols and packet
forwarding, including both hardware and software.


Trident, FM6000, and Arad platform switches support dataplane VRFs.


VRFs support unicast IPv4 and IPv6 traffic
and multicast traffic. Loopback, SVI, and routed ports may be added to
VRFs. Management ports may be added without any hardware forwarding.


To allow overlap in the sets of IP addresses used by different VRF instances, a Route
Distinguisher (RD) may be prepended to each address. RFC4364 defines RDs.


#### Default VRF


EOS creates the default VRF automatically and you cannot renamed or configure
it. Some configuration options accept ***default*** as a VRF input.


#### User-Defined VRFs


Create a user-defined VRF with the vrf instance command. After creating it,
a VRF may be assigned a Route Distinguisher (RD) with the rd (VRF configuration mode) command in
the VRF submode of Router-BGP Configuration Mode.


**Examples**

- These commands create a VRF named
**purple**, place the switch
in BGP VRF configuration mode for that VRF, and
specify a route distinguisher for the VRF,
identifying the administrator as **AS
530**, and assigning
**12** as its local
number.
```
`switch(config)# **vrf instance purple**
switch(config-vrf-purple)# **router bgp 50**
switch(config-router-bgp)# **vrf purple**
switch(config-router-bgp-vrf-purple)# **rd 530:12**
switch(config-router-bgp-vrf-purple)#`
```

- To add interfaces to a user-defined VRF, enter
configuration mode for the interface and use the
vrf (Interface mode)
command. Loopback, SVI, and routed ports can be
added to a VRF.These commands add
**vlan 20** to the VRF named
**purple**.
```
`switch(config)# **interface vlan 20**
switch(config-if-Vl20)# **vrf purple**
switch(config-if-Vl20)#`
```

- The show vrf command shows
information about user-defined VRFs on the
switch.This command displays information for
the VRF named
**purple**.
```
`switch# **show vrf purple**
Vrf     RD         Protocols  State       Interfaces
------- ---------- ---------- ----------- ------------
purple  64496:237  ipv4       no routing  Vlan42, Vlan43

switch>`
```


##### rd (VRF configuration
mode)


The **rd** command issued in VRF Configuration Mode is a legacy command
supported for backward compatibility. To configure a Route Distinguisher
(RD) for a VRF, use the rd (VRF configuration mode)
command.


Note: Legacy RDs that were assigned to a VRF in VRF Configuration Mode still appear in
**show vrf** outputs if an RD has not
been configured in Router-BGP VRF Configuration Mode, but they no longer
have an effect on the system.


#### Context-Active VRF


The context-active VRF specifies the default VRF commands to use when displaying or refreshing
routing table data.


VRF-context aware commands include:

- clear arp-cache

- show ip

- show ip arp

- show ip route

- show ip route gateway

- show ip route host


The cli vrf command specifies the context-active VRF.


**Example**


This command specifies **magenta** as the context-active
VRF.
```
`switch# **cli vrf magenta**
switch# **show routing-context vrf**
Current VRF routing-context is magenta`
```


The show routing-context vrf command displays the context-active VRF.


**Example**


This command displays the context-active
VRF.
```
`switch# **show routing-context vrf**
Current VRF routing-context is magenta
switch#`
```


### RIB Route Control


The Routing Information Base (RIB) consists of the routing information learned by the routing
protocols, including static routes. The Forwarding Information Base (FIB) consists of
the routes actually used to forward traffic through a router.


Forwarding Information Base (FIB) performs IP destination prefix-based switching decisions.
Similar to a routing table, the FIB maintains the forwarding information for the winning
routes from the RIB. When routing or topology changes occur in the network, the IP
routing table information updates, and reflects the changes in the FIB.


#### Configuring FIB policy


The RIB calculates the best or winning routes to each destination and place these routes in the
forwarding table. Then advertises the best routes based on the configured
FIB policy.


For example, a FIB policy can be configured to deny the routes for FIB programming, however, it
does not prevent these routes fromadvertising a routing protocol, or
redistributed into another routing domain, or used for recursive resolution
in the IP RIB. FIB policies control the size and content of the routing
tables, and the best route to take to reach a destination.


Use the **rib ipv4 | ipv6 fib policy** command to enable an FIB policy for
a specific VRF in the Router General Configuration Mode.


EOS supports the following match statements:

- **match interface**

- **match** **[ ip |
ipv6 ] address** **prefix-list**

- **match** **[ ip |
ipv6 ]
resolved-next-hop**
**prefix-list**

- **match isis level**

- **match metric**

- **match source-protocol**


**Example**


The following example enables FIB policy for IPv4 in the default VRF, using the
route map,
**map1**.
```
`switch(config)# **router general**
switch(config-router-general)# **vrf default**
switch(config-router-general-vrf-default)# **rib ipv4 fib policy map1**`
```


##### Configuring FIB Route Limits


The FIB route count for a VRF table includes FIB routes from most protocol
sources, such as BGP, IGP, static routes, and address families.
After the FIB routes reach a configured limit on the VRF, EOS
suppresses new BGP route additions in the FIB to avoid exceeding the
limit. Other types of routes continue to add to the FIB table after
the configured limit has been exceeded.


EOS maintains suppressed routes for each VRF and address family in a suppressed routes list. If the FIB table reduces routes below
the configured limit, then routes on the suppressed routes list install into the table. If a BGP route becomes suppressed due to the table
limit, the BGP route does not advertise to peers.


The FIB route limit does not affect routes already installed in the FIB. When configuring a lower limit on the FIB table, existing BGP
routes remain in the table. Only new BGP routes become suppressed based on the new limit configuration.


| Protocol
| Apply to the FIB Route Count
| FIB Route Suppression Supported
|


| BGP
| Yes
| Yes
|


| IGP
| Yes
| No
|


| Static
| Yes
| No
|


| Other
| Yes
| No
|


| ARP
| No
| No
|


Use the following command to configure a global route limit for IPv4 to 100 and warn when the table has consumed 80%
of the limit:


```
`switch(config)# **router general**
switch(config-router-general)# **fib route limit**
switch(config-router-general-fib-route-limit)# **ipv4 limit 100 warning-limit 80 percent**`
```


All VRFs inherit the global configuration unless explicitly configured with a limit.


Use the following command to limit the number of routes to 100 on VRF
purple and warn when the table has
consumed 80% of the limit:


```
`switch(config)# **router general**
switch(config-router-general)# **vrf purple**
switch(config-router-general-vrf-purple)# **fib ipv4 route limit 100 warning-limit 80 percent**`
```


To disable the feature, use the following command:


```
`switch(config-router-general-vrf-purple)# **fib ipv4 route limit disabled**`
```


Configure globally suppressing BGP routes in case of a route limit overflow using the following commands:


```
`switch(config)# **router general**
switch(config-router-general)# **fib route limit**
switch(config-router-general-fib-route-limit)# **action protocol bgp route overflow suppress**`
```


Use the **show fib [ipv4 | ipv6] route limit [vrf vrf_name] suppressed**
command to display information about suppressed routes in the FIB table:


```
`switch# **show fib ipv4 route limit suppressed**
VRF: default
  Address-Family IPv4:
     12 routes suppressed
        201.1.0.0/24 (bgp)
        201.1.4.0/24 (bgp)
        201.1.5.0/24 (bgp)
        201.1.6.0/24 (bgp)
        201.1.7.0/24 (bgp)
        201.1.8.0/24 (bgp)
        201.1.9.0/24 (bgp)
        201.1.10.0/24 (bgp)
        201.1.11.0/24 (bgp)
        201.1.12.0/24 (bgp)
        201.1.13.0/24 (bgp)
        201.1.14.0/24 (bgp)`
```


#### Displaying FIB Information


Use the **show rib route <ipv4|ipv6> fib policy exclude** command to
 display the RIB information. The **fib policy excluded** option
 displays the RIB routes excluded from programming into the FIB by the FIB policy.


**Example**


The following example displays the routes filtered by FIB policy using the **fib
 policy excluded** option of the **show rib route
 ip|ipv6**
 command.
```
`switch# **show rib route ipv6 fib policy excluded**
switch# **show rib route ip bgp fib policy excluded**

VRF name: default, VRF ID: 0xfe, Protocol: bgp
Codes: C - Connected, S - Static, P - Route Input
       B - BGP, O - Ospf, O3 - Ospf3, I - Isis
       > - Best Route, * - Unresolved Nexthop
       L - Part of a recursive route resolution loop
>B    10.1.0.0/24 [200/0]
         via 10.2.2.1 [115/20] type tunnel
            via 10.3.5.1, Ethernet1
         via 10.2.0.1 [115/20] type tunnel
            via 10.3.4.1, Ethernet2
            via 10.3.6.1, Ethernet3
>B    10.1.0.0/24 [200/0]
         via 10.2.2.1 [115/20] type tunnel
            via 10.3.5.1, Ethernet1
         via 10.2.0.1 [115/20] type tunnel
            via 10.3.4.1, Ethernet2
            via 10.3.6.1, Ethernet3`
```


#### Displaying RIB Route Information


Use the show rib route ip command to view the IPv4 RIB information.


**Example**


This command displays IPv4 RIB static
 routes.
```
`switch# **show rib route ip static**

VRF name: default, VRF ID: 0xfe, Protocol: static
Codes: C - Connected, S - Static, P - Route Input
       B - BGP, O - Ospf, O3 - Ospf3, I - Isis
       > - Best Route, * - Unresolved Nexthop
       L - Part of a recursive route resolution loop
>S    10.80.0.0/12 [1/0]
         via 172.30.149.129 [0/1]
            via Management1, directly connected
>S    172.16.0.0/12 [1/0]
         via 172.30.149.129 [0/1]
            via Management1, directly connected

switch#`
```


## IPv4 Route Scale


Optimize IPv4 routes to achieve route scale when route distribution has many routes with one or
two parameters, and each parameter consisting of prefix lengths
**12**, **16**,
**20**, **24**,
**28**, and
**32**. If configuring two separate prefix
lengths, in any order, one must have the prefix length of
**32**.


Note: IPv4 Route Scale cannot be used with AlgoMatch.
The following sections describe IPv4 route scale configuration, show commands, and system log
messages:

- Configuring IPv4 Route Scale

- IPv4 Routescale with 2-to-1 Compression

- Show
Commands


### Configuring IPv4 Route Scale


Enable IPv4 route scale using the ip hardware fib optimize command in
the Global Configuration Mode. The platform Layer 3 agentrestarts to
ensure IPv4 routes optimization with the agent SandL3Unicast terminate command in the Global
Configuration Mode.


**Example**


This configuration command allows configuring prefix lengths
**12** and
**32**.
```
`switch(config)# **ip hardware fib optimize exact-match prefix-length 12 32**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


One of the two prefixes uses a prefix-length of
**32** required in the instance when
using two prefixes. For this command to take effect, you must
restart the platform Layer 3 agent.


**Example**


This configuration command restarts the platform Layer 3 agent to ensure
IPv4 route
optimization.
```
`switch(config)# **agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


Restarting the platform Layer 3 agent results in deletion of all IPv4 routes and then
re-adds them to the hardware.


**Example**


This configuration command allows configuring prefix lengths
**32** and
**16**.
```
`switch(config)# **ip hardware fib optimize exact-match prefix-length 32 16**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


One of the two prefixes uses a prefix-length of
**32** required in the instance when
using two prefixes. For this command to take effect, you must
restart the platform Layer 3 agent.


**Examples**

- This configuration command restarts the platform Layer 3
agent to ensure IPv4 route
optimization.
```
`switch(config)# **agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


Restarting
the platform Layer 3 agent results in deletion of
all IPv4 routes and then re-adds them to the
hardware.

- This configuration command allows configuring prefix
length
**24**.
```
`switch(config)# **ip hardware fib optimize exact-match prefix-length 24**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


In this instance, when configuring a single prefix-length, the
configuration does not require a prefix-length of
**32**. For this command to
take effect, you must restart the platform Layer 3 agent.


**Examples**

- This configuration command restarts the platform Layer 3
agent to ensure IPv4 route
optimization.
```
`switch(config)#**agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


Restarting
the platform Layer 3 agent results in deletion of
all IPv4 routes and then re-adds them to the
hardware.

- This configuration command allows configuring the
prefix length
**32**.
```
`switch(config)# **ip hardware fib optimize exact-match prefix-length 32**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


For this command to take effect, you must restart
the platform Layer 3 agent.

- This configuration command restarts the platform Layer 3
agent to ensure IPv4 route
optimization.
```
`switch(config)# **agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```

Restarting
the platform Layer 3 agent results in deletion of
all IPv4 routes and then re-adds them to the
hardware.

- This configuration command disables the prefix lengths
**12** and
**32**
configuration.
```
`switch(config)#**no ip hardware fib optimize exact-match prefix-length 12 32**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are not optimized`
```


One of the two prefixes uses a prefix-length of
**32** required in the instance when
using two prefixes. For this command to take effect, you must
restart the platform Layer 3 agent.


**Examples**

- This configuration command restarts the platform Layer 3
agent to ensure no IPv4 route
optimization.
```
`switch(config)#**agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


Restarting
the platform Layer 3 agent results in deletion of
all IPv4 routes and then re-adds them to the
hardware.

- This configuration command attempts to configure the
prefix lengths **20** and
**28** which triggers an
error exception. One of the two prefixes in this
command must be a prefix-length of
**32** required when adding
two
prefixes.
```
`switch(config)#**ip hardware fib optimize exact-match prefix-length 20 28**
% One of the prefix lengths must be 32`
```


IPv4 routes of certain prefix lengths can be optimized for enhanced route
scale. The following command disables prefix optimization on the
specified VRF(s) to provide more flexibility.


**Examples**

- This configuration command disables prefix optimization
on the default
VRF.
```
`switch(config)# **ip hardware fib optimize disable-vrf default**
! Please restart layer 3 forwarding agent to ensure that the disable-vrf option change takes effect`
```

- This configuration command disables prefix optimization
on VRFs named **vrf1** and
**vrf2**.
```
`switch(config)# **ip hardware fib optimize disable-vrf vrf1 vrf2**
! Please restart layer 3 forwarding agent to ensure that the disable-vrf option change takes effect`
```

- This configuration command restarts the platform Layer 3
agent to ensure that the disable-vrf
configuration takes
effect.
```
`switch(config)# **agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


**Examples**

- This configuration command enables prefix optimization
on the default
VRF.
```
`switch(config)# **ip hardware fib optimize vrf default prefix-length 32**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```

- This configuration command enables prefix optimization
on VRFs named **vrf1** and
**vrf2**.
```
`switch(config)# **ip hardware fib optimize vrf vrf1 vrf2 prefix-length 32**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```

- This configuration command disables optimization on
**vrf1** and
**vrf2** optimization
configured in above
example.
```
`switch(config)# **no ip hardware fib optimize vrf vrf1**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


The **platform trident forwarding-table partition
flexible** command enables ALPM Mode in
Flexible UFT mode using a subset of resources, so ALPM and Exact
Match can coexist.


**Examples**

- This configuration command sets up the flexible
partition.
```
`switch(config)# **platform trident forwarding-table partition flexible ?**
  alpm         Shared UFT bank entries for the ALPM table
  exact-match  Shared UFT bank entries for the exact-match table
  l2-shared    Shared UFT bank entries for the MAC table
  l3-shared    Shared UFT bank entries for the host table`
```

- ALPM gives the route prefix in DEFIM (TCAM table for
longest prefix matched (LPM) lookup) and ALPM
tables.
```
`switch(config)# **platform trident forwarding-table partition flexible alpm ?**
  184320  Upto 180K LPM routes
  368640  Upto 360K LPM routes`
```


Note: The size parameter has following values:

- DCS-7300X3: 180k and 360k are accepted.

- CCS-720XP: 144k and 96k are accepted.

- Other sizes are invalid.


#### Reserving IPv4 and IPv6 Optimized Prefixes


The Large Exact Match (LEM) table stores routes of one or two prefix lengths that belong to a default or non-default VRF. When the LEM table becomes
full, the Longest Prefix Match table stores the routes. This enables reservation of some entries in the LEM table for a specific VRF.


Note: The platform Layer 3 agentrestarts to ensure IPv4 routes optimization with the agent SandL3Unicast terminate command in the Global
Configuration Mode.

Use the following command to create reservations for 25 IPv4 optimized prefixes on VRF blue:


```
`switch(config)# ip hardware fib optimize vrf blue prefixes minimum count 25
! Please restart the SandL3Unicast agent to reserve space for optimized FIB prefixes`
```


Use the following command to create reservations for 35 IPv6 prefixes on VRF green:


```
`switch(config)# ipv6 hardware fib optimize vrf green prefixes minimum count 35
                ! Please restart the SandL3Unicast agent to reserve space for optimized FIB prefixes`
```


Use the following command to restart the Layer 3 agent and allow the changes to take effect:


```
`switch#agent SandL3Unicast terminate
                Sandl3Unicast was terminated`
```


Restarting the agent impacts all forwarding as the command deletes all routes and re-adds them to the switch.


LEM reservations on a VRF persist independently of VRF deletion. Explicitly remove the configuration using the **no** version
of the command.


### IPv4 Routescale with 2-to-1 Compression


The IPv4 routescale with2-to-1 compression optimizes certain prefix lengths and
enhances the route scale capabilities on 7500R, 7280R, 7500R2, and 7280R2 platforms. The
compression is best suited to achieve route scale when route distribution has a large number
of routes of one or two prefix lengths.


#### Configuring IPv4 Routescale 2-to-1 Compression


Use the **compress** command to increase the hardware resources
available for the specified prefix length. This command allows configuring up to one
compressed prefix length, and this command is supported only on 7500R, 7280R, 7500R2,
and 7280R2 platforms.


Note: The **compress** command takes effect only
when you restart the platform Layer3 agent on 7500R, 7280R, 7500R2, and 7280R2
platforms. Use command **agent SandL3Unicast terminate** to
restart the platform Layer3 agent.

**Examples**

- In the following example we are configuring prefix length
**20** and **24**, expanding
prefix length **19** and **23**, and
compressing prefix length
**25**.
```
`switch(config)# **ip hardware fib optimize prefix-length 20 24 expand 19 23 compress 25**
 ! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```

- In the following example we are configuring prefix length
**20** and **23**, expanding
prefix length **19**, compressing prefix length
**24**.
```
`switch(config)# **ip hardware fib optimize prefix-length 20 23 expand 19 compress 24**
 ! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```

- Optionally, you can also use the **internet** profile to configure the IPv4
route scale
compression.
```
`switch(config)# **ip hardware fib optimize prefixes profile internet**
 ! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


Configure a new TCAM profile for the **compress** configuration to work, and disable a few features in the new TCAM profile to make space for the flex-route feature in the hardware. Features like **acl vlan ip** and the **mirror ip** have to be disabled, if you need any of these features or any other features to be enabled with flex-route feature, contact the Arista team.


The **internet** profile works differently based on whether the flex-route feature is enabled in the TCAM profile or not. If the flex-route feature is enabled, the **internet** profile behaves like **ip hardware fib optimize prefix-length 20 23 expand 19 22 compress 24**. If the flex-route feature is disabled, the **internet** profile behaves as **ip hardware fib optimize prefix-length 20 24 expand 19 23**.


**Example**
```
`switch(config)# **hardware tcam**
switch(config-hw-tcam)# **profile flex-route copy default**
switch(config-hw-tcam-profile-flex-route)# **feature flex-route copy system-feature-source-profile**
switch(config-hw-tcam-profile-flex-route-feature-flex-route)# **exit**
switch(config-hw-tcam-profile-flex-route)# **no feature acl vlan ip**
switch(config-hw-tcam-profile-flex-route)# **no feature mirror ip**
switch(config-hw-tcam-profile-flex-route)# **exit**
Saving new profile 'flex-route'
switch(config-hw-tcam)# **system profile flex-route**`
```


#### Limitations


- A maximum of two prefix lengths can be optimized directly at any point of time, of
which only one can be a non-nibble aligned prefix length. Additional prefix lengths
can be optimized using the **expand** or the
**compress** options.

- A maximum of 1-to-4 way expansion and 2-to-1 way compression into any optimized
prefix length is supported. Multiple expansion prefix lengths can be programmed at
any time, however, there can be just one compression prefix length programmed at any
given point in time.

- A maximum of **4096** next-hops can be reliably pointed to by
the compressed prefixes using 2-to-1 way compression.

- The 2-to-1 compression cannot be enabled along with unicast RPF. When both features
are enabled together, unicast RPF functionality may not be correct.

- The flex-route feature in TCAM profiles based only on the default profile, while
disabling the **acl vlan ip** and the **mirror
ip** features. Contact the Arista team if any other feature,
that is not available in the default TCAM profile, is required to be supported along
with the flex-route feature, including support for Mirror to GRE tunnel or ACLs on
SVI.

- VXLAN is not supported with the compress option of this feature.
There is no Syslog or a warning message when VXLAN is configured along with the
2-to-1 way compression feature.


### Show Commands


Display the IPv4 route scale summary using the show platform arad ip route
summary command in the Global Configuration Mode. Resources for all IPv4 route scale
routes are displayed by the show platform
arad ip route command for the Global Configuration Mode.


**Examples**

- This command displays hardware resource usage for IPv4 routes.

```
`switch(config)# **show platform arad ip route summary**

Total number of VRFs: 1
Total number of routes: 25
Total number of route-paths: 21
Total number of lem-routes: 4`
```

- This command shows resources for all IPv4 routes in hardware.
Routes that use the additional hardware resources appear with an asterisk (*).

```
`switch(config)# **show platform arad ip route**

Tunnel Type: M(mpls), G(gre)
* - Routes in LEM
------------------------------------------------------------------------------------------------
|                              Routing Table                                      |             |
|------------------------------------------------------------------------------------------------
|VRF|  Destination   |     |                   |    |Acl  |                 |ECMP | FEC | Tunnel
|ID |    Subnet      | Cmd |    Destination    |VID |Label| MAC / CPU Code  |Index|Index|T Value
------------------------------------------------------------------------------------------------
|0  |0.0.0.0/8       |TRAP |CoppSystemL3DstMiss|0   | -   |ArpTrap          |  -  |1030 |   -
|0  |100.1.0.0/32    |TRAP |CoppSystemIpBcast  |0   | -   |BcastReceive     |  -  |1032 |   -
|0  |100.1.0.0/32    |TRAP |CoppSystemIpUcast  |0   | -   |Receive          |  -  |32766|   -
|0  |100.1.255.255/32|TRAP |CoppSystemIpBcast  |0   | -   |BcastReceive     |  -  |1032 |   -
|0  |200.1.255.255/32|TRAP |CoppSystemIpBcast  |0   | -   |BcastReceive     |  -  |1032 |   -
|0  |200.1.0.0/16    |TRAP |CoppSystemL3DstMiss|1007| -   |ArpTrap          |  -  |1029 |   -
|0  |0.0.0.0/0       |TRAP |CoppSystemL3LpmOver|0   | -   |SlowReceive      |  -  |1024 |   -
|0  |4.4.4.0/24*     |ROUTE|Et10               |1007| -   |00:01:00:02:00:03|  -  |1033 |   -
|0  |10.20.30.0/24*  |ROUTE|Et9                |1006| -   |00:01:00:02:00:03|  -  |1027 |   -`
```


## IP Source Guard


IP Source Guard (IPSG) prevents IP spoofing attacks.


IP Source Guard (IPSG) filters inbound IP packets based on the source MAC and IP addresses.
Hardware supports IPSG. IPSG enabled on a Layer 2 port verifies
IP packets received on this port. EOS permits packets if each
packet source MAC and IP addresses match user-configured IP-MAC
binding entries on the receiving VLAN and port. EOS drops
packets with no match immediately.


### Configuring IPSG


IPSG applies only to Layer 2 ports, and you enable it using the ip verify source command for the Global
Configuration Mode. When configured on Layer 3 ports, IPSG does not take
effect until this interface converts to Layer 2.


Layer 2 Port-Channels, not member ports, support IPSG. The IPSG configuration on port channels
supersedes the configuration on the physical member ports. Therefore, source
IP MAC binding entries should be configured on port channels using the ip source binding command. When configured on a
port channel member port, IPSG does not take effect until deleting this port
from the port channel configuration.


**Examples**

- These configuration commands exclude VLAN IDs
**1** through
**3** from IPSG filtering.
When enabled on a trunk port, IPSG filters the inbound IP
packets on all allowed VLANs. IP packets received on VLANs
**4** through
**10** on
**ethernet 36** filter using
IPSG, while those received on VLANs
**1** through
**3** are
permitted.
```
`switch(config)# **no ip verify source vlan 1-3**
switch(config)# **interface ethernet 36**
switch(config-if-Et36)# **switchport mode trunk**
switch(config-if-Et36)# **switchport trunk allowed vlan 1-10**
switch(config-if-Et36)# **ip verify source**
switch(config-if-Et36)#`
```

- This configuration command configures source IP-MAC binding
entries to IP address **10.1.1.1**,
MAC address **0000.aaaa.1111**,
**VLAN ID 4094**, and
**interface ethernet
36**.
```
`switch(config)# **ip source binding 10.1.1.1 0000.aaaa.1111 vlan 4094 interface ethernet 36**
switch(config)#`
```


### DHCP Server Show Commands


Use the **show dhcp server** command to display DHCP server
information.

- DHCPv4 display
 example:
```
`switch# **show dhcp server ipv4**
IPv4 DHCP Server is active
Debug log is enabled
DNS server(s): 10.2.2.2
DNS domain name: domainFoo
Lease duration: 1 days 0 hours 0 minutes
TFTP server:
serverFoo (Option 66)
10.0.0.3 (Option 150)
TFTP file: fileFoo
Active Leases: 1
IPv4 DHCP interface status:
   Interface   Status
-------------------------------------------------
   Ethernet1   Inactive (Could not determine VRF)
   Ethernet2   Inactive (Not in default VRF)
   Ethernet3   Inactive (Kernel interface not created yet)
   Ethernet4   Inactive (Not up)
   Ethernet5   Inactive (No IP address)
   Ethernet6   Active

Vendor information:
Vendor ID: default
  Sub-options         Data
---------------- ----------------
      1          192.0.2.0, 192.0.2.1

Vendor ID: vendorFoo
  Sub-options       Data
---------------- -----------
      2            192.0.2.2
      3            “Foo”

Subnet: 10.0.0.0/8
Subnet name: subnetFoo
Range: 10.0.0.1 to 10.0.0.10
DNS server(s): 10.1.1.1 10.2.2.2
Lease duration: 3 days 3 hours 3 minutes
Default gateway address: 10.0.0.3
TFTP server:
subnetServerFoo (Option 66)
10.0.0.4 (Option 150)
TFTP boot file: subnetFileFoo
Active leases: 1
Reservations:
MAC address: 1a1b.1c1d.1e1f
IPv4 address: 10.0.0.1

MAC address: 2a2b.2c2d.2e2f
IPv4 address: 10.0.0.2`
```

- For DHCPv6, there are two additional fields in subnet information output,
 **Direct** field and the
 **Relay** field. These two fields specify if
 the DHCP Server is accepting broadcast or relayed messages.
The
**Direct** field displays
**Active** when the subnet matches the
interface with DHCPv6 configured. This indicates the server is accepting broadcast
messages.


The **Direct** field
displays **Inactive** when there is another existing subnet already matching
the interface, or when the subnet matches more than one DHCP configured
interface.


Examples of outputs for the DHCPv6 **show dhcp
server** command:

In this example, DHCPv6 is configured
with subnet **fe80::/10** while being enabled on
**Ethernet1** with address
**fe80::1/64** and on
 **Ethernet3** with address
**fe80::2/64**.
```
`switch# **show dhcp server ipv6**
IPv6 DHCP server is active
Debug log is enabled
DNS server(s): fe80::6
DNS domain name: testaristanetworks.com
Lease duration: 1 days 3 hours 30 minutes
Active leases: 0
IPv6 DHCP interface status:
   Interface    Status
--------------- ------
   Ethernet1    Active
   Ethernet3    Active

Subnet: fe80::/10
Subnet name: foo
Range: fe80::1 to fe80::3
DNS server(s): fe80::4 fe80::5
Direct: Inactive (Multiple interfaces match this subnet: Ethernet1 Ethernet3)
Relay: Active
Active leases: 0`
```

- This example illustrates when multiple subnets match an interface. In this
 example, DHCPv6 is configured with subnets **fc00::/7** and
**fe80::/10** while being enabled on **Ethernet1** with
 address **fe80::1/10** and
 **fc00::1/7**.
```
`switch# **show dhcp server ipv6**
IPv6 DHCP server is active
DNS server(s):  fc00::2
DNS domain name: testaristanetworks.com
Lease duration: 1 days 3 hours 30 minutes
Active leases: 0
IPv6 DHCP interface status:
   Interface    Status
--------------- ------
   Ethernet1    Active

Subnet: fc00::/7
Subnet name: foo
Range: fc00::1 to fc00::5
DNS server(s): fc00::6 fc00::8
Direct: Inactive (This and other subnets match interface Ethernet1)
Relay: Active

Active leases: 0

Subnet: fe80::/10
Subnet name: bar
Direct: Inactive (This and other subnets match interface Ethernet1)
Relay: Active

Active leases: 0`
```

- When a subnet is disabled, the **show dhcp server**
 command displays the disable message with a reason. The number of active leases of
 the disabled subnets will be **0**. In this example, there are
 overlapping subnets.
```
`switch# **show dhcp server**
IPv4 DHCP Server is active
DNS server(s): 10.2.2.2
Lease duration: 1 days 0 hours 0 minutes
Active Leases: 0
IPv4 DHCP interface status:
   Interface   Status
-------------------------------------------------
   Ethernet1   Active

Subnet: 10.0.0.0/24 (Subnet is disabled - overlapping subnet 10.0.0.0/8)
Range: 10.0.0.1 to 10.0.0.10
DNS server(s): 10.3.3.3 10.4.4.4
Default gateway address: 10.0.0.4
Active leases: 0

Subnet: 10.0.0.0/8 (Subnet is disabled - overlapping subnet 10.0.0.0/24)
DNS server(s):
Default gateway address: 10.0.0.3
Active leases: 0`
```

- In this example, the display output shows overlapping
 ranges.
```
`switch# **show dhcp server**
IPv4 DHCP Server is active
DNS server(s): 10.2.2.2
Lease duration: 1 days 0 hours 0 minutes
Active Leases: 0
IPv4 DHCP interface status:
   Interface   Status
-------------------------------------------------
   Ethernet1   Active

Subnet: 10.0.0.0/8 (Subnet is disabled - range 10.0.0.9-10.0.0.12 overlaps with an existing pool)
Range: 10.0.0.1 to 10.0.0.10
Range: 10.0.0.9 to 10.0.0.12
DNS server(s): 10.3.3.3 10.4.4.4
Default gateway address: 10.0.0.4
Active leases: 0`
```

- This example shows duplicate static IP address
 reservation.
```
`Subnet: 10.0.0.0/8 (Subnet is disabled - ipv4-address 10.0.0.11 is reserved more than once)
Subnet name:
DNS server(s):
Default gateway address: 10.0.0.3
Active leases: 0
Reservations:
MAC address: 1a1b.1c1d.1e1f
IPv4 address: 10.0.0.11

MAC address: 2a2b.2c2d.2e2f
IPv4 address: 10.0.0.11`
```

- Use the **show dhcp server leases** command to display
 detailed information about the IP addresses allocated by the DHCP Server (including
 the IP address, the expected end time for that address, the time when the address is
 handed out, and the equivalent MAC
 address).
```
`switch# **show dhcp server leases**
10.0.0.10
End: 2019/06/20 17:44:34 UTC
Last transaction: 2019/06/19 17:44:34 UTC
MAC address: 5692.4c67.460a

2000:0:0:40::b
End: 2019/06/20 18:06:33 UTC
Last transaction: 2019/06/20 14:36:33 UTC
MAC address: 165a.a86d.ffac`
```


## DHCP Server


The router with DHCP Server enabled acts as a server that allocates and delivers
network addresses with desired configuration parameters to its hosts.


The DHCP server is based on ISC Kea.


The router with an DHCP Server enabled acts as a server that allocates and delivers
network addresses with desired configuration parameters to its hosts.


DHCP Server support includes:


DHCPv4 support includes:

- Configurable on different interfaces: Routed, VLAN, LAG, Sub-interface, and LAG
Sub-interface.

- Configurable lease time for allocated network addresses.

- Configurable DNS domain.

- Configurable DNS servers.

- Configurable subnets with parameters:

- Default gateway

- DNS servers

- Ranges

- Lease time


 Additional features for DHCPv4 include:

- Configurable TFTP server

- Configurable TFTP bootfile


 Additional features for DHCPv4 includes:

- Configurable Vendor options with sub options

- Configurable sub option types include: IPv4 address, array of IPv4 addresses,
and string

- TFTP bootfile now supports an URI


Additional features for DHCPv4 include a configurable static IP address for exclusive use
by a given client, based on the client’s MAC address.


Example deployment:


DHCP Server on an aggregation switch, via VXLAN tunnels.


### Configuring DHCP Servers


Global DHCP server options are configured per address family and apply to all
subnets. These commands are accessed at the `**config-dhcp-server**`
level.


To enter the DHCP server global configuration mode, use the following
commands:


```
`switch# **configure**
switch(config)# **dhcp server**
switch(config-dhcp-server)#`
```


To disable the DHCP server:


```
`switch(config-dhcp-server)# **disabled**`
```


Use the following commands to configure the DNS servers. Only two servers can be
configured globally per address family.


```
`switch(config-dhcp-server)# **dns server ipv4 192.0.2.4 192.0.2.5**
switch(config-dhcp-server)# **dns server ipv6 2001:db8:0:10::53 2001:db8:0:10::5353**`
```


The following commands configure the domain names for allocated IP
addresses. For example, add a domain with the name
**podV4.example.com** for DHCPv4 and a domain with the
name **podV6.example.com** for DHCPv6.


```
`switch(config-dhcp-server)# **dns domain name ipv4 podV4.example.com**
switch(config-dhcp-server)# **dns domain name ipv6 podV6.example.com**`
```


The following commands configure lease time for the allocated IP
addresses. For example, configure the lease time as one (1) day.


```
`switch(config-dhcp-server)# **lease time ipv4 1 days 0 hours 0 minutes**
switch(config-dhcp-server)# **lease time ipv6 1 days 0 hours 0 minutes**`
```


The following command configures the TFTP Server-Name. The server can be
in the form of either an IPv4 address or a fully qualified domain
name and only available in DHCPv4. For example, configure the TFTP
server with the IPv4 address, 192.0.2.6.


```
`switch(config-dhcp-server)# **tftp server option 66 ipv4 192.0.2.6**`
```


The following command configures the TFTP Servers.


```
`switch(config-dhcp-server)# **tftp server option 150 ipv4 192.0.2.6 192.0.2.7**`
```


The following command configures the TFTP Server Bootfile-Name, only
available in DHCPv4.


```
`switch(config-dhcp-server)# **tftp server file ipv4 bootfile.conf**`
```


The following command configures Vendor specific option. To enter the
Vendor option submode **config-dhcp-vendor-ipv4** from
**config-dhcp-server** config mode, specify a vendor
class identifier, only available in DHCPv4. For example, Vendor
option for clients with vendor class identifier
vendorClassIDA.


```
`switch(config-dhcp-server)# **vendor-option ipv4 vendorClassIDA**`
```


The following command configures ***default***. If you do not configure the
***default***, the DHCP Server sends the configured Vendor option to
clients requesting a Vendor option with a vendor class identifier that does not match
any configured Vendor option.


```
`switch(config-dhcp-server)# **vendor-option ipv4 default**`
```


The following command configures suboptions for the Vendor. The
configuration sends the resulting Vendor option in a hexadecimal
format to the desired client. The output displays aVendor option
with a suboption with IPv4 address 192.0.2.8, for clients with the
vendor class identifier vendorClassIDA, resulting
in Vendor option 1:4:c0:0:2:8.


```
`Sub option number is 1
Length of the Data is 4
Data is c0:0:2:8
dhcp server
vendor-option ipv4 vendorClassIDA
sub-option 1 type ipv4-address data 192.0.2.8`
```


The following command configures the Vendor option with IPv4 addresses 192.0.2.8 and
192.0.2.9, for clients with the vendor class identifier
vendorClassIDA, resulting in the Vendor option
fe:8:c0:0:2:8:c0:0:2:9.


```
`switch(config-dhcp-server)# **vendor-option ipv4 vendorClassIDA sub-option 254 type array ipv4-address data 192.0.2.8 192.0.2.9**`
```


The following command configures Vendor option with a string “vendor”,
for all clients whose vendor class identifier does not match any
configured Vendor option, resulting in Vendor option
1e:3:46:4f:4f..


```
`switch(config-dhcp-server)# **vendor-option ipv4 default sub-option 30 type string data "vendor"**`
```


The following command sets up Vendor option holding two suboptions, suboption 1 holds
the IPv4 address 192.0.2.8, and suboption 2 holds a string “vendor”, for all clients
whose vendor class identifier does not match any configured Vendor option, resulting in
Vendor option 1:4:c0:0:2:8:2:3:46:4f:4f.


```
`switch(config-dhcp-server)# **vendor-option ipv4 default sub-option 1 type ipv4-address data 192.0.2.8 sub-option 2 type string data “vendor"**`
```


#### Configuring DHCP Server Subnets


DHCP Server settings can also be configured per subnet and
overrides the DHCP Server global mode configurations. There can be
multiple subnets configured, but they must not overlap. EOS disables
overlapping subnets.


The following command enters DHCP Server subnet mode under the
IPv4 address family.


```
`switch# **config**
switch(config)# **dhcp server**
switch(config-dhcp-server)# **subnet 192.0.2.0/32**`
```


The following command configures the name of the subnet. For example, name subnetv4
for DHCPv4.


```
`switch(config-dhcp-subnet-ipv4)# **name subnetv4**`
```


The following command configures range of IP addresses of the subnet. The
range must be within the subnet mask, otherwise the subnet becomes
disabled.


```
`switch(config-dhcp-subnet-ipv4)# **range 192.0.2.100 192.0.2.199**`
```


The following command configures the DNS servers for a subnet. Configure
up to 2 servers per subnet.


```
`switch(config-dhcp-subnet-ipv4-range)# **dns server 192.0.2.1 192.0.2.10**`
```


The following command configures the lease time for allocated IP addresses of the
subnet.
```
`switch(config-dhcp-subnet-ipv4)# **lease time ipv4 3 days 0 hours 0 minutes**`
```


The following command configures the default-gateway for a subnet.

```
`switch(config-dhcp-server)# **subnet 192.0.2.0/32**
switch(config-dhcp-subnet-ipv4)# **default-gateway 192.0.2.3**`
```


The following command configures the TFTP Server-Name for a subnet. The server can be
in the form of either an IPv4 address or a fully qualified domain name, but can only
be configured for
DHCPv4.
```
`switch(config-dhcp-subnet-ipv4)# **tftp server option 66 subnet-tftp.example.com**`
```


The following command configures a list of TFTP servers. The server can only be in
the form of an IP address, but can only be configured for
DHCPv4.
```
`switch(config-dhcp-subnet-ipv4)# **tftp server option 150 192.0.2.6 192.0.2.7**`
```


The following command configures the TFTP server Bootfile-Name for a subnet, but can
only be configured for
DHCPv4.
```
`switch(config-dhcp-subnet-ipv4)# **tftp server file subnet-bootfile.conf**`
```


**Example DHCP Server Subnets
Configuration**
```
`switch# **config**
switch(config)# **dhcp server**
switch(config-dhcp-server)# **subnet 192.0.2.0/32**
switch(config-dhcp-subnet-ipv4)# **name subnetv4**
switch(config-dhcp-subnet-ipv4)# **range 192.0.2.100 192.0.2.199**
switch(config-dhcp-subnet-ipv4-range)# **dns server 192.0.2.1 192.0.2.10**
switch(config-dhcp-subnet-ipv4)# **lease time ipv4 3 days 0 hours 0 minutes**
switch(config-dhcp-server)# **subnet 192.0.2.0/32**
switch(config-dhcp-subnet-ipv4)# **default-gateway 192.0.2.3**
switch(config-dhcp-subnet-ipv4)# **tftp server option 66 subnet-tftp.example.com**
switch(config-dhcp-subnet-ipv4)# **tftp server option 150 192.0.2.6 192.0.2.7**
switch(config-dhcp-subnet-ipv4)# **tftp server file subnet-bootfile.conf**`
```


The following command configures a static IP address for exclusive use by a client.
Enter the **dhcp-server-subnet** configuration submode,
***(config-dhcp-mac-address-ipv4)*** from and specify the client MAC
Address. The IP address must not be used by another client. Only DHCPv4 addresses
allowed for this configuration.

```
`switch(config-dhcp-subnet-ipv4)# **reservations**
switch(config-dhcp-sub-v4-reserve)# **mac-address 1a1b.1c1d.1e1f**
switch(config-dhcp-sub-v4-rsrv-mac-address)# **ipv4-address 192.0.2.0**`
```


### Displaying DHCP Information


#### Show DHCP Server Information


The following command displays the DHCP Server information.


```
`switch# **show dhcp server ipv4**
IPv4 DHCP Server is active
Debug log is enabled
DNS server(s): 192.0.2.4 192.0.2.5
DNS domain name: podV4.example.com
Lease duration: 1 days 0 hours 0 minutes
TFTP server: 192.0.2.6 (Option 66)
192.0.2.6 192.0.2.7 (Option 150)
TFTP file: https://[john.doe@www.example.com](mailto:john.doe@www.example.com):123/example/one
Active Leases: 1
IPv4 DHCP interface status:
Interface   Status
-------------------------------------------------
Ethernet1   Inactive (Could not determine VRF)
Ethernet2   Inactive (Not in default VRF)
Ethernet3   Inactive (Kernel interface not created yet)
Ethernet4   Inactive (Not up)
Ethernet5   Inactive (No IP address)
Ethernet6   Inactive (No Link Local address)
Ethernet7   Inactive (DHCP relay is configured for this interface)
Ethernet8   Inactive (DHCP relay is always on)
Ethernet9   Active

Vendor information:
Vendor ID: default
Sub-options         Data
---------------- ----------------
1          192.0.2.0
2          “vendor”

Vendor ID: vendorClassIDA
Sub-options       Data
---------------- --------------------
254        192.0.2.8, 192.0.2.9

Subnet: 192.0.2.0/24
Subnet name: subnetFooV4
Range: 192.0.2.100 to 192.0.2.199
DNS server(s): 192.0.2.1 192.0.2.10
Lease duration: 3 days 0 hours 0 minutes
Default gateway address: 192.0.2.3
TFTP server:
 subnet-tftp.example.com (Option 66)
 192.0.2.6 192.0.2.7 (Option 150)
 TFTP boot file: subnet-bootfile.conf
 Active leases: 1
 Reservations:
 MAC address: 1a1b.1c1d.1e1f
 IPv4 address: 192.0.2.201
 MAC address: 2a2b.2c2d.2e2f
 IPv4 address: 192.0.2.150`
```


#### Displaying Disabled Subnets


When a subnet becomes disabled, the **show dhcp server
[ipv4|ipv6]** output displays the disabled message under
Disabled reason(s). None of the disabled subnets have active
leases. Currently, the output displays only 2 disabled reasons.


```
`switch# **show dhcp server**
IPv4 DHCP Server is active
DNS server(s): 10.2.2.2
Lease duration: 1 days 0 hours 0 minutes
Active Leases: 0
IPv4 DHCP interface status:
Interface   Status
-------------------------------------------------
Ethernet1   Active

Subnet: 10.0.0.0/24 (Subnet is disabled)
Range: 10.0.0.1 to 10.0.0.10
DNS server(s): 10.3.3.3 10.4.4.4
Default gateway address: 10.0.0.4
Active leases: 0
Disabled reason(s):
Overlapping subnets: 10.0.0.0/8

Subnet: 10.0.0.0/8 (Subnet is disabled)
Range: 10.0.0.1 to 10.0.0.10
DNS server(s): 10.5.5.5
Default gateway address: 10.0.0.3
Active leases: 0
Disabled reason(s):
Overlapping subnets: 10.0.0.0/24

For Overlapping ranges:
switch# **show dhcp server**
IPv4 DHCP Server is active
DNS server(s): 10.2.2.2
Lease duration: 1 days 0 hours 0 minutes
Active Leases: 0
IPv4 DHCP interface status:
Interface   Status
-------------------------------------------------
Ethernet1   Active

Subnet: 10.0.0.0/8 (Subnet is disabled)
Range: 10.0.0.1 to 10.0.0.10
Range: 10.0.0.9 to 10.0.0.12
DNS server(s): 10.3.3.3 10.4.4.4
Default gateway address: 10.0.0.4
Active leases: 0
Disabled reason(s):
Overlapping range: 10.0.0.9 to 10.0.0.12

E.g. Duplicate static IP address reservation:
Subnet: 10.0.0.0/8 (Subnet is disabled)
Subnet name:
Range: 10.0.0.1 to 10.0.0.10
DNS server(s): 10.5.5.5
Default gateway address: 10.0.0.3
Active leases: 0
Reservations:
MAC address: 1a1b.1c1d.1e1f
IPv4 address: 10.0.0.11

MAC address: 2a2b.2c2d.2e2f
IPv4 address: 10.0.0.11

Disabled reason(s):
Duplicate IPv4 address reservation: 10.0.0.11`
```


For DHCPv6, ***Direct*** and ***Relay*** indicates that the DHCP
Server accepts broadcast and relayed messages.


```
`switch# **show dhcp server ipv6**
IPv6 DHCP server is active
Debug log is enabled
DNS server(s): fe80::6
DNS domain name: aristanetworks.example.com
Lease duration: 1 days 3 hours 30 minutes
Active leases: 0
IPv6 DHCP interface status:
Interface    Status
--------------- ------
Ethernet1    Active
Ethernet3    Active

Subnet: fe80::/10
Subnet name: foo
Range: fe80::1 to fe80::3
DNS server(s): fe80::4 fe80::5
Direct: Inactive (Multiple interfaces match this subnet: Ethernet1 Ethernet3)
Relay: Active
Active leases: 0`
```


For DHCPv6, a subnet may match only one interface and vice versa. Otherwise the
subnet is disabled and no lease assigned for that subnet.


```
`interface Ethernet1
no switchport
ipv6 address 2001:db8:0:10::1/64
dhcp server ipv6
interface Ethernet3
no switchport
ipv6 address 2001:db8:0:11::1/64
dhcp server ipv6
dhcp server
subnet 2001:db8::/56`
```


The following enables DHCPv6 on Ethernet1 (with address fc00::1/7 and fe80::1/10),
and then configures subnets fc00::/7 and fe80::/64 for DHCPv6.


```
`interface Ethernet1
no switchport
ipv6 address fc00::1/7
ipv6 address fe80::1/64 link-local
dhcp server ipv6
dhcp server
subnet fc00::/7
subnet fe80::/64

#**show dhcp server ipv6**
IPv6 DHCP server is active
DNS server(s):  fc00::2
DNS domain name: aristanetworks.example.com
Lease duration: 1 days 3 hours 30 minutes
Active leases: 0
IPv6 DHCP interface status:
Interface    Status
--------------- ------
Ethernet1    Active

Subnet: fc00::/7
Subnet name: foo
Range: fc00::1 to fc00::5
DNS server(s): fc00::6 fc00::8
Direct: Inactive (This and other subnets match interface Ethernet1)
Relay: Active

Active leases: 0

Subnet: fe80::/64
Subnet name: subnetBarV6
Direct: Inactive (This and other subnets match interface Ethernet1)
Relay: Active

Active leases: 0`
```


#### Leases


The following output displays the IP addresses allocated by the DHCP Server with the
**show dhcp server [ipv4|ipv6] leases** command. It
also displays the expected end time for the address, the time when the address is
assigned, and the equivalent MAC address.


```
`switch# **show dhcp server leases**
10.0.0.10
End: 2019/06/20 17:44:34 UTC
Last transaction: 2019/06/19 17:44:34 UTC
MAC address: 5692.4c67.460a

2000:0:0:40::b
End: 2019/06/20 18:06:33 UTC
Last transaction: 2019/06/20 14:36:33 UTC
MAC address: 165a.a86d.ffac`
```



## DHCP Relay Global Configuration Mode




Configure DHCP Relay using the dhcp relay command in
 the global configuration mode. The command places the switch in DHCP Relay mode and allows
 the configuration of DHCP Relay on several interfaces with a single command. The
 configuration entered in the DHCP Relay global configuration mode can be overridden by
 equivalent interface specific commands.


**Examples**


The **dhcp relay** command places the switch in the DHCP Relay
 configuration
 mode.
```
`switch(config)# **dhcp relay**
switch(config-dhcp-relay)#`
```


Specify the IP address of the default DHCP or DHCPv6 Server. Multiple IP addresses can be
 specified and DHCP requests forward to all specified helper addresses. Configure an
 **ip helper-address
IP_Address** under each desired routing interface.


Use the following commands to forward DHCP broadcast packets received on interface
 **Ethernet1** and **Vlan2** to DHCP
 servers at **10.0.0.1**, **10.0.0.2**, and to
 hostname
 **DefaultDHCPHostname**:
```
`switch(config)# **interface ethernet1**
switch(config-if-Et1)# **no switchport**
switch(config-if-Et1)# **ip address 192.168.1.1/16**

switch(config)# **interface vlan2**
switch(config-if-Et1)# **ip address 172.16.1.1/16**

switch(config)# **dhcp relay**
switch(config-dhcp-relay)# **server 10.0.0.1**
switch(config-dhcp-relay)# **server 10.0.0.2**
switch(config-dhcp-relay)# **server DefaultDHCPHostname**`
```


Use the following commands to forward DHCPv6 broadcast packets received on interface
 **ethernet1** to a DHCPv6 Server at
 **fc00::3**.
```
`switch(config)# **interface ethernet1**
switch(config-if-Et1)# **no switchport**
switch(config-if-Et1)# **ipv6 address fc00::1/10**

switch(config)# **dhcp relay**
switch(config-dhcp-relay)# **server fc00::3**`
```


The configuration points a routed interface to the specified DHCP and DHCPv6 server, if the
 configuration meets following criteria:

- The default VRF contains the routed interface.

- The interface has an IP address configured.

- The configuration does not occur on a Management or a Loopback interface.




 Use the following commands to remove the default DHCP or DHCPv6
 Server.
```
`switch(config)# **dhcp relay**
switch(config-dhcp-relay)# **no server 10.0.0.1**
switch(config-dhcp-relay)# **no server 10.0.0.2**
switch(config-dhcp-relay)# **no server DefaultDHCPHostname**
switch(config-dhcp-relay)# **no server fc00::3**`
```


To override the default DHCP Server on an interface, the parameter,**ip
 helper-addressIP_Address**, must be used.


Use the following commands to forward a DHCP broadcast packet received on interface
 Ethernet1 to DHCP Servers at **10.0.0.1**,
 **10.0.0.2** and hostname
 **DefaultDHCPHostname**, but VLAN2 broadcasts packets to the
 DHCP Server at **10.0.0.3**
 only.
```
`switch(config)# **interface ethernet 1**
switch(config-if-Et1)# **no switchport**
switch(config-if-Et1)# **ip address 192.168.1.1/16**

switch(config)# **interface vlan2**
switch(config-if-Et1)# **ip address 172.16.1.1/16**
switch(config-if-Et1)# **ip helper-address 10.0.0.3**

switch(config)# **dhcp relay**
switch(config-dhcp-relay)# **server 10.0.0.1**
switch(config-dhcp-relay)# **server 10.0.0.2**
switch(config-dhcp-relay)# **server DefaultDHCPHostname**`
```


To override the default DHCPv6 Server on an interface, the parameter, **ipv6
 helper-address
IPv6_Address>** must be used.


Use the following commands to forward a DHCPv6 broadcast packet received on interface
 Ethernet1 to DHCPv6 Server at **fc00::3**, and VLAN2 broadcasts
 packets to DHCPv6 Server at **fc00::4**
 only.
```
`switch(config)# **interface ethernet 1**
switch(config-if-Et1)# **no switchport**
switch(config-if-Et1)# **ipv6 address fc00::1/10**

switch(config)# **interface vlan2**
switch(config-if-Et1)# **ipv6 address fc00::2/10**
switch(config-if-Et1)# **ipv6 helper-address fc00::4**

switch(config)# **dhcp relay**
switch(config-dhcp-relay)# **server fc00::3**`
```


Configure DHCP Relay for IPv4 unnumbered interfaces by adding a DHCP IPv4 helper address
 and configuring the vendor option.


Use the **information option** command to enter DHCP Relay
 Information Option Configuration
 Mode:
```
`switch(config)# **dhcp relay**
switch(config-dhcp-relay)# **information option**
switch(config-information-option)# **vendor-option**`
```


Configure Option-37 in DHCPv6 Relay to include the host name of the switch along with MAC
 address and interface name in the remote id of the option. It requires the
`remote-id` format to be specified in the configuration mode.


Use the following command to add the
 remote-id:
```
`switch(config)# **ipv6 dhcp relay option remote-id format %m:%h:%p**`
```


You can disable DHCP or DHCPv6 Relay functionality from a specific interface. This disables
 both DHCP Relay global and interface mode configurations.


Use the following command to disable DHCP Relay functionality
 only.
```
`switch(config)# **interface vlan3**
switch(config-if-Et1)# **dhcp relay ipv4 disabled**`
```


Use the following to disable DHCPv6 Relay functionality
 only.
```
`switch(config)# **interface vlan3**
switch(config-if-Et1)# **dhcp relay ipv6 disabled**`
```





### Displaying DHCP Relay


The **show ip dhcp relay** command displays all the
interfaces enabled with DHCP Relay and the server configured on these interfaces.


**Example**
```
`switch# **show ip dhcp relay**
DHCP Relay is active
DHCP Relay Option 82 is disabled
DHCPv6 Relay Link-layer Address Option (79) is disabled
DHCPv6 Relay Remote ID (Option 37) encoding format: MAC address:interface ID
DHCP Smart Relay is disabled
Default L3 interface DHCP servers:
  DHCPv4 servers: 10.0.0.1
                  10.0.0.2
                  DefaultDHCPHostname
  DHCPv6 servers: fc00::3
Interface: Ethernet1
  DHCP Smart Relay is disabled
  DHCPv6 all subnet relaying is disabled
  Using default DHCPv4 servers
  Using default DHCPv6 servers
Interface: Ethernet2
  DHCP Smart Relay is disabled
  DHCPv6 all subnet relaying is disabled
  Using default DHCPv4 servers
  DHCPv6 servers: fc00::4
Interface: Vlan2
  DHCP Smart Relay is disabled
  DHCPv6 all subnet relaying is disabled
  DHCPv4 servers: 11.0.0.3
  DHCPv6 servers: fc00::4
Interface: Vlan3
  DHCP Smart Relay is disabled
  DHCPv6 all subnet relaying is disabled
  DHCPv4 Relay is disabled
  DHCPv6 Relay is disabled`
```


 Use the **show ip dhcp relay** command to display DHCP Relay for unnumbered
 interfaces:

```
`switch# **show ip dhcp relay**
   DHCP Relay Option (82) is enabled
   DHCP Relay vendor-specific suboption (9) under information option (82)`
```


### DHCP Relay Across VRF


The EOS DHCP relay agent supports
forwarding of DHCP requests to DHCP servers located in a different VRF
to the DHCP client interface VRF. In order to enable VRF support for
the DHCP relay agent, Option 82 (DHCP Relay Agent Information Option)
must first be enabled. The DHCP relay agent uses Option 82 to pass client
specific information to the DHCP server.


These sections describe DHCP Relay across VRF features:

- Configuring DHCP Relay

- DHCP Relay Global Configuration Mode Show
Command


The DHCP relay agent inserts Option 82 information into the DHCP forwarded request, which
requires the DHCP server belongs to a network on an interface, and that interface
belongs to a different VRF than the DHCP client interface. Option 82 information
includes the following:

- **VPN identifier** - The VRF name for the ingress interface of the DHCP
request, inserted as sub-option 151.


Table 1. VPN Identifier

| SubOpt
| Len
| ASCII VRF Identifier
|


| 151
| 7
| V
| R
| F
| N
| A
| M
| E
|

- **Link selection** - The subnet address of the interface that receives the
DHCP request, inserted as sub-option 5. After enabling the DHCP smart relay, the
link selection fills with the subnet of the active address. The relay agent sets
the Gateway IP address (gIPaddr) to its IP address so that DHCP messages can be
routed over the network to the DHCP server.
Table 2. Link Selection

| SubOpt
| Len
| Subnet IP Address
|


| 5
| 4
| A1
| A2
| A3
| A4
|

- **Server identifier override** - The primary IP address of the interface that
receives the DHCP request, inserted as sub-option 11. After enabling the DHCP
smart relay, the server identifier fills with the active address, one of the
primary or secondary addresses chosen by smart relay mechanism.
Table 3. Link Selection

| SubOpt
| Len
| Overriding Server Identifier
Address
|


| 11
| 4
| B1
| B2
| B3
| B4
|

- **VSS control suboption as suboption 152** - The DHCP server strips out this
suboption when sending the response to the relay, indicating that the DHCP
server used VPN information to allocate IP address.

- **Circuit ID** - Identifies the circuit, interface or VLAN, on the switch that received the request.

- **Remote ID** - Identifies the remote host.


Note: The DHCP server must be capable of handling VPN identifier information in Option 82.



Direct communication between DHCP client and server may not be possible if they reside in
separate VRFs. The Server identifier override and Link Selection sub-options set the
relay agent to act as the DHCP server, and enable all DHCP communication to flow through
the relay agent.


The relay agent adds all the appropriate sub-options, and forwards all request packets, including
renew and release,to the DHCP server. When the relay receives the DHCP server response
messages, EOS removes Option 82 information and forwards the response to the DHCP client
in the client VRF.


#### Configuring DHCP Relay


The DHCP relay agent information option is inserted in DHCP messages relayed to the DHCP server.
The ip helper-address command enables DHCP relay on an interface
and relays DHCP messages to the specified IPv4 address.


**Example**


This command enables DHCP relay on the **interface ethernet 1/2**;
and relays DHCP messages to the server at
**1.1.1.1**.
```
`switch(config)# **interface ethernet 1/2**
switch(config-if-Et1/2)# **ip helper-address 1.1.1.1**
switch(config-if-Et1/2)#`
```


The commands provided in the following examples enable the attachment of VRF-related tags
in the relay agent information option. If both the DHCP client interface and server
interface exist on the same VRF, default or non-default, then EOS does not insert the
VRF-related DHCP relay agent information option.


**Examples**

- This command configures the DHCP relay to add option 82
information.
```
`switch(config)# **ip dhcp relay information option**`
```

- These commands configures two new VRF instances and assign them Route
Distinguishers
(RDs).
```
`switch(config)# **vrf instance mtxxg-vrf**
switch(config-vrf-mtxxg-vrf)# **router bgp 50**
switch(config-router-bgp)# **vrf mtxxg-vrf**
switch(config-router-bgp-vrf-mtxxg-vrf)# **rd 5546:5546**
switch(config)# **vrf instance qchyh-vrf**
switch(config-vrf-qchyh-vrf)# **router bgp 50**
switch(config-router-bgp)# **vrf qchyh-vrf**
switch(config-router-bgp-vrf-qchyh-vrf)# **rd 218:218**`
```

- This command configures an interface connected to DHCP client in vrf
**mtxxg-vrf** and assigns an IP
address.
```
`switch(config)# **interface ethernet 9**
switch(config-if-Et9)# **no switchport**`
```

- This command configures the DHCP client interface in VRF
**mtxxg-vrf**.
```
`switch(config-if-Et9)# **vrf mtxxg-vrf**
switch(config-if-Et9)# **ip address 10.10.0.1/16**`
```

- This command configures the server interface in VRF
**qchyh-vrf.**
```
`switch(config-if-Et11)# **vrf qchyh-vrf**
switch(config-if-Et11)# **ip address 10.40.0.1/16**`
```

- This command configures a helper address for a DHCP server in VRF
**qchyh-vrf**.
```
`switch(config-if-Et11)# **ip helper-address 10.40.2.3 vrf qchyh-vrf**`
```


##### Configuring Option 82


Use the following commands to enter Information Option (Option 82) insertion and configure the format of information options:


```
`switch(config)# **dhcp relay**
switch(config-dhcp-relay)# **information option**
switch(config-information-option)#`
```


To specify the format for the **circuit-id encoding**, use the following command:


```
`switch(config-information-option)# **circuit-id encoding (%x | %p)**`
```


The default format uses string denoted by **%p**. Setting the encoding to **%x** enables
hex encoding for the circuit ID. The configured value must be a valid hex number. If not configured, DHCP Relay uses the default format.


To specify the format for the **remote-id encoding**, use the following command:


```
`switch(config-information-option)# **remote-id encoding (%x | %p)**`
```


The default format uses string denoted by **%p**. Setting the encoding to **%x** enables
hex encoding for the remote ID. The configured value must be a valid hex number. If not configured, DHCP Relay uses the default format.


#### DHCP Relay Global Configuration Mode Show Command


**Example**


This command displays the VRF specifier for the
server:
```
`switch# **show ip dhcp relay**
DHCP Relay is active
DHCP Relay Option 82 is enabled
DHCP Smart Relay is disabled
Interface: Ethernet9
Option 82 Circuit ID: Ethernet9
DHCP Smart Relay is disabled
DHCP servers: 10.40.2.3
10.40.2.3:vrf=qchyh-vrf`
```


### DHCP Relay in VXLAN EVPN


The ip dhcp relay information option (Global)
command enables the configuration of the DHCP server to uniquely identify
the origin of the request using a source-interface and the helper address.
Configure the source interface with a routable address used by the
DHCP server to uniquely identify the DHCP relay agent that forwarded the
client request.


#### Configuring DHCP Relay in VXLAN EVPN (IPv4)


Use the following command to enable the DHCP relay information option
(**Option 82**) required to specify
a source interface.


```
`switch(config)# **ip dhcp relay information option**`
```


The following configures a Loopback interface as the source interface.


```
`switch(config)# **interface Loopback1**
switch(config-if-Lo1)# **ip address 1.1.1.1/24**`
```


Use the following commands to configure the Loopback interface as the
specified source interface for the helper address.


```
`switch(config)# **interface vlan100**
switch(config-if-Vl100)# **ip helper-address 10.1.1.4 source-interface Loopback1**`
```


Use the following commands to configure the Loopback interface when the
DHCP server resides in a different VRF
(**red**). The source interface must
be configured in the DHCP server VRF for the command to take effect.


```
`switch(config)# **interface Loopback3**
switch(config-if-Lo3)# **vrf red**
switch(config-if-Lo3)# **ip address 1.1.1.1/24**

switch(config)# **interface vlan100**
switch(config-if-Vl100)# **ip helper-address 10.1.1.4 vrf red source-interface Loopback3**`
```


The following command disables the use of source interface along with the
helper address.


```
`switch(config)# **interface vlan100**
switch(config-if-Vl100)# **no ip helper-address 10.1.1.4 source-interface Loopback1**`
```


#### Configuring DHCP Relay in VXLAN EVPN (IPv6)


Use the following commands to configure a local interface.


```
`switch(config)# **interface Loopback2**
switch(config-if-Vl100)# **ipv6 address 2001::10:20:30:1/128**`
```


Use the following commands to configure the Loopback interface as the
local interface for the helper address.


```
`switch(config)# **interface vlan200**
switch(config-if-Vl200)# **ipv6 dhcp relay destination 2002::10:20:30:2 local-interface Loopback2**`
```


Use the following commands to configure the Loopback interface when the
DHCP server is in a different VRF (**red**).
The local interface must be configured in the DHCP server's VRF for
the command to take effect.


```
`switch(config)# **interface Loopback4**
switch(config-if-Lo4)# **vrf red**
switch(config-if-Lo4)# **ipv6 address 2001::10:20:30:1/128**

switch(config)# **interface vlan200**
switch(config-if-Vl200)# **ipv6 dhcp relay destination 2002::10:20:30:2 vrf red local-interface Loopback4**`
```


Use the following command to disable the use of local interface along
with the helper address.


```
`switch(config-if-Vl200)# **no ipv6 dhcp relay destination 2002::10:20:30:2 local-interface Loopback4**`
```


The following command displays the status of DHCP relay option
(**Option 82**) and lists the
configured DHCP servers.


```
`switch# **show ip dhcp relay**
DHCP Relay is active
DHCP Relay Option 82 is enabled
DHCP Smart Relay is disabled
Interface: Vlan100
  Option 82 Circuit ID: Vlan100
  DHCP Smart Relay is disabled
  DHCP servers: 10.1.1.4
Interface: Vlan200
  Option 82 Circuit ID: Vlan100
  DHCP Smart Relay is disabled
  DHCP servers: 2002::10:20:30:2`
```


## DHCP Snooping with Bridging


In this configuration, in addition to sending DHCP packets to relay after
adding information option, the packets can also bridge within the VLAN. In the bridging mode, the
switch intercepts DHCP packets, inserts option-82 if not already present, and bridges the packet
within the VLAN. This mode of DHCP snooping can be configured without DHCP relay
configuration.
Note: EOS supports DHCP Snooping with Bridging on MLAG configurations.



### Configuring DHCP Snooping with Bridging


Following are the steps to configure DHCP snooping with bridging:

- Enable DHCP snooping feature using the ip dhcp snooping
command.
```
`switch# **ip dhcp snooping**`
```

- Enable the insertion of option-82 in DHCP request packets using the ip dhcp snooping information option
command. By default, option-82 is disabled and must be enabled for
DHCP Snooping to be
functional.
```
`switch# **ip dhcp snooping information option**`
```

- Enable DHCP snooping on the corresponding VLANs using the ip dhcp snooping vlan command. By default,EOS
disables DHCP snooping on any
VLAN.
```
`**switch# ip dhcp snooping vlan**`
```

- Set the circuit-id information sent in option-82. By default, EOS sends the
Interface name and VLAN ID. Remote circuit-id contains the MAC address
of the relay
agent.
```
`switch# **ip dhcp snooping information option circuit-id type 2 format**
%h:%p  Hostname and interface name
%p:%v  Interface name and VLAN ID`
```

- Enable bridging capabilities of DHCP snooping using the ip dhcp snooping bridging command. This
command enables DHCP snooping with or without DHCP relay
configuration.
```
`switch# **ip dhcp snooping bridging**`
```







### DHCP Snooping with Bridging Show Commands


The show ip dhcp snooping displays the DHCP snooping with bridging
information.
```
`switch# **show ip dhcp snooping**
DHCP Snooping is enabled
DHCP Snooping is operational
DHCP Snooping is configured on following VLANs:
 650
**DHCP Snooping bridging is operational on following VLANs:**
 650
Insertion of Option-82 is enabled
 Circuit-id sub-option Type: 0
 Circuit-id format: Interface name:Vlan ID
 Remote-id: 00:1c:73:8d:eb:67 (Switch MAC)`
```


### Troubleshooting


- Configure all the needed commands so that DHCP snooping is enabled and operational on all
the VLANs.

- **show ip dhcp snooping** displays whether the DHCP snooping is
operational or not.

- **show ip dhcp snooping counters** displays if snooped packets are
getting dropped or not.

- **show ip dhcp snooping counters debug** displays the reason for
packets getting dropped.
```
`switch# **show ip dhcp snooping counters debug**
Counter                           Requests          Responses
----------------------------- ----------------- -----------------
Received                                      3                 2
Forwarded                                     3                 2
Dropped - Invalid VlanId                      0                 0
Dropped - Parse error                         0                 0
Dropped - Invalid Dhcp Optype                 0                 0
Dropped - Invalid Info Option                 0                 0
Dropped - Snooping disabled                   0                 0`
```

- Check if the packets are hitting the TCAM rule.

```
`switch# **show platform trident tcam detail | grep -i dhcp**
DHCP Snooping uses 3 entries.
…
655402               45 hits - DHCP client to relay trap-to-cpu`
```


## TCP MSS Clamping


TCP MSS clamping limits the value of the Maximum Segment Size (MSS) in the TCP header of TCP SYN
packets transiting a specified Ethernet or tunnel interface.
Setting the MSS ceiling can avoid IP fragmentation in tunnel
scenarios by ensuring that the MSS is low enough to account for
the extra overhead of GRE and tunnel outer IP headers. TCP MSS
clamping can be used when connecting via GRE to cloud providers
that require asymmetric routing.


When MSS clamping is configured on an
interface, if the TCP MSS value in a SYN packet transiting that interface
exceeds the configured ceiling limit it will be overwritten with the
configured limit and the TCP checksum will be recomputed and updated.


TCP MSS clamping is handled by default in the software data path, but the process can be
supported through hardware configuration to minimize possible packet loss and a
reduction in the number of TCP sessions which the switch can establish per second.


### Cautions


*This feature should be used with caution*. When the TCP MSS clamping feature is enabled by
issuing the tcp mss ceiling command
on any routed interface, *all* routed IPv4 TCP SYN
packets (TCP packets with the “SYN” flag set) are sent by
default to the CPU and switched through software, even on
interfaces where no TCP MSS ceiling has been configured,
as long as TCP MSS clamping is enabled. This limits the
number of TCP sessions that can be established through the
switch per second, and, because throughput for software
forwarding is limited, this feature can also cause packet
loss if the rate at which TCP SYN packets are sent to the
CPU exceeds the limits configured in the control-plane
policy map.


Packet loss and TCP session reductions
can be minimized by enabling TCP MSS clamping in hardware, but only SYN
packets in which MSS is the first TCP option are clamped in the hardware
data path; other TCP SYN packets are still switched through software.


To disable MSS clamping, the MSS ceiling must be removed from every interface on which it has
been configured by issuing the **no tcp mss
ceiling** command on each configured
interface.


### Enabling TCP MSS Clamping


There is no global configuration to enable TCP MSS clamping. It is enabled as soon as an MSS ceiling is configured on at least one interface.


### Disabling TCP MSS Clamping


To disable TCP MSS clamping, the MSS ceiling configuration must be removed from every interface
by using the **no** or **default** form of
the tcp mss ceiling command on every interface where a ceiling
has been configured.


### Configuring the TCP MSS Ceiling on an Interface


The TCP MSS ceiling limit is set on an interface using the tcp mss ceiling
command. This also enables TCP MSS clamping on the switch as a whole.


Note: Configuring a TCP MSS ceiling on any interface enables TCP MSS clamping on the switch as a
whole. Without hardware support, clamping routes all TCP SYN packets through
software, even on interfaces where no TCP MSS ceiling has been configured.
This significantly limits the number of TCP sessions the switch can
establish per second, and can potentially cause packet loss if the CPU
traffic exceeds control plane policy limits.
On Sand platform switches (Qumran-MX, Qumran-AX, Jericho, Jericho+), the following limitations
apply:

- This command works only on egress.

- TCP MSS ceiling is supported on IPv4 unicast packets entering
the switch; the configuration has no effect on GRE transit
packets.

- The feature is supported only on IPv4 routed interfaces. It is
not supported on L2 (switchport) interfaces or IPv6 routed
interfaces.

- The feature is not supported for IPv6 packets even if they are
going to be tunneled over an IPv4 GRE tunnel.

- The feature is not supported on VXLAN, loopback or management
interfaces.

- The feature is only supported on IPv4 unicast packets entering
the switch. The configuration has no effect on GRE transit
packets or GRE decap, even if the egress interface has a TCP
MSS ceiling configured.


**Example**


- These commands configure **interface ethernet 5**
as a routed port, then specify a maximum MSS ceiling value of
**1458** bytes for TCP SYN
packets exiting that
port.
```
`switch(config)# **interface ethernet 5**
switch(config-if-Et5)# **no switchport**
switch(config-if-Et5)# **tcp mss ceiling ipv4 1458 egress**
switch(config-if-Et5)#`
```

- These commands apply TCP MSS clamping at **1436**
bytes in the egress direction for IPv6
packets:
```
`switch(config)# **interface ethernet 26**
switch(config)# **tcp mss ceiling ipv6 1436 egress**`
```

- These commands apply TCP MSS clamping at **1476**
bytes for IPv4 packets and **1436** bytes for
IPv6 packets in egress
direction:
```
`switch(config)# **interface ethernet 27**
switch(config)# **tcp mss ceiling ipv4 1476 ipv6 1436 egress**`
```


### Verifying the TCP MSS Clamping


If TCP MSS ceiling is configured on an interface and if the command **show cpu
counters queue | nz** is incrementing in
**CoppSystemL3Ttl1IpOptUcast**
field for Tcp packet with Syn flag, then TCP MSS clamping is being performed
in Software.


```
`switch# **show cpu counters queue | nz**
Fap0.1:
CoPP Class                     Queue    Pkts   Octets   DropPkts   DropOctets
Aggregate
------------------------------------------------------------------------------
CoppSystemL3Ttl1IpOptUcast     TC0      1       82       0          0`
```


### Configuring TCP MSS Clamping


#### Interface Configuration


You can specify the TCP MSS value under the ***interface configuration
mode***. The command syntax is shown below:


**tcp mss ceiling** [ipv4 |
ipv6] **64-65515**
egress


The keyword **egress** specifies that the MSS clamping is
applied on packets transmitted out on the interface in egress direction.


The following example applies TCP MSS clamping at **1436**
bytes in the egress direction for IPv4
packets:
```
`switch(config)# **interface ethernet 25**
switch(config)#**tcp mss ceiling ipv4 1436 egress**`
```


the following example applies TCP MSS clamping at **1436**
bytes in the egress direction for IPv6
packets:
```
`switch(config)# **interface ethernet 26**
switch(config)# **tcp mss ceiling ipv6 1436 egress**`
```


The following example applies TCP MSS clamping at **1476**
bytes for IPv4 packets and **1436** bytes for IPv6 packets in
egress
direction:
```
`switch(config)# **interface ethernet 27**
switch(config)# **tcp mss ceiling ipv4 1476 ipv6 1436 egress**`
```


#### Hardware TCP MSS Clamping Configuration


Hardware MSS clamping requires the system TCAM profile to have TCP MSS clamping
enabled. You can achieve this by creating a user defined TCAM profile as described
below. The [User Defined PMF Profiles - TOI](https://www.arista.com/en/support/toi/eos-4-20-5f/13977-user-defined-pmf-profile) provides
general guidelines on how to create and configure TCAM profiles.


The system TCAM profile must have the feature **tcp-mss-ceiling
ip** in it in order to use hardware MSS clamping. This is
applicable regardless of whether the TCAM profile is copied from an existing profile
or created from scratch.


**Step 1: Create the user defined TCAM profile**


The following example demonstrates copying any source profile and adding the feature
**tcp-mss-ceiling ip**. In this example, the profile
name is **Pro1** and the source profile name is
**Source1**.
```
`(config)# **hardware tcam**
(config-hw-tcam)# **profile Pro1 copy Source1**
(config-hw-tcam-profile-Pro1)# **feature tcp-mss-ceiling ip copy system-feature-source-profile**`
```


TCP MSS clamping is supported only for IPv4 routed packets. Set the packet type for
the feature as follows. This is optional when using **copy
system-feature-source-profile**. In this example, the system
profile name is **Pro1** and the feature name is
**Source1**.
```
`(config-hw-tcam-profile-Pro1-feature-Source1)# **packet ipv4 forwarding routed**`
```


Set the key size limit to **160**. This is also optional when
the feature is copied from **system-feature-source-profile**.
In this example, the system profile name is **Pro1** and the
feature name is
**Source1**.
```
`(config-hw-tcam-profile-Pro1-feature-Source1)# **key size limit 160**`
```


Removing unused features to ensure that the TCP MSS TCAM DB is allocated. In this
example, the system profile name is **Pro1** and the feature
name is
**Source1**.
```
`(config-hw-tcam-profile-Pro1-feature-Source1)# **exit**
(config-hw-tcam-profile-Pro1)# **no feature mirror ip**
(config-hw-tcam-profile-Pro1)# **no feature acl port mac**`
```


**Step 2: Apply the user defined TCAM profile to the system.**


The following example sets the profile as the system profile under the *hardware
tcam* mode. In this example, the system profile name is
**red**.
```
`(config-hw-tcam)# **system profile red**`
```


When the system TCAM profile is changed, it is expected that some agents will
restart. Also it might be necessary to remove some unused features from the TCAM
profile to ensure that the TCP MSS feature gets allocated a TCAM DB. For more
information about configuring TCAM profiles, refer to [User Defined PMF Profiles](https://www.arista.com/en/support/toi/eos-4-20-5f/13977-user-defined-pmf-profile).


Note: The hardware clamping only works for TCP packets with MSS as the first TCP option.
Packets where MSS is not the first TCP option are still trapped to CPU for clamping
in software even if the **feature tcp-mss-ceiling** is
configured in the system TCAM profile.


#### Backward Compatibility


The **tunnel mss ceiling** command which provides the same
functionality is deprecated with the introduction of **tcp mss
ceiling** command. The configuration option **tunnel
mss ceiling** was available only on GRE tunnel interfaces, while
**tcp mss ceiling** is supported on other routed IPv4
interfaces as well.


### TCP MSS Clamping Limitations


- The TCP-MSS Clamping is not supported on L2 (switchport ) interfaces.

- The TCP-MSS Clamping is NOT supported on VXLAN, Loopback and Management
interfaces.

- The TCP-MSS Clamping is supported only in the Egress direction.

- The TCP-MSS Clamping is only supported on unicast routed packets
entering the switch. The configuration has no effect on GRE transit
packets and GRE decap case, even if the Egress interface has TCP MSS
ceiling configured.


**Software TCP MSS Clamping Limitations**


- Once the TCP-MSS Clamping is enabled, all routed TCP-SYN packets will be
software switched, even on interfaces where there is no TCP-MSS
ceiling configuration.

- TCP SYN packets could get dropped under high CPU usage conditions or due
to DOS attack protection mechanisms such as PDP/CoPP. These factors
could limit the TCP connection establishment rate, i.e new TCP
sessions established per second through the switch.


**Hardware MSS Clamping Limitations**


- Hardware TCP-MSS clamping is not supported with host routes when the
clamping is applied on a non-tunnel interface. This limitation does
not apply to GRE tunnel interfaces.

- TCP SYN packets where TCP-MSS is not the first TCP option are trapped to
CPU for MSS adjustment even in hardware MSS clamping mode.

- Hardware TCP-MSS clamping is not supported for IPv6 packets.


### Configuring Hardware Support for TCP MSS Clamping


TCP MSS clamping can be supported
in hardware, but some packets are still routed through the software data
path, and an MSS ceiling value must be configured on each interface where
clamping is to be applied.


Hardware support for clamping is accomplished through the use of a user-defined TCAM profile. The
TCAM profile can be created from scratch or copied
from an existing profile, but in either case it must
include the **tcp-mss-ceiling
ip** feature.


#### Guidelines


- When the system TCAM profile is changed, some agents will restart.

- To ensure that the TCP MSS feature is allocated a TCAM DB, it may be necessary to remove
some unused features from the TCAM profile.

- Hardware TCP MSS clamping only works for TCP packets with MSS as the first TCP option.
Other TCP SYN packets are still trapped to the CPU for clamping in software.

- Hardware TCP MSS clamping is not supported with host routes when the clamping is applied
on a non-tunnel interface. This limitation does not apply to GRE tunnel interfaces.

- The maximum MSS ceiling limit with hardware MSS clamping is 32727 even though the CLI
allows configuration of much larger values.

- For more information on the creation of user-defined TCAM profiles, see [https://www.arista.com/en/support/toi/eos-4-20-5f/13977-user-defined-pmf-profile](https://www.arista.com/en/support/toi/eos-4-20-5f/13977-user-defined-pmf-profile).


To configure hardware support for TCP MSS clamping, create a TCAM profile that includes the tcp mss ceiling feature, then apply it to the system.


#### Creating the TCAM Profile


A TCAM profile that supports
TCP MSS clamping can be created from scratch, or the feature can be added
to a copy of the default TCAM profile. When creating a profile from scratch,
care must be taken to ensure that all needed TCAM features are included
in the profile.


##### Modifying a Copy of the Default TCAM Profile


The following commands create a copy of the default TCAM profile, name it
**tcp-mss-clamping**, and
configure it to enable MSS clamping in hardware, then remove some
unused features included in the default profile to ensure that there
are sufficient TCAM resources for the clamping feature.


```
`switch(config)# **hardware tcam**
switch(config-hw-tcam)# **profile tcp-mss-clamping copy default**
switch(config-hw-tcam-profile-tcp-mss-clampingl)# **feature tcp-mss-ceiling ip copy system-feature-source-profile**
switch(config-hw-tcam-profile-tcp-mss-clamping-feature-tcp-mss-ceiling)# **key size limit 160**
switch(config-hw-tcam-profile-tcp-mss-clamping-feature-tcp-mss-ceiling)# **packet ipv4 forwarding routed**
switch(config-hw-tcam-profile-tcp-mss-clamping-feature-tcp-mss-ceiling)# **exit**

switch(config-hw-tcam-profile-tcp-mss-clamping)# **no feature mirror ip**
switch(config-hw-tcam-profile-tcp-mss-clamping)# **no feature acl port mac**
switch(config-hw-tcam-profile-tcp-mss-clampingl)# **exit**

switch(config-hw-tcam)# **exit**

switch(config)#`
```


#### Applying the TCAM Profile to the System


The following commands enter Hardware TCAM Configuration Mode and set the
**tcp-mss-clamping** profile as the
system profile.


```
`switch(config)# **hardware tcam**
switch(config-hw-tcam)# **system profile tcp-mss-clamping**
switch(config-hw-tcam)#`
```


#### Verifying the TCAM Profile Configuration


The following command displays
hardware TCAM profile information to verify that the user-defined TCAM
profile has been applied correctly.


```
`switch(config)# **show hardware tcam profile**

Configuration        Status
FixedSystem          tcp-mss-clamping         tcp-mss-clamping

switch(config)#`
```


## IPv4 GRE Tunneling


GRE tunneling supports the
forwarding over IPv4 GRE tunnel interfaces. The GRE tunnel interfaces
act as a logical interface that performs GRE encapsulation or decapsulation.


Note: The forwarding over GRE tunnel interface on DCS-7500R
is supported only if all the line cards on the system have Jericho
family chip-set.


### Configuring GRE Tunneling Interface


#### On a Local Arista Switch


```
`switch(config)# **ip routing**
switch(config)# **interface Tunnel 10**
switch(config-if-Tu10)# **tunnel mode gre**
switch(config-if-Tu10)# **ip address 192.168.1.1/24**
switch(config-if-Tu10)# **tunnel source 10.1.1.1**
switch(config-if-Tu10)# **tunnel destination 10.1.1.2**
switch(config-if-Tu10)# **tunnel path-mtu-discovery**
switch(config-if-Tu10)# **tunnel tos 10**
switch(config-if-Tu10)# **tunnel ttl 10**`
```


#### On a Remote Arista Switch


```
`switch(config)# **ip routing**
switch(config)# **interface Tunnel 10**
switch(config-if-Tu10)# **tunnel mode gre**
switch(config-if-Tu10)# **ip address 192.168.1.2/24**
switch(config-if-Tu10)# **tunnel source 10.1.1.2**
switch(config-if-Tu10)# **tunnel destination 10.1.1.1**
switch(config-if-Tu10)# **tunnel path-mtu-discovery**
switch(config-if-Tu10)# **tunnel tos 10**
switch(config-if-Tu10)# **tunnel ttl 10**`
```


#### Alternative Configuration for Tunnel Source IPv4 Address


```
`switch(config)# **interface Loopback 10**
switch(config-if-Lo10)# **ip add 10.1.1.1/32**
switch(config-if-Lo10)# **exit**

switch(config)# **conf terminal**
switch(config)# **interface Tunnel 10**
switch(config-if-Tu10)# **tunnel source interface Loopback 10**`
```


#### Configuration for Adding an IPv4 Route over the GRE Tunnel
Interface


```
`switch(config)# **ip route 192.168.100.0/24 Tunnel 10**`
```


#### Tunnel Mode


Tunnel Mode needs to be configured as gre, for GRE tunnel interface. Default value is
**tunnel mode gre**.


#### IP Address


Configures the IP address for the GRE
tunnel interface. The IP address can be used for routing over the GRE
tunnel interface. The configured subnet is reachable over the GRE tunnel
interface and the packets to the subnet are encapsulated in the GRE header.


#### Tunnel Source


Specifies the source IP address for the
outer IPv4 encapsulation header for packets going over the GRE tunnel
interface. The tunnel source IPv4 address should be a valid local IPv4
address configured on the Arista Switch. The tunnel source can also be
specified as any routed interface on the Arista Switch. The routed interface’s
IPv4 address is assigned as the tunnel source IPv4 address.


#### Tunnel Destination


Specifies the destination IPv4 address
for the outer IPv4 encapsulation header for packets going over the GRE
tunnel interface. The tunnel destination IPv4 should be reachable from
the Arista Switch.


#### Tunnel Path Mtu Discovery


Specifies if the “Do not Fragment”
flag needs to set in the outer IPv4 encapsulation header for packets
going over the GRE tunnel interface.


#### Tunnel TOS


Specifies the Tunnel Type of Service (ToS) value to be assigned to the outer IPv4 encapsulation
header for packets going over the GRE tunnel interface. Default TOS
value of **0** will be assigned if tunnel TOS
is not configured.


#### Tunnel TTL


Specifies the TTL value to the assigned
to the outer IPv4 encapsulation header for packet going over the GRE
tunnel interface. The TTL value is copied from the inner IPv4 header
if tunnel TTL is not configured. The tunnel TTL configuration requires
the tunnel Path MTU Discovery to be configured.


### Displaying GRE tunnel Information


- The following commands
display the tunnel configuration.


```
`switch# **show interfaces Tunnel 10**
Tunnel10 is up, line protocol is up (connected)
 Hardware is Tunnel, address is 0a01.0101.0800
 Internet address is 192.168.1.1/24
 Broadcast address is 255.255.255.255
 Tunnel source 10.1.1.1, destination 10.1.1.2
 Tunnel protocol/transport GRE/IP
   Key disabled, sequencing disabled
   Checksumming of packets disabled
 Tunnel TTL 10, Hardware forwarding enabled
 Tunnel TOS 10
 Path MTU Discovery
 Tunnel transport MTU 1476 bytes
 Up 3 seconds`
```

- ```
`switch# **show gre tunnel static**

Name     Index  Source   Destination  Nexthop  Interface
-------- ------ -------- ------------ -------- -----------
Tunnel10 10     10.1.1.1 10.1.1.2     10.6.1.2 Ethernet6/1

switch# **show tunnel fib static interface gre 10**
Type 'Static Interface', index 10, forwarding Primary
   via 10.6.1.2, 'Ethernet6/1'
      GRE, destination 10.1.1.2, source 10.1.1.1, ttl 10, tos 0xa`
```

- Use the **show platform fap tcam summary** command
to verify if the TCAM bank is allocated for GRE packet termination
lookup.
```
`switch# **show platform fap tcam summary**

           Tcam Allocation (Jericho0)
Bank        Used By     Reserved By
---------- ------------ -----------
0          dbGreTunnel   -`
```

- Use the **show ip route** command to verify if the
routes over tunnel is setup
properly.
```
`switch# **show ip route**

VRF: default
Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B I - iBGP, B E - eBGP,
       R - RIP, I L1 - IS-IS level 1, I L2 - IS-IS level 2,
       O3 - OSPFv3, A B - BGP Aggregate, A O - OSPF Summary,
       NG - Nexthop Group Static Route, V - VXLAN Control Service,
       DH - DHCP client installed default route, M - Martian,
       DP - Dynamic Policy Route

Gateway of last resort is not set

 C      192.168.1.0/24 is directly connected, Tunnel10, Static Interface GRE tunnel
index 10, dst 10.1.1.2, src 10.1.1.1, TTL 10, TOS 10
 S      192.168.100.0/24 is directly connected, Tunnel10, Static Interface GRE
tunnel index 10, dst 10.1.1.2, src 10.1.1.1, TTL 10, TOS 10`
```

- The following commands are used to verify the tunnel encapsulation
programming.
```
`switch# **show platform fap eedb ip-tunnel gre interface Tunnel 10**

-------------------------------------------------------------------------------
|                                                  Jericho0                   |
|                                 GRE Tunnel Egress Encapsulation DB
|
|-----------------------------------------------------------------------------|
| Bank/ | OutLIF | Next   | VSI  | Encap | TOS  | TTL | Source | Destination|
OamLIF| OutLIF | Drop|
| Offset|        | OutLIF | LSB  | Mode  |      |     | IP     | IP         | Set
| Profile|     |
|-----------------------------------------------------------------------------|
| 3/0   | 0x6000 | 0x4010 | 0    | 2     | 10   | 10  | 10.1.1.1 | 10.1.1.2 | No
| 0      | No |

switch# **show platform fap eedb ip-tunnel**

-------------------------------------------------------------------------------
|                                                  Jericho0                    |
|                                     IP Tunnel Egress Encapsulation DB
|
|-----------------------------------------------------------------------------|
| Bank/ | OutLIF | Next   | VSI | Encap| TOS | TTL | Src | Destination | OamLIF
| OutLIF  | Drop|
| Offset|        | OutLIF | LSB | Mode | Idx | Idx | Idx | IP          | Set    |
Profile |     |
|-----------------------------------------------------------------------------|
| 3/0   | 0x6000 | 0x4010 | 0   | 2    | 9   | 0   | 0   | 10.1.1.2    | No     |
0       | No |`
```


## GRE Tunneling Support


GRE tunneling supports the forwarding over IPv4 GRE tunnel interfaces. The GRE tunnel
interfaces act as a logical interface that performs GRE encapsulation or decapsulation.
A maximum of 256 GRE-tunnel interfaces are supported.


Note: GRE keepalives are not supported.
To configure a local Arista switch on a GRE-tunnel interface, consider the following an
example.
```
`switch(config)# **ip routing**
switch(config)# **interface Tunnel 10**
switch(config-if-Tu10)# **tunnel mode gre**
switch(config-if-Tu10)# **ip address 192.168.1.1/24**
switch(config-if-Tu10)# **tunnel source 10.1.1.1**
switch(config-if-Tu10)# **tunnel destination 10.1.1.2**
switch(config-if-Tu10)# **tunnel path-mtu-discovery**
switch(config-if-Tu10)# **tunnel tos 10**
switch(config-if-Tu10)# **tunnel ttl 10**`
```


To configure a remote Arista switch on a GRE-tunnel interface, consider the following an
example.
```
`switch(config)# **ip routing**
switch(config)# **interface Tunnel 10**
switch(config-if-Tu10)# **tunnel mode gre**
switch(config-if-Tu10)# **ip address 192.168.1.2/24**
switch(config-if-Tu10)# **tunnel source 10.1.1.2**
switch(config-if-Tu10)# **tunnel destination 10.1.1.1underlayVrf**
switch(config-if-Tu10)# **tunnel path-mtu-discovery**
switch(config-if-Tu10)# **tunnel tos 10**
switch(config-if-Tu10)# **tunnel ttl 10**`
```


To add a IPv4 route over the GRE-tunnel interface, configure simulare to the following.

```
`switch(config)# **ip route 192.168.100.0/24 Tunnel 10**`
```


Note: IPv6 GRE-Tunnels are not supported. This is only a data-plane limitation whereas IS-IS
IPv6 (such as control-plane) can still work.

Use the **show interfaces Tunnel** command to display the interface
tunnel.


```
`switch(config)# **show interfaces Tunnel 10**
Tunnel10 is up, line protocol is up (connected)
  Hardware is Tunnel, address is 0a01.0101.0800
  Internet address is 192.168.1.1/24
  Broadcast address is 255.255.255.255
  Tunnel source 10.1.1.1, destination 10.1.1.2
  Tunnel protocol/transport GRE/IP
   Key disabled, sequencing disabled
   Checksumming of packets disabled
  Tunnel TTL 10, Hardware forwarding enabled
  Tunnel TOS 10
  Path MTU Discovery
  Tunnel transport MTU 1476 bytes
  Tunnel underlay VRF "underlayVrf"
  Up 3 seconds`
```


Use the **show gre tunnel static** command to display a static
interface tunnel.


```
`switch(config)#**show gre tunnel static**
Name        Index      Source         Destination       Nexthop     Interface
----------- -------    -----------    -------------     ----------  ----------
Tunnel10    10         10.1.1.1       10.1.1.2          10.6.1.2    Ethernet6/1`
```


Use the **show tunnel fib static interface** command to display a
fib static interface tunnel.


```
`switch(config)# **show tunnel fib static interface gre 10**
Type 'Static Interface', index 10, forwarding Primary
   via 10.6.1.2, 'Ethernet6/1'
      GRE, destination 10.1.1.2, source 10.1.1.1, ttl 10, tos 0xa`
```


### Tunnel Mode


Tunnel mode is **GRE** for a GRE-tunnel interface which is also
the default tunnel mode.


### IP address


Use this IP address for routing over the GRE-tunnel interface. The configuration
subnet is reachable over the GRE-tunnel interface, and the packets to the subnet is
encapsulated with the GRE header.


### Tunnel Source


Specifies the source IP address for the encapsulating IPv4 header of a packet going
over the GRE-tunnel interface. The tunnel source IPv4 address is a valid local IPv4
address configured on the Arista switch. It uses any route interface on the Arista
switch. The routed interfaces IPv4 address assigns the tunnel source IPv4 address.
Maximum of 16 unique tunnel source IPv4 addresses are supported across all
GRE-tunnel interfaces.


The following is an example of an interface as a Tunnel source.


```
`switch(config)# **interface Loopback 10**
switch(config-if-Lo10)# **ip add 10.1.1.1/32**
switch(config-if-Lo10)# **exit**
switch(config)# **interface Tunnel 10**
switch(config-if-Tu10)#  **tunnel source interface Loopback 10**`
```


Note: Coexistence of GRE-tunnel interfaces and Decap-Groups is not supported.

Note: Coexistence of GRE-tunnel interfaces and VXLAN is not supported.

Note: GRE-tunnel is not supported with MLAG configuration.

### Tunnel Destination


Specifies the destination IPv4 address for the encapsulating IPv4 header of a packet
going over the GRE-tunnel interface. The tunnel destination IPv4 is reachable from
the Arista switch.


Note:Multicast traffic over GRE-Tunnels is not supported.


### Tunnel Path MTU Discovery


The tunnel path Maximum Transmition Unit (MTU) Discovery specifies if the Don't
Fragment (DF) flag needs to be set in the encapsulating IPv4 header of a packet
going over the GRE-Tunnel interface. MTU configuration on the GRE-tunnel interface
is used by control plane protocols and not enforced in hardware for packets
forwarded in data-plane. The MTU change on the tunnel interface does not take effect
until the tunnel interface is flapped.


### Tunnel TOS


The Tunnel TOS specifies the TOS value to be set in the encapsulating IPv4 header of
a packet going over the GRE-Tunnel interface. The default value of
**0** is assigned if tunnel TOS is not configured.
Maximum of seven unique tunnel TOS values are supported across all GRE-tunnel
interfaces.


### Tunnel TTL


The Tunnel TTL specifies the TTL value to be set in the encapsulating IPv4 header of
a packet going over the GRE-tunnel interface. The TTL value is copied from the inner
IPv4 header if tunnel TTL is not configured. The tunnel TTL configuration requires
the tunnel path MTU discovery to be configured. Maximum of four unique tunnel TTL
values are supported across all GRE-tunnel interfaces.


### VRF Forwarding (Overlay VRF)


 The following configuration is an example of overlay VRF, for a GRE tunnel
interface.
```
`switch(config)# **vrf instance overlayVrf**
switch(config)# **ip routing vrf overlayVrf**
switch(config)# **interface Tunnel 10**
switch(config-if-Tu10)# **vrf overlayVrf**`
```


Note:Both the tunnels source and destination address must be in the underlay VRF. GRE
key forwarding is not supported.
The following is an example of a static route configuration, with an overlay
VRF.
```
`switch(config)# **ip route vrf overlayVrf 7.7.7.0/24 192.168.1.2**`
```


### VRF Forwarding (Underlay VRF)


The following is an configuration example of a underlay VRF for a GRE tunnel
interface.
```
`switch(config)# **vrf instance underlayVrf**
switch(config)# **interface Tunnel 10**
switch(config-if-Tu10)# **tunnel underlay vrf underlayVrf**`
```


### TCAM Bank Allocation


Note: Command to check if Ternary Content-Addressable Memory (TCAM) bank is allocated for
GRE packet termination lookup.

```
`switch(config)# **show platform fap tcam summary**

           Tcam Allocation (Jericho0)
Bank       Used By                   Reserved By
---------- ------------------------- -----------
0           dbGreTunnel               -`
```


PBR is not supported on GRE terminated packets.


#### Verifing Tunnel Routes


Use the **show ip route** command to check if the routes over
tunnel is setup
correctly.
```
`switch(config)# **show ip route**
VRF: default
Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B I - iBGP, B E - eBGP,
       R - RIP, I L1 - IS-IS level 1, I L2 - IS-IS level 2,
       O3 - OSPFv3, A B - BGP Aggregate, A O - OSPF Summary,
       NG - Nexthop Group Static Route, V - VXLAN Control Service,
       DH - DHCP client installed default route, M - Martian,
       DP - Dynamic Policy Route

Gateway of last resort is not set

 C      192.168.1.0/24 is directly connected, Tunnel10, Static Interface GRE-Tunnel index 10, dst 10.1.1.2, src 10.1.1.1, TTL 10, TOS 10
 S      192.168.100.0/24 is directly connected, Tunnel10, Static Interface GRE-Tunnel index 10, dst 10.1.1.2, src 10.1.1.1, TTL 10, TOS 10`
```


#### Verifing Tunnel Encap


Use the **show platform fap eedb ip-tunnel gre interface
Tunnel** command to check the tunnel encap programming on the GRE
interface.


```
`switch(config)# **show platform fap eedb ip-tunnel gre interface Tunnel 10**
 ------------------------------------------------------------------------------------------------------------------
|                                                  Jericho0                                                        |
|                                 GRE Tunnel Egress Encapsulation DB                                               |
|------------------------------------------------------------------------------------------------------------------|
| Bank/   | OutLIF  | Next    | VSI   | Encap | TOS  | TTL  | Source   | Destination     | OamLIF | OutLIF  | Drop |
| Offset  |         | OutLIF  | LSB   | Mode  |      |      | IP       | IP              | Set    | Profile |      |
|------------------------------------------------------------------------------------------------------------------|
| 3/0     | 0x6000  | 0x4010  | 0     | 2     | 10   | 10   | 10.1.1.1 | 10.1.1.2        | No     | 0       | No   |`
```


Use the **show platform fap eedb ip-tunnel** command to check
the tunnel encap programming on the IP-tunnel interface.


```
`switch(config)# **show platform fap eedb ip-tunnel**
 -----------------------------------------------------------------------------------------------------------
|                                                  Jericho0                                                 |
|                                     IP Tunnel Egress Encapsulation DB                                     |
|-----------------------------------------------------------------------------------------------------------|
| Bank/   | OutLIF  | Next    | VSI   | Encap | TOS | TTL | Src | Destination     | OamLIF | OutLIF  | Drop |
| Offset  |         | OutLIF  | LSB   | Mode  | Idx | Idx | Idx | IP              | Set    | Profile |      |
|-----------------------------------------------------------------------------------------------------------|
| 3/0     | 0x6000  | 0x4010  | 0     | 2     | 9   | 0   | 0   | 10.1.1.2        | No     | 0       | No   |`
```


#### Verifing Tunnel VRF


Use the **show ip interface tunnel** command to check the
overlay VRF.


```
`switch(config)# **show ip interface tunnel 10**
Tunnel10 is up, line protocol is up (connected)
  Internet address is 192.168.1.1/24
  Broadcast address is 255.255.255.255
  IPv6 Interface Forwarding : None
  Proxy-ARP is disabled
  Local Proxy-ARP is disabled
  Gratuitous ARP is ignored
  IP MTU 1476 bytes
  VPN Routing/Forwarding "overlayVrf"

switch(config)# **show ip route vrf overlayVrf**

VRF: overlayVrf
Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B I - iBGP, B E - eBGP,
       R - RIP, I L1 - IS-IS level 1, I L2 - IS-IS level 2,
       O3 - OSPFv3, A B - BGP Aggregate, A O - OSPF Summary,
       NG - Nexthop Group Static Route, V - VXLAN Control Service,
       DH - DHCP client installed default route, M - Martian,
       DP - Dynamic Policy Route, L - VRF Leaked

Gateway of last resort is not set

 C        1.1.1.0/24 is directly connected, Ethernet1
 S        7.7.7.0/24 [1/0] via 192.168.1.2, Tunnel10, Static Interface GRE-Tunnel index 10, dst 10.1.1.2, src 10.1.1.1
 C        192.168.1.0/24 is directly connected, Tunnel10, Static Interface GRE-Tunnel index 10, dst 10.1.1.2, src 10.1.1.1`
```


#### Tunnel underlay VRF Configuration


Use the **show interfaces Tunnel** command to check the
underlay
VRF.
```
`switch(config)# **show interfaces Tunnel 10**
Tunnel10 is up, line protocol is up (connected)
  Hardware is Tunnel, address is 0a01.0101.0800
  Internet address is 192.168.1.1/24
  Broadcast address is 255.255.255.255
  Tunnel source 10.1.1.1, destination 10.1.1.2
  Tunnel protocol/transport GRE/IP
   Key disabled, sequencing disabled
   Checksumming of packets disabled
  Tunnel TTL 10, Hardware forwarding enabled
  Tunnel TOS 10
  Path MTU Discovery
  Tunnel transport MTU 1476 bytes
  Tunnel underlay VRF "underlayVrf"
  Up 3 seconds`
```


Use the **show ip route vrf underlayVrf** command to check the
IP route VFR underlayVRF.


```
`switch(config)# **show ip route vrf underlayVrf**
VRF: underlayVrf
Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B - BGP, B I - iBGP, B E - eBGP,
       R - RIP, I L1 - IS-IS level 1, I L2 - IS-IS level 2,
       O3 - OSPFv3, A B - BGP Aggregate, A O - OSPF Summary,
       NG - Nexthop Group Static Route, V - VXLAN Control Service,
       DH - DHCP client installed default route, M - Martian,
       DP - Dynamic Policy Route, L - VRF Leaked,

Gateway of last resort is not set

 C        10.1.1.0/24 is directly connected, Ethernet1`
```


## BfRuntime to Use Non-default VRFs


Use the following commands to configure the VRF for the BfRuntime connection for the management
interface on the switches that support it. The management interface may be configured on a
different VRF from the default one.


### **Configuring BfRuntime to Use Non-default VRFs**


The **platform barefoot bfrt vrf** command configures the forwarding plane
agent to restart and listen on the configured VRFs for
connections.
```
`switch(config)# **platform barefoot bfrt vrf <VRF name>**`
```


If no VRF specified, the configuration uses the default VRF for the IP and port for the the
BfRuntime server.


The following displays a typical
configuration.
```
`switch(config)# **vrf instance management**
switch(config-vrf-management)# **exit**
switch(config)# **platform barefoot bfrt 0.0.0.0 50052**
switch(config)# **platform barefoot bfrt vrf <VRF name>**
switch(config)# **int management1**
switch(config-if-Ma1)# **vrf management**`
```


### Displaying BfRuntime Configuration


The **show platform barefoot bfrt** command displays the existing
configuration for the BfRuntime
server.
```
`switch# **show platform barefoot bfrt**
Namespace: management
FixedSystem:0.0.0.0:50052`
```


## IPv4 Commands


### Cluster Load Balancing Commands


- load-balance cluster

- destination grouping

- flow

- flow source learning

- forwarding type

- load-balance method

- port group host

- balance factor

- flow exhaustion

- flow limit

- flow warning

- member Ethernet


### IP Routing and Address
Commands


- agent SandL3Unicast terminate

- clear arp inspection statistics

- clear snapshot counters ecmp

- compress

- ip arp inspection limit

- ip arp inspection logging

- ip arp inspection trust

- ip arp inspection vlan

- ip hardware fib ecmp resilience

- ip hardware fib load-balance distribution

- ip hardware fib optimize

- ip hardware fib next-hop resource optimization

- ip icmp redirect

- ip load-sharing

- ip route

- ip routing

- ip source binding

- ip verify

- ip verify source

- ipv4 routable
240.0.0.0/4

- rib fib policy

- show dhcp server

- show hardware capacity

- show hardware resource DlbEcmpGroupTable agent *

- show ip

- show ip arp inspection vlan

- show ip arp inspection statistics

- show ip hardware fib
summary

- show hardware resource l3 summary

- show ip interface

- show ip interface brief

- show ip route

- show ip route age

- show ip route gateway

- show ip route host

- show ip route match tag

- show ip route summary

- show ip verify source

- show platform arad ip route

- show platform arad ip route summary

- show rib route ip

- show rib route fib policy excluded

- show rib route summary

- show routing-context vrf

- show snapshot counters ecmp history

- show vrf

- start snapshot counters

- tcp mss ceiling


### IPv4 DHCP Relay Commands


- clear ip dhcp relay counters

- dhcp relay

- ip dhcp relay all-subnets

- ip dhcp relay all-subnets default

- ip dhcp relay always-on

- ip dhcp relay information option (Global)

- ip dhcp relay information option circuit-id

- ip helper-address

- show ip dhcp relay

- show ip dhcp relay counters


### DHCP Server Configuration Commands


- dhcp server

- dhcp server client

- dhcp server debug

- dhcp server dns

- dhcp server lease

- dhcp server option

- dhcp server private-option

- dhcp server subnet

- dhcp server subnet client

- dhcp server tftp

- dhcp server vendor-option

- dhcp server vendor-option ipv4 sub-option

- show dhcp server

- show dhcp server leases


### IPv4 DHCP Snooping Commands


- clear ip dhcp snooping counters

- ip dhcp snooping

- ip dhcp snooping
bridging

- ip dhcp snooping information option

- ip dhcp snooping vlan

- show ip dhcp snooping

- show ip dhcp snooping counters

- show ip dhcp snooping hardware


### IPv4 Multicast Counters Commands


- clear ip multicast count

- ip multicast count


### ARP Table Commands


- arp

- arp aging timeout

- arp cache persistent

- arp gratuitous accept

- arp proxy max-delay

- clear arp-cache

- clear arp

- ip local-proxy-arp

- ip proxy-arp

- show arp

- show ip arp


### VRF Commands


- cli vrf

- description (VRF)

- platform barefoot bfrt vrf

- show platform barefoot bfrt

- show routing-context vrf

- show vrf

- vrf (Interface mode)

- vrf instance


### Trident Forwarding Table Commands


- platform trident forwarding-table partition

- platform trident routing-table partition

- show platform trident forwarding-table partition

- show platform trident l3 shadow dlb-ecmp-group-control


### IPv4 GRE Tunneling Commands


- interface tunnel

- show interface tunnel

- show platform fap eedb ip-tunnel gre interface tunnel

- show platform fap tcam summary

- show tunnel fib static interface gre

- tunnel


### Dynamic Load Balancing


- ip hardware fib ecmp resilience

- ip hardware fib load-balance distribution

- show hardware resource DlbEcmpGroupTable agent *

- show platform trident l3 shadow dlb-ecmp-group-control


### agent SandL3Unicast terminate


The **agent SandL3Unicast terminate** command restarts the
platform Layer 3 agent to ensure optimized IPv4 routes.


**Command Mode**


Global Configuration


**Command Syntax**


**agent SandL3Unicast terminate**


**Related Commands**


- ip hardware fib optimize - Enables IPv4 route
scale.

- show platform arad ip route -Displays resources
for all IPv4 routes in hardware. Routes that use the additional hardware
resources will appear with an asterisk.

- show platform arad ip route summary -Displays
hardware resource usage of IPv4 routes.


**Example**


This configuration command restarts the platform Layer 3 agent to ensure optimized
IPv4.
```
`switch(config)# **agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


Restarting the platform Layer 3 agent results in deletion of all IPv4 routes and
re-adds them to the hardware.


### arp


The **arp** command adds a static entry to an Address
Resolution Protocol (ARP) cache. The switch uses ARP cache entries to correlate
32-bit IP addresses to 48-bit hardware addresses.


The **no arp** and **default arp**
commands remove the ARP cache entry with the specified IP address. When multiple
VRFs contain ARP cache entries for identical IP addresses, each entry can only be
removed individually.


**Command Mode**


Global Configuration


**Command Syntax**


**arp [vrf_instance] ipv4_addr
mac_addr
arpa**


**no arp [vrf_instance]
ipv4_addr**


**default arp [vrf_instance]
ipv4_addr**


**Parameters**

- **vrf_instance** - Specifies the VRF instance
modify.


- **no parameter** - Specify changes to the
default VRF.

- **vrf**
**vrf_name** - Specify changes to the
specified user-defined VRF.

- **ipv4_addr** - Specify the IPv4 address of ARP entry.

- **mac_addr** - Specify the local data-link (hardware) address
(48-bit dotted hex notation – H.H.H).


**Examples**

- This command adds a static entry to the ARP cache in the default
VRF.
```
`switch(config)# **arp 172.22.30.52 0025.900e.c63c arpa**
switch(config)#`
```

- This command adds the same static entry to the ARP cache in the VRF named
**purple**.
```
`switch(config)# **arp vrf purple 172.22.30.52 0025.900e.c63c arpa**
switch(config)#`
```


### arp aging timeout


The **arp aging timeout** command specifies the duration of
dynamic address entries in the Address Resolution Protocol (ARP) cache for addresses
learned through the configuration mode interface. The default duration is
**14400** seconds (four hours).


The **arp aging timeout** and **default arp aging
timeout** commands restores the default ARP aging timeout for
addresses learned on the configuration mode interface by deleting the corresponding
**arp aging timeout** command from
***running-config***.


**Command Mode**


Interface-Ethernet Configuration


Interface-Loopback Configuration


Interface-Management Configuration


Interface-Port-channel Configuration


Interface-VLAN Configuration


**Command Syntax**


**arp aging timeout
arp_time**


**no arp aging timeout**


**default arp aging timeout**


**Parameter**


**arp_time** - Specify the ARP aging timeout period in seconds.
Values range from **60** to
**65535**. Default value is
**14400**.


**Example**


This command specifies an ARP cache duration of **7200**
seconds (two hours) for dynamic addresses added to the ARP cache learned through
**vlan
200**.
```
`switch(config)# **interface vlan 200**
switch(config-if-Vl200)# **arp aging timeout 7200**
switch(config-if-Vl200)# **show active**
interface Vlan200
   arp aging timeout 7200
switch(config-if-Vl200)#`
```


### arp cache dynamic capacity


AARP and IPv6 Neighbor Discovery store neighbor address resolutions in a neighbor cache. The resources and capabilities of the switch determine the capacity of the
neighbor cache. The Neighbor Cache Capacity feature adds parameters to specify a
per-interface capacity for the neighbor cache. A neighboring device, through
misconfiguration or maliciousness, can unfairly use a large number of address
resolutions. This feature mitigates the over-utilization of address resolutions.


**Command Mode**


Interface Configuration Mode


**Command Syntax**


**ipv6 nd cache dynamic capacity capacity**


**no arp cache dynamic capacity**


**default arp cache dynamic capacity**


**Parameters**


- **capacity capacity** - The number of dynamic address resolution entries accepted into the ARP
on the specified interface. Configure a range from 0 to 4294967295. If no capacity specified, then the interface
accepts all neighbor resolutions up to the capacity of the switch platform.


**Example**


Use the following commands to configure an ARP cache of 3000 dynamic address resolution
entries:
```
`switch(config)# **interface Ethernet3/1**
switch(config-if-Et3/1)# **arp cache dynamic capacity 3000**`
```


### arp cache persistent


The **arp cache persistent** command restores the dynamic
entries in the Address Resolution Protocol (ARP) cache after reboot.


The **no arp cache persistent** and **default arp
cache persistent** commands remove the ARP cache persistent
configuration from the ***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


**arp cache persistent**


**no arp cache persistent**


**default arp cache persistent**


**Example**


This command restores the ARP cache after
reboot.
```
`switch(config)# **arp cache persistent**
switch(config)#`
```


### arp gratuitous accept


The **arp gratuitous accept** command configures the
configuration mode interface to accept gratuitous ARP request packets received on
that interface. The ARP table then learns the accepted gratuitous ARP requests.


The no and **default** forms of the command
prevent the interface from accepting gratuitous ARP requests. Configuring gratuitous
ARP acceptance on an L2 interface has no effect.


**Command Mode**


Interface-Ethernet Configuration


Interface-VLAN Configuration


Interface Port-channel Configuration


**Command Syntax**


**arp gratuitous accept**


**no arp gratuitous accept**


**default arp gratuitous accept**


**Example**


These commands configure **interface ethernet 2/1** to accept
gratuitous ARP request
packets.
```
`switch(config)# **interface ethernet 2/1**
switch(config-if-Et2/1)# **arp gratuitous accept**
switch(config-if-Et2/1)#`
```


### arp proxy max-delay


The **arp proxy max-delay** command enables delaying proxy ARP
requests on the configuration mode interface. EOS disables proxy ARP by default.
When enabled, the switch responds to all ARP requests, including gratuitous ARP
requests, with target IP addresses that match a route in the routing table. When a
switch receives a proxy ARP request, EOS performs a check to send the response
immediately or delay the response based on the configured maximum delay in
milliseconds (ms).


**Command Mode**


Configuration mode


**Command Syntax**


**arp proxy max-delay
milliseconds**


**Parameters**


**milliseconds** - Configure the maximum delay before returning
a proxy ARP response in milliseconds. Use a range between 0 and 1000ms with a
default value of 800ms.


**Example**


This command sets a delay of 500ms before returning a response to a proxy ARP
request.
```
`switch(config)# **arp proxy max-delay 500ms**`
```


### balance factor


The **balance factor** command in the Port Group Host Configuration Mode configures port balancing for Cluster Load Balancing on the network.


A higher value results in a more aggressive rebalancing of
flows from a port group, a logical group of hosts, across the available
links, even if the link has a small load imbalance. This is ideal for very
bursty traffic patterns.


Configuring a lower value provides a more
conservative action and only triggers a rebalance when encountering a
significant load difference. This minimizes changes and suitable for more
consistent, long-lived flows.


The **no** version of the command deletes the configuration from the ***running-config***.


**Command Mode**


Cluster Load Balancing Configuration


Port Group Host Configuration


**Command Syntax**


**balance factor factor_value**


**no balance factor factor_value**


**Parameters**


- **balance** - Configure port group balancing.

- **factor
factor_value** - Configure port group balancing factor
from 0-4294967295.




**Example**


Use the following commands to configure a balance factor of 2500 for the port group
*MyPortGroup*:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **port group host MyPortGroup**
switch(config-clb-port-host-MyPortGroup)# **balance factor 2500**
switch(config-clb-port-host-MyPortGroup)#`
```


### clear arp inspection
statistics


The **clear arp inspection statistics** command clears ARP
inspection statistics.


**Command Mode**


EXEC


**Command Syntax**


**clear arp inspection statistics**


**Related Commands**


- ip arp inspection limit

- ip arp inspection logging

- ip arp inspection trust

- ip arp inspection vlan

- show ip arp inspection vlan

- show ip arp inspection statistics


**Example**


This command clears ARP inspection
statistics.
```
`switch(config)# **clear arp inspection statistics**
switch(config)#`
```


### clear arp


The **clear arp** command removes the specified dynamic ARP
entry for the specified IP address from the Address Resolution Protocol (ARP)
table.


**Command Mode**


Privileged EXEC


**Command Syntax**


**clear arp [vrf_instance] ipv4_addr**


**Parameters**

- **vrf_instance** - Specifies the VRF instance for
which arp data is removed.

- **no parameter** - Specifies the
context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF
instance. Specify the system default using the
**default** option.

- **ipv4_addr** - IPv4 address of dynamic ARP
entry.


**Example**


These commands display the ARP table before and after the removal of dynamic ARP
entry for IP address
**172.22.30.52**.
```
`switch# **show arp**

Address         Age (min)  Hardware Addr   Interface
172.22.30.1             0  001c.730b.1d15  Management1
172.22.30.52            0  0025.900e.c468  Management1
172.22.30.53            0  0025.900e.c63c  Management1
172.22.30.133           0  001c.7304.3906  Management1

switch# **clear arp 172.22.30.52**
switch# **show arp**

Address         Age (min)  Hardware Addr   Interface
172.22.30.1             0  001c.730b.1d15  Management1
172.22.30.53            0  0025.900e.c63c  Management1
172.22.30.133           0  001c.7304.3906  Management1

switch#`
```


### clear arp-cache


The **clear arp-cache** command refreshes dynamic entries in
the Address Resolution Protocol (ARP) cache. Refreshing the ARP cache updates
current ARP table entries and removes expired ARP entries not yet deleted by an
internal, timer-driven process.


The command, without arguments, refreshes ARP cache entries for all enabled
interfaces. With arguments, the command refreshes cache entries for the specified
interface. Executing **clear arp-cache** for all interfaces
can result in extremely high CPU usage while the tables are resolving.


**Command Mode**


Privileged EXEC


**Command Syntax**


**clear arp-cache
[vrf_instance][interface_name]**


**Parameters**

- **vrf_instance** - Specifies the VRF instance to refresh
ARP data.

- **no parameter** - Specifies the
context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF instance.
System default VRF specified by
**default**.

- **interface_name** - Interface to refresh ARP cache
entries. Options include the following:

- **no parameter** - All ARP cache entries.

- **interface ethernet**
**e_num** - ARP cache entries of specified
Ethernet interface.

- **interface loopback**
**l_num** - ARP cache entries of specified
loopback interface.

- **interface management**
**m_num** - ARP cache entries of specified
management interface.

- **interface port-channel**
**p_num** - ARP cache entries of specified
port-channel Interface.

- **interface vlan**
**v_num** - ARP cache entries of specified
VLAN interface.

- **interface VXLAN**
**vx_num** - VXLAN interface specified by
**vx_num**.


**Related Commands**


The cli vrf command specifies the context-active VRF.


**Example**


These commands display the ARP cache before and after ARP cache entries
refresh.
```
`switch# **show arp**

Address         Age (min)  Hardware Addr   Interface
172.22.30.1             0  001c.730b.1d15  Management1
172.22.30.118           0  001c.7301.6015  Management1

switch# **clear arp-cache**
switch# **show arp**

Address         Age (min)  Hardware Addr   Interface
172.22.30.1             0  001c.730b.1d15  Management1

switch#`
```


### clear ip dhcp relay counters


The **clear ip dhcp relay counters** command resets the DHCP
relay counters. The configuration mode determines which counters are reset:.


The **Interface configuration** command clears the counter for
the configuration mode interface.


**Command Mode**


Privileged EXEC


**Command Syntax**


**clear ip dhcp relay counters****[interface_name]**


**Parameters**


**interface_name** - Specify the interface to clear counters..
Add the following options:

- **no parameter** - Clears counters for the switch and
for all interfaces.

- **interface ethernet**
**e_num** - Clears counters for the specified Ethernet
interface.

- **interface loopback**
**l_num** - Clears counters for the specified loopback
interface.

- **interface port-channel**
**p_num** - Clears counters for the specified
port-channel Interface.

- **interface vlan**
**v_num**  -Clears counters for the specified VLAN
interface.


**Examples**

- These commands clear the DHCP relay counters for **vlan
1045** and shows the counters before and after the
**clear**
command.
```
`switch# **show ip dhcp relay counters**

          |  Dhcp Packets  |
Interface | Rcvd Fwdd Drop |         Last Cleared
----------|----- ---- -----|---------------------
  All Req |  376  376    0 | 4 days, 19:55:12 ago
 All Resp |  277  277    0 |
          |                |
 Vlan1001 |  207  148    0 | 4 days, 19:54:24 ago
 Vlan1045 |  376  277    0 | 4 days, 19:54:24 ago

switch# **clear ip dhcp relay counters interface vlan 1045**

          |  Dhcp Packets  |
Interface | Rcvd Fwdd Drop |         Last Cleared
----------|----- ---- -----|---------------------
  All Req |  380  380    0 | 4 days, 21:19:17 ago
 All Resp |  281  281    0 |
          |                |
 Vlan1000 |  207  148    0 | 4 days, 21:18:30 ago
 Vlan1045 |    0    0    0 |          0:00:07 ago`
```

- These commands clear all DHCP relay counters on the
switch.
```
`switch(config-if-Vl1045)# **exit**
switch(config)# **clear ip dhcp relay counters**
switch(config)# **show ip dhcp relay counters**

          |  Dhcp Packets  |
Interface | Rcvd Fwdd Drop | Last Cleared
----------|----- ---- -----|-------------
  All Req |    0    0    0 |  0:00:03 ago
 All Resp |    0    0    0 |
          |                |
 Vlan1000 |    0    0    0 |  0:00:03 ago
 Vlan1045 |    0    0    0 |  0:00:03 ago`
```


### clear ip dhcp snooping
counters


The **clear ip dhcp snooping counters** command resets the DHCP
snooping packet counters.


**Command Mode**


Privileged EXEC


**Command Syntax**


clear ip dhcp snooping counters [counter_type]


**Parameters**


**counter_type**  - Specify the type of counter to reset. Options
include the following:

- **no parameter** - Counters for each VLAN.

- **debug** - Aggregate counters and drop cause
counters.


**Examples**

- This command clears the DHCP snooping counters for each
VLAN.
```
`switch# **clear ip dhcp snooping counters**
switch# **show ip dhcp snooping counters**

     | Dhcp Request Pkts | Dhcp Reply Pkts |
Vlan |  Rcvd  Fwdd  Drop | Rcvd Fwdd  Drop | Last Cleared
-----|------ ----- ------|----- ---- ------|-------------
 100 |     0     0     0 |    0    0     0 |  0:00:10 ago

switch#`
```

- This command clears the aggregate DHCP snooping
counters.
```
`switch# **clear ip dhcp snooping counters debug**
switch# **show ip dhcp snooping counters debug**

Counter                       Snooping to Relay Relay to Snooping
----------------------------- ----------------- -----------------
Received                                      0                 0
Forwarded                                     0                 0
Dropped - Invalid VlanId                      0                 0
Dropped - Parse error                         0                 0
Dropped - Invalid Dhcp Optype                 0                 0
Dropped - Invalid Info Option                 0                 0
Dropped - Snooping disabled                   0                 0

Last Cleared:  0:00:08 ago

switch#`
```


### clear ip multicast count


The **clear ip multicast count** command clears all counters
associated with the multicast traffic.


**Command Mode**


Gobal Configuration


**Command Syntax**


clear ip multicast count [group_address
[source_address]]


**Parameters**


- **no parameters** - Clears all counts of the multicast
route traffic.

- **group_address** - Clears the multicast traffic count
of the specified group address.

- **source_address** - Clears the multicast
traffic count of the specified group and source addresses.


**Guidelines**


This command functions only when the ip multicast count
command is enabled.


**Examples**

- This command clears all counters associated with the multicast
traffic.
```
`switch(config)# **clear ip multicast count**`
```

- This command clears the multicast traffic count of the specified group
address.
```
`switch(config)# **clear ip multicast count 16.39.24.233**`
```


### clear snapshot counters ecmp


The **clear shapshot counters ecmp** deletes previous snapshots.


**Command Mode**


EXEC


**Command Syntax**


**clear snapshot counters ecmp req_id_range**


**Parameter**


**req_id_range** - Specify the Request ID of the snapshot to
delete. If none specified, all previous snapshots delete from the switch.


**Example**


To delete previous snapshots, use the following
command:
```
`switch# **clear snapshot counters ecmp id_range**`
```


### cli vrf


The **cli vrf** command specifies the context-active VRF. The
context-active VRF determines the default VRF that VRF-context aware commands use
when displaying routing table data.


**Command Mode**


Privileged EXEC


**Command Syntax**


**cli vrf [vrf_id]**


**Parameters**


**vrf_id** - Specify the name of VRF assigned as the current VRF
scope. Options include the following:

- **vrf_name** - Specify the name of user-defined
VRF.

- **default** - Specify the system-default VRF.


**Guidelines**


VRF-context aware commands include the following:


clear arp-cache


show ip


show ip arp


show ip route


show ip route gateway


show ip route host


**Related Commands**


The show routing-context vrf command displays the
context-active VRF.


**Example**


These commands specify **magenta** as the context-active VRF,
then display the context-active
VRF.
```
`switch# **cli vrf magenta**
switch# **show routing-context vrf**
Current VRF routing-context is magenta
switch#`
```


### compress


The **compress** command increases the hardware resources
available for the specified prefix lengths.


The **no compress** command removes the 2-to-1 compression
configuration from the ***running-config***.


Note: The **compress** command is supported only on 7500R, 7280R, 7500R2 and 7280R2
platforms.


**Command Mode**


Global Configuration


**Command Syntax**


ip hardware fib optimize prefix-length
prefix-length
expand
prefix-length
compress


no ip hardware fib optimize prefix-length
prefix-length
expand
prefix-length
compress


**Parameters**


**compress** - Allows configuring up to one compressed prefix
length.


**Example**


In the following example, configure the prefix length **20**
and **24**, expanding prefix length
**19** and **23**, and compressing
prefix length
**25**.
```
`switch(config)# **ip hardware fib optimize prefix-length 20 24 expand 19 23 compress 25**
 ! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


### description (VRF)


The **description** command adds a text string to the
configuration mode VRF. The string has no functional impact on the VRF.


The **no description** and **default
description** commands remove the text string from the
configuration mode VRF by deleting the corresponding
**description** command from
***running-config***.


**Command Mode**


VRF Configuration


**Command Syntax**


**description
label_text**


**no description**


**default description**


**Parameters**


**label_text** - Specify the character string assigned to the
VRF configuration.


**Related Commands**


The vrf instance command places the switch in VRF configuration
mode.


**Example**


These commands add description text to the **magenta**
VRF.
```
`switch(config)# **vrf instance magenta**
switch(config-vrf-magenta)# **description This is the first vrf**
switch(config-vrf-magenta)# **show active**
 vrf instance magenta
   description This is the first vrf

switch(config-vrf-magenta)#`
```


### destination grouping


The **destination grouping** command in the Cluster Load Balancing
Configuration mode allows the configuration of destination grouping settings with
`**BGP**`, `**prefix**`, or
**`VTEP`** groupings for cluster load balancing. The
**no** version of the command deletes the configuration
from the ***running-config***.


Destination Grouping prevents traffic bottlenecks on the network by distributing the incoming traffic across all available ECMP paths.


**Command Mode**


Cluster Load Balancing Configuration


**Command Syntax**


**destination groupings [bgp field-set] [prefix length length**]
[vtep]


**no destination groupings [bgp field-set] [prefix length length] [vtep]**


**Parameters**


- **destination groupings** - Configure destination grouping parameters for cluster load balancing.


- **bgp field-set** - Specify using BGP field-sets for destination grouping.

- **prefix length length** - Specify using address prefix length for destination grouping. Configure the network prefix length between 0 and 128.

- **vtep** - Specify using a VXLAN tunnel endpoint for destination grouping.


**Example**


Use the following commands to enter Cluster Load Balancing Mode and use BGP field-sets for destination grouping:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **destination grouping bgp field-set**
switch(config-clb)#`
```


### dhcp relay


The **dhcp relay** command places the switch in the DHCP relay
mode. Execute this command in the Global Configuration Mode.


The **no dhcp relay** command removes DHCP relay configuration
from the ***running-config***.


**Command Mode**


Global Configuration Mode


**Command Syntax**


dhcp relay


no dhcp relay


**Example**


The **dhcp relay** command places the switch in the DHCP relay
configuration mode.
```
`switch(config)# **dhcp relay**
switch(config-dhcp-relay)#`
```


### dhcp server


The **dhcp server** command places the switch in the DHCP relay
mode. Execute this command in the DHCP Server Configuration Mode.


The **no dhcp server** command removes DHCP relay configuration
from the ***running-config***.


**Command Mode**


Global Configuration Mode


**Command Syntax**


**dhcp server**


**no dhcp server**


**Example**


The **dhcp server** command places the switch in the DHCP relay
configuration mode.
```
`switch(config)# **dhcp server**
switch(config-dhcp-server)#`
```


### dhcp server client


The **dhcp server client** command configures client options
for the DHCP server.Execute this command under the ***dhcp server configuration
mode***.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


dhcp server client class [ipv4|ipv6] definition
client_class
assignments
[default-gateway|dns|lease|option|private-option|tftp]


**Parameters**


- **[ipv4|ipv6]** - Select the IP address family.

- **definition
client_class** - Add a class for the client
definition.

- **default-gateway** - Configure the client class default
gateway sent to DHCP clients.

- **dns** - Configure the client class DNS.

- **lease** - Configure the client class lease.

- **option** - Configure the client class DHCP options.

- **private-option** - Configure the client class's private options.

- **tftp** - Configure the client class's TFTP
options.


**Example**


Use the **dhcp server client class default-gateway** command to
add a client definition for the IPv4 DHCP client class default gateway of 10.0.0.1.
options.
```
`switch(config-dhcp-server)# **client class ipv4 definition test1 default-gateway 10.0.0.1**`
```


### dhcp server debug


The **dhcp server debug log** command configures DHCP server
debugging configuration. Execute this command in the DHCP Server Configuration Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server debug
log
file**


**Parameters**


**log
file** - Specify the file location to store debugging
logs.


**Example**


Use the **dhcp server log** command to add a file location for
debugging logs.

```
`switch(config-dhcp-server)#**debug log**`
```


### dhcp server dns


The **dhcp server dns** command configures DHCP server DNS
options. Execute this command in the DHCP Server Configuration Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server dns [domain name
domain_name
]
[server [ipv4|ipv6]
ip_address**


**Parameters**


- **domain name domain_name** - Specify the domain name of the DNS server.

- **server [ipv4|ipv6]
ip_address** - Specify the DNS server as IPv4 or IPv6
and the IP address of the server.


**Example**


Use the **dhcp server dns** command to add an IPv4 DNS server,
192.168.10.5, to the DHCP configuration.
options.
```
`switch(config-dhcp-server)# **dns server ipv4 192.168.10.5**`
```


### dhcp server lease


The **dhcp server lease** command configures DHCP server lease
options. Execute this command in the DHCP Server Configuration Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server lease time [ipv4|ipv6]
days
days
hourshours
minutesminutes**


**Parameters**


- **[ipv4|ipv6]** - Configure the lease for IPv4 or IPv6.

- **days** **days** - Specify the number of days for the lease to be in effect from 0 to 2000 days.

- **hours****hours** - Specify the number of hours for the lease to be in effect from 0 to 23 hours.

- **minutes****minutes** - Specify the
number of minutes for the lease to be in effect from 0 to 59 minutes.


**Example**


Use the **dhcp server lease** command to add an IPv4 lease to
be in effect for 10 days, to the DHCP configuration.

```
`switch(config-dhcp-server)# **dns lease time ipv4 10 days**`
```


### dhcp server option


The **dhcp server option** command configures DHCP server
options. Execute this command in the DHCP Server Configuration Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server option [ipv4|ipv6]
code
[always-send data type [hex |string] data]]
>quoted_string >hex
[client-id disable]
hourshours
minutesminutes**


**Parameters**


- **[ipv4|ipv6]** - Configure the option for IPv4 or IPv6.

- **code**- Specify the option number from the DHCP options.

- **[always-send data type [hex |string] data]]** **>quoted_string** **>hex** - Specify to send the option whether or not the client requested it.

- **client-id disable** - Prevent the DHCPv4 server from
sending back the client ID.


**Example**


Use the **dhcp server option** command to add an IPv4 DHCP
code, 67, to the DHCP configuration.

```
`switch(config-dhcp-server)# **option ipv4 option 67**`
```


### dhcp server private-option


The **dhcp server private-option** command configures DHCP
server private options. Execute this command in the DHCP Server Configuration Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server private-option [ipv4|ipv6]
code
[always-send data type [hex |string] data]]
>quoted_string >hex**


**Parameters**


- **[ipv4|ipv6]** - Configure the option for IPv4 or IPv6.

- **code**- Specify the option number from 224 to 254.

- **[always-send data type [hex |string] data]]**
**quoted_string**
**>hex** - Specify to send the option whether or not the
client requested it.


**Example**


Use the **dhcp server option** command to add an IPv4 private
option code, *225*, to always send the option to the DHCP configuration.

```
`switch(config-dhcp-server)# **option ipv4 private-option 225 always-send private-option ipv4 225 always-send type string data "Code Sent"**`
```


### dhcp server subnet


The **dhcp server subnet** command configures DHCP server
subnet options. Execute this command in the DHCP Server Configuration
Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server subnet
ipv4_address
ipv6_address**


**Parameters**


- **ipv4_address**> - Configure the IPv4 subnet.

- **ipv6_address** - Configure the IPv6 subnet.


**Example**


Use the **dhcp server subnet** command to add an IPv4 subnet,
*198.168.0.0/24*, to the DHCP configuration.

```
`switch(config-dhcp-server)# **subnet 198.168.0.0/24**`
```


### dhcp server subnet client


The **dhcp server subnet [ipv4 | ipv6] client** command
configures client options for the DHCP server. Execute this command in the DHCP
Server Configuration Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server subnet [ipv4|ipv6] client class definition
client_class
[default-gateway|dns|lease|name|range|reservations|tftp]**


**Parameters**


- **[ipv4|ipv6]** - Select the IP address family.

- **definition
client_class** - Add a class for the client
definition.

- **default-gateway** **ip_address** - Configure the client class default
gateway sent to DHCP clients.

- **dns server** **** - Configure the client class DNS.

- **lease** **days** **hours****hours**
**minutes****minutes** - Configure the client class lease in days, hours, and minutes.

- **name** **name** - Configure the subnet name.

- **range** **ip_address_start** **ip_address_end** - Configure the range of IP addresses for the subnet.

- **reservations mac-address** **mac_address** **[hostname | ipv4-address]**- Configure the MAC address to use for reservations.

- **tftp** - Configure the client class's TFTP
options.


**Example**


Use the **dhcp server subnet ipv4 client class
default-gateway** command to add a client definition for the IPv4
DHCP client class default gateway of 10.0.0.1.
options.
```
`switch(config-dhcp-server)#**subnet ipv4 client class ipv4 definition test1 default-gateway 10.0.0.1**`
```


### dhcp server tftp


The **dhcp server tftp** command configures DHCP
server TFTP options. Execute this command in the DHCP Server Configuration Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server tftp server [file [ipv4|ipv6]
file_name]
[option [150|66]] ipv4**


**Parameters**


- **file [ipv4|ipv6]** **file_name**> - Configure the IPv4 or IPv6 boot file name.

- **option [150|66]] ipv4**
**ip_address** - Configure the TFTP DHCP option as 150 or
66 with an IPv4 address.


**Example**


Use the **dhcp server tftp** command to add option 150 with an
IPv4 address *198.168.0.11*, to the DHCP configuration.

```
`switch(config-dhcp-server)# **tftp option 150 ipv4 198.168.0.11**`
```


### dhcp server vendor-option


The **dhcp server vendor-option** command configures the DHCP
server vendor identifier options. Execute this command under the DHCP Server
Configuration Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server vendor-option ipv4
vendor_id
default
vendor_id
sub-option
sub-option_code**


**Parameters**


- **vendor_id** - Configure the vendor identifier.

- **default** **vendor_id** - Set as the default vendor specific option.

- **sub-option**
**sub-option_code** - Set the sub-option code from
1-254.


**Example**


Use the **dhcp server vendor-option** command to add vendor
option, *1:4:c0:0:2:8* , to the DHCP configuration.

```
`switch(config-dhcp-server)# **vendor-option 1:4:c0:0:2:8**`
```


### dhcp server vendor-option ipv4 sub-option


The **dhcp server vendor-option** command configures the DHCP
server vendor identifier options. Execute this command in the DHCP Server
Configuration Mode.


**Command Mode**


DHCP Server Configuration Mode


**Command Syntax**


**dhcp server vendor-option ipv4
vendor_id
default
vendor_id
sub-option
sub-option_code
type
[array | ipv4-address |
string]
array [ipv4-address data
ip_address
[string data
quoted_string**


**Parameters**


- **vendor_id** - Configure the vendor identifier.

- **default** **vendor_id** - Set as the default vendor specific option.

- **sub-option**
**sub-option_code** - Set the sub-option code from
1-254.


**Example**


Use the **dhcp server vendor-option** command to add the vendor
option, *1:4:c0:0:2:8*, to the DHCP Server configuration.

```
`switch(config-dhcp-server)# **vendor-option 1:4:c0:0:2:8**`
```


### fib route limit


The **fib route limit** command in the Router General Configuration Mode limits the number of routes added to the Forwarding Information Database (FIB) and
also suppresses BGP routes when exceeding the table limit. The **no** version of the command removes the configuration
from the ***running-config***.


**Command Mode**


Router General Configuration


FIB Route Limit Configuration


VRF Configuration


**Command Syntax**


**[ipv4 | ipv6] limit route_number [warning-limit percent percent]**


**Parameters**


- **[ipv4 | ipv6]** - Configure IPv4 or IPv6 routes to limit in the FIB.

- **limit route_number** - Configure the number of routes to limit in the FIB.

- **warning-limit percent percent** - Configure the percentage of a FIB with routes and issue
a warning. For example, if the FIB has a 100 route limit, and the percentage set to 80, then EOS issues a warning when the FIB has 80 routes.


**Example**


Use the following command to configure a global route limit for IPv4 to 100 and warn when the table has consumed 80%
of the limit:


```
`switch(config)# **router general**
switch(config-router-general)# **fib route limit**
switch(config-router-general-fib-route-limit)# **ipv4 limit 100 warning-limit 80 percent**`
```


### flow


The **flow** command in the Cluster Load Balancing Configuration Mode allows the configuration of flow settings for Cluster Load Balancing including counters, matching, monitoring, sources, and warnings.
The **no** version of the command deletes the configuration from the ***running-config***.




**Command Mode**


Cluster Load Balancing Configuration


**Command Syntax**


**flow [counters] [match encapsulation [none | vxlan] ipv4] [monitor] [warning ungrouped]**


**no flow [counters] [match encapsulation [none | vxlan] ipv4] [monitor] [warning ungrouped]**


**Parameters**


- **flow** - Specify flow behavior for cluster load balancing.


- **counters** - Configure the flow to generate counters for cluster load balancing.

- **match encapsulation [none | vxlan] ipv4** - Specify the flow to match encapsulation for IPv4.

- **monitor** - Configure the flow to monitor cluster load balancing without impacting actual forwarding.

- **warning ungrouped** - Configure the flow to generate warning messages about the cluster load balancing configuration.


**Example**


Use the following commands to enter Cluster Load Balancing Configuration Mode and configure the flow to match VXLAN encapsulation:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **flow match encapsulation vxlan ipv4**
switch(config-clb)#`
```


### flow exhaustion


The **flow exhaustion** command in the Port Group Host Configuration Mode configures flow-related settings for cluster load balancing on the switch.


The **no** version of the command deletes the configuration from the ***running-config***.


**Command Mode**


Cluster Load Balancing Configuration


Port Group Host Configuration


**Command Syntax**


**flow exhaustion action [dscp dscp_value] [traffic-class class_value**


**no flow exhaustion action [dscp dscp_value] [traffic-class class_value**


**Parameters**


- **exhaustion action** - Configure an action when the flows reach limits.

- **dscp dscp_value** - Configure the packet DSCP value from 0 to 63.

- **traffic-class class_value** - Configure the traffic-class value from 0 to 7.


**Example**


Configure the MyPortGroup exhaustion action to use a DSCP value of 25:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **port group host MyPortGroup**
switch(config-clb-port-host-MyPortGroup)# **flow exhaustion action dscp 25**`
```


### flow source learning


The **flow source learning** command enters the Flow Source Learning Configuration Mode and configures cluster load balancing to learn flow sources.


The **no** version of the command deletes the configuration from the ***running-config***.


**Command Mode**


Cluster Load Balancing Configuration


Flow Source Learning Configuration


**Command Syntax**


**flow source learning**


**[aging timeout number_of_seconds seconds | limit  number_of_learned_flows**


**no flow source learning**


**Parameters**


- **flow source learning** - Configure flow discovery by learning.

- **aging timeoutnumber_of_seconds seconds** - Configure the aging timeout between 30 and 2147483647 seconds with a default value of 600 seconds.

- **limit number_of_learned_flows** - Configure the number of flows to learn and preserve hardware TCAM resources.


**Example**


Use the following commands to configure the flow source learning timeout to 1200 seconds:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **flow source learning**
switch(config-clb-flow-learning)# **aging timeout 1200 seconds**
switch(config-clb-flow-learning)#`
```


### flow limit


The **flow limit** command in the Port Group Host Configuration Mode configures flow-related settings for cluster load balancing on the switch.


The **no** version of the command deletes the configuration from the ***running-config***.


**Command Mode**


Cluster Load Balancing Configuration


Port Group Host Configuration


**Command Syntax**


**flow limit max_flows learning max_flows**


**no flow limit max_flows learning max_flows**


**Parameters**


- **flow limit max_flows** - Configure the maximum number of flows per port group.

- **learning max_flows** - Configure the limit of learned flows.




**Example**


Configure the MyPortGroup flow limit to limit learned flows to 25000:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **port group host MyPortGroup**
switch(config-clb-port-host-MyPortGroup)# **flow limit learning 2500**`
```


### flow warning


The **flow warning** command in the Port Group Host Configuration Mode configures flow warning thresholds for cluster load balancing on the switch.


The **no** version of the command deletes the configuration from the ***running-config***.


**Command Mode**


Cluster Load Balancing Configuration


Port Group Host Configuration


**Command Syntax**


**flow warning threshold_flows**


**no flow warning threshold_flows**


**Parameters**


- **flow warning max_flows** - Configure the warning threshold of flows per port group.


**Example**


Configure the MyPortGroup flow warning threshold to 25000:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **port group host MyPortGroup**
switch(config-clb-port-host-MyPortGroup)# **flow warning 2500**`
```





### forwarding type


The **forwarding type** command configures the encapsulation and mode used to deliver packets between TORs over the uplinks.


The **no** version of the command deletes the configuration from the ***running-config***.


**Command Mode**


Cluster Load Balancing Configuration


**Command Syntax**


**forwarding type routed**


**no forwarding type routed**


**Parameters**


- **forwarding type routed**


**Example**


Use the following commands to configure the forwarding type as routed:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **forwarding type routed**
switch(config-clb)#`
```


### interface tunnel


The **interface tunnel** command places the switch in
Interface-Tunnel Configuration Mode.


The **no interface tunnel** command deletes the specified
interface tunnel configuration.


The **exit** command returns the switch to the global
configuration mode.


**Command Mode**


Global Configuration


**Command Syntax**


**interface tunnel
number**


**no interface tunnel
number**


**Parameter**


**number** - Specify the tunnel interface number. Values range
from **0** to **255**.


**Example**


This command places the switch in Interface-Tunnel Configuration Mode for tunnel
interface
**10**.
```
`switch(config)# **interface tunnel 10**
switch(config-if-Tu10)#`
```


### ip arp inspection limit


The **ip arp inspection limit** command disables the interface
if the incoming ARP rate exceeds the configured value rate limit of the incoming ARP
packets on an interface.


**Command Mode**


EXEC


**Command Syntax**


**ip arp inspection limit** [ rate
pps] [burst_interval
**sec | none]**


**no ip arp inspection limit** [ rate
pps] [burst_interval
**sec | none]**


**default ip arp inspection limit** [ rate
pps] [burst_interval
**sec | none]**


**Parameters**

- **rate** - Specifies the ARP inspection limit rate in
packets per second.

- **pps** - Specify the number of ARP inspection
limit rate packets per second.

- **burst_interval** - Specifies the ARP inspection limit
burst interval.

- **sec** - Specify the burst interval in
seconds.


**Related Commands**

- ip arp inspection limit

- ip arp inspection trust

- ip arp inspection vlan

- show ip arp inspection vlan


**Examples**

- This command configures the rate limit of incoming ARP packets to disable
the interface when the incoming ARP rate exceeds the configured value, sets
the rate to **512**, the upper limit for the number of
invalid ARP packets allowed per second, and sets the burst consecutive
interval to monitor the interface for a high ARP rate to
**11** seconds.

```
`switch(config)# **ip arp inspection limit rate 512 burst interval 11**
switch(config)#`
```

- This command displays verification of the interface specific configuration.

```
`switch(config)# **interface ethernet 3/1**
switch(config)# **ip arp inspection limit rate 20 burst interval 5**
switch(config)# **interface Ethernet 3/3**
switch(config)# **ip arp inspection trust**
switch(config)# **show ip arp inspection interfaces**
 
 Interface      Trust State  Rate (pps) Burst Interval
 -------------  -----------  ---------- --------------
 Et3/1          Untrusted    20         5
 Et3/3          Trusted      None       N/A

switch(config)#`
```


### ip arp inspection logging


The **ip arp inspection logging** command enables logging of
incoming ARP packets on the interface if the rate exceeds the configured value.


**Command Mode**


EXEC


**Command Syntax**


**ip arp inspection logging****[rate
pps ][burst_interval
sec | none]**


**no ip arp inspection logging**
**[RATE
pps ][burst_interval**
**sec | none]**


**default ip arp inspection logging**
**[RATE
pps ][burst_interval**
**sec | none]**


**Parameters**


- **RATE** - Specifies the ARP inspection limit rate in
packets per second.

- **pps** -Specifies the number of ARP
inspection limit rate packets per second.

- **burst_interval** - Specifies the ARP inspection limit
burst interval.

- **sec** - Specify the number of burst
interval seconds.


**Related Commands**

- ip arp inspection limit

- ip arp inspection trust

- ip arp inspection vlan

- show ip arp inspection vlan


**Example**


This command enables logging of incoming ARP packets when the incoming ARP rate
exceeds the configured value on the interface, sets the rate to monitor the
interface for a high ARP rate to **15** seconds.

```
`switch(config)# **ip arp inspection logging rate 2048 burst interval 15**
switch(config)#`
```


### ip arp inspection trust


The **ip arp inspection trust**
command configures the trust state of an interface. By default, all interfaces are
untrusted.


**Command Mode**

Global Configuration Mode
**Command Syntax**


ip arp inspection
trust


no ip arp inspection
trust


default ip arp inspection
trust

**Related Commands**

- ip arp inspection limit

- ip arp inspection logging

- show ip arp inspection vlan

- ip arp inspection vlan


**Examples**

- This command configures the trust state of an
interface.
```
`switch(config)# **ip arp inspection trust**
switch(config)#`
```

- This command configures the trust state of an interface to
untrusted.
```
`switch(config)# **no ip arp inspection trust**
switch(config)#`
```

- This command configures the trust state of an interface to the
default.
```
`switch(config)# **default ip arp inspection trust**
switch(config)#`
```


### ip arp inspection vlan


The **ip arp inspection vlan** command enables ARP inspection.
EOS intercepts ARP requests and responses on untrusted interfaces on specified
VLANs, and verifies intercepted packets with valid IP-MAC address bindings. EOS
drops all invalid ARP packets. On trusted interfaces, EOS processes all incoming ARP
packets and forwards without verification. By default, EOS disables ARP inspection
on all VLANs.


**Command Mode**


EXEC


**Command Syntax**


**ip arp inspection vlan [list]**


**Parameters**


**list** - Specifies the VLAN interface number.


**Related Commands**


- ip arp inspection limit

- ip arp inspection trust

- ip arp inspection vlan


**Example**

- This command enables ARP inspection on VLANs **1**
through
**150**.
```
`switch(config)# **ip arp inspection vlan 1 - 150**
switch(config)#`
```

- This command disables ARP inspection on VLANs **1**
through
**150**.
```
`switch(config)# **no ip arp inspection vlan 1 - 150**
switch(config)#`
```

- This command sets the ARP inspection default to VLANs
**1** through
**150**.
```
`switch(config)# **default ip arp inspection vlan 1 - 150**
switch(config)#`
```

- These commands enable ARP inspection on multiple VLANs 1 through
**150** and **200**
through
**250**.
```
`switch(config)# **ip arp inspection vlan 1-150,200-250**
switch(config)#`
```


### ip dhcp relay all-subnets


The **ip dhcp relay all-subnets** command configures the DHCP
smart relay status in the Interface Configuration Mode. DHCP smart relay supports
forwarding DHCP requests with a client secondary IP addresses in the gateway address
field. Enabling DHCP smart relay on an interface requires that you enable DHCP relay
on that interface.


By default, an interface assumes the global DHCP smart relay setting as configured by
the ip dhcp relay all-subnets default command. The
**ip dhcp relay all-subnets** command, when
configured, takes precedence over the global smart relay setting.


The **no ip dhcp relay all-subnets** command disables DHCP
smart relay on the configuration mode interface. The **default ip dhcp
relay all-subnets** command restores the interface to the
default DHCP smart relay setting, as configured by the **ip dhcp relay
all-subnets default** command, by removing the corresponding
**ip dhcp relay all-subnets** or **no ip
dhcp relay all-subnets** statement from
***running-config***.


**Command Mode**


Interface-Ethernet Configuration


Interface-Port-channel Configuration


Interface-VLAN Configuration


**Command Syntax**


ip dhcp relay all-subnets


no ip dhcp relay all-subnets


default ip dhcp relay all-subnets


**Examples**

- This command enables DHCP smart relay on VLAN interface
**100**.
```
`switch(config)# **interface vlan 100**
switch(config-if-Vl100)# **ip helper-address 10.4.4.4**
switch(config-if-Vl100)# **ip dhcp relay all-subnets**
switch(config-if-Vl100)# **show ip dhcp relay**
DHCP Relay is active
DHCP Relay Option 82 is disabled
DHCP Smart Relay is enabled
Interface: Vlan100
  DHCP Smart Relay is enabled
  DHCP servers: 10.4.4.4
switch(config-if-Vl100)#`
```

- This command disables DHCP smart relay on VLAN interface
**100**.
```
`switch(config-if-Vl100)# **no ip dhcp relay all-subnets**
switch(config-if-Vl100)# **show active**
 interface Vlan100
   no ip dhcp relay all-subnets
   ip helper-address 10.4.4.4
switch(config-if-Vl100)# **show ip dhcp relay**
DHCP Relay is active
DHCP Relay Option 82 is disabled
DHCP Smart Relay is enabled
Interface: Vlan100
  DHCP Smart Relay is disabled
  DHCP servers: 10.4.4.4
switch(config-if-Vl100)#`
```

- This command enables DHCP smart relay globally, configures VLAN interface
**100** to use the global setting, then
displays the DHCP relay
status.
```
`switch(config)# **ip dhcp relay all-subnets default**
switch(config)# **interface vlan 100**
switch(config-if-Vl100)# **ip helper-address 10.4.4.4**
switch(config-if-Vl100)# **default ip dhcp relay**
switch(config-if-Vl100)# **show ip dhcp relay**
DHCP Relay is active
DHCP Relay Option 82 is disabled
DHCP Smart Relay is enabled
Interface: Vlan100
  Option 82 Circuit ID: 333
  DHCP Smart Relay is enabled
  DHCP servers: 10.4.4.4
switch(config-if-Vl100)#`
```


### ip dhcp relay all-subnets
default


The **ip dhcp relay all-subnets default** command configures
the global DHCP smart relay setting. DHCP smart relay supports forwarding DHCP
requests with a client secondary IP addresses in the gateway address field. The
default global DHCP smart relay setting is disabled.


The global DHCP smart relay setting applies to all interfaces for which an ip dhcp relay all-subnets statement does not exist. Enabling
DHCP smart relay on an interface requires that you also enable DHCP relay on that
interface.


The **no ip dhcp relay all-subnets default** and
**default ip dhcp relay all-subnets default** commands
restore the global DHCP smart relay default setting of disabled by removing the
**ip dhcp relay all-subnets default** command from
***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


ip dhcp relay all-subnets default


no ip dhcp relay all-subnets default


default ip dhcp relay all-subnets default


**Example**


This command configures the global DHCP smart relay setting to
**enabled**.
```
`switch(config)# **ip dhcp relay all-subnets default**
switch(config)#`
```


### ip dhcp relay always-on


The **ip dhcp relay always-on** command enables the DHCP relay
agent on the switch regardless of the DHCP relay agent status on any interface. By
default, EOS enables the DHCP relay agent only if you have one routable interface
configured with an ip helper-address statement.


The **no ip dhcp relay always-on** and **default ip
dhcp relay always-on** commands remove the **ip dhcp
relay always-on** command from ***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


ip dhcp relay always-on


no ip dhcp relay always-on


default ip dhcp relay always-on


**Example**


This command enables the DHCP relay
agent.
```
`switch(config)# **ip dhcp relay always-on**
switch(config)#`
```


### ip dhcp relay information
option (Global)


The **ip dhcp relay information option** command configures the
switch to attach tags to DHCP requests before forwarding them to the DHCP servers
designated by the ip helper-address commands. The command
specifies the tag contents for packets forwarded by the configured interface. The
default value for each interface configured with an ip helper-address is the name and number of the
interface.


The **no ip dhcp relay information option** and
**default ip dhcp relay information option** commands
restore the switch default setting of not attaching tags to DHCP requests by
removing the **ip dhcp relay information option** command from
***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


ip dhcp relay information option


no ip dhcp relay information option


default ip dhcp relay information option


**Example**


This command enables the attachment of tags to DHCP requests forwarded to DHCP server
addresses.
```
`switch(config)# **ip dhcp relay information option**
switch(config)#`
```


### ip dhcp relay information option circuit-id


The **ip dhcp relay information option circuit-id** command
specifies the content of tags that the switch attaches to DHCP requests before
forwarding them from the configuration mode interface to DHCP server addresses
specified by ip helper-address commands. Tags attach to
outbound DHCP requests only if you enable the information option on the switch
(ip dhcp relay information option circuit-id).


The **no ip dhcp relay information option circuit-id** and
**default ip dhcp relay information option circuit-id** commands restore the default content setting for the
configuration mode interface by removing the corresponding command from
***running-config***.


**Command Mode**


Interface-Ethernet Configuration


Interface-Loopback Configuration


Interface-Management Configuration


Interface-Port-channel Configuration


Interface-VLAN Configuration


**Command Syntax**


ip dhcp relay information option circuit-id
id_label


no ip dhcp relay information option circuit-id


default ip dhcp relay information option circuit-id


**Parameters**


**id_label**- Specifies the tag content. Use a format in
alphanumeric characters (maximum 15 characters).


**Example**


This command configures **x-1234** as the tag content for
packets send from VLAN **200**.

```
`switch(config)# **interface vlan 200**
switch(config-if-Vl200)# **ip dhcp relay information option circuit-id x-1234**
switch(config-if-Vl200)#`
```


### ip dhcp snooping


The **ip dhcp snooping** command enables DHCP snooping globally
on the switch. Configure DHCP snooping as a set of Layer 2 processes and use it with
DHCP servers to control network access to clients with specific IP/MAC addresses.
The switch supports Option-82 insertion,a DHCP snooping process that allows relay
agents to provide remote-ID and circuit-ID information to DHCP reply and request
packets. DHCP servers use this information to determine the originating port of DHCP
requests and associate a corresponding IP address to that port. DHCP servers use
port information to track host location and IP address usage by authorized physical
ports.


DHCP snooping uses the information option (Option-82) to include the switch MAC
address as the router-ID along with the physical interface name and VLAN number as
the circuit-ID in DHCP packets. After adding the information to the packet, the DHCP
relay agent forwards the packet to the DHCP server as specified by the DHCP
protocol.


DHCP snooping on a specified VLAN requires all of these conditions to be met:

- Enable DHCP snooping globally.

- Enabled insertion of option-82 information in DHCP packets.

- Enable DHCP snooping on the specified VLAN.

- Enable DHCP relay on the corresponding VLAN interface.


The **no ip dhcp snooping** and **default ip dhcp
snooping** commands disables global DHCP snooping by removing
the **ip dhcp snooping** command from
***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


ip dhcp snooping


no ip dhcp snooping


default ip dhcp snooping


**Related Commands**


- ip dhcp snooping information option enables
insertion of option-82 snooping data.

- ip helper-address enables the DHCP relay agent on a
configuration mode interface.


**Example**


This command globally enables snooping on the switch, displaying DHCP snooping status
prior and after invoking the
command.
```
`switch(config)# **show ip dhcp snooping**
DHCP Snooping is disabled
switch(config)# **ip dhcp snooping**
switch(config)# **show ip dhcp snooping**
DHCP Snooping is enabled
DHCP Snooping is not operational
DHCP Snooping is configured on following VLANs:
  None
DHCP Snooping is operational on following VLANs:
  None
Insertion of Option-82 is disabled
switch(config)#`
```


### ip dhcp snooping bridging


The **ip dhcp snooping bridging** command enables the DHCP
snooping bridging configuration.


The **no ip dhcp snooping bridging** command removes the DHCP
snooping bridging configuration from the ***running-config***.


**Command Mode**


Global Configuration Mode


**Command Syntax**


ip dhcp snooping bridging


no ip dhcp snooping bridging


**Example**


This command configures the DHCP snooping bridging.

```
`switch# **configure**
switch(config)# **ip dhcp snooping bridging**`
```


### ip dhcp snooping information
option


The **ip dhcp snooping information option** command enables the
insertion of option-82 DHCP snooping information in DHCP packets on VLANs where you
have DHCP snooping enabled. DHCP snooping provides a Layer 2 switch process that
allows relay agents to provide remote-ID and circuit-ID information to DHCP reply
and request packets. DHCP servers use this information to determine the originating
port of DHCP requests and associate a corresponding IP address to that port.


DHCP snooping uses information option (Option-82) to include the switch MAC address
(router-ID) along with the physical interface name and VLAN number (circuit-ID) in
DHCP packets. After adding the information to the packet, the DHCP relay agent
forwards the packet to the DHCP server through DHCP protocol processes.


DHCP snooping on a specified VLAN requires all of these conditions to be met:

- Enable DHCP snooping globally.

- Enabled insertion of option-82 information in DHCP packets.

- Enable DHCP snooping on the specified VLAN.

- Enable DHCP relay on the corresponding VLAN interface.


Ifnot enabling DHCP snooping globally, the **ip dhcp snooping information
option** command persists in
***running-config*** without any operational
effect.


The **no ip dhcp snooping information option** and
**default ip dhcp snooping information option**
commands disable the insertion of option-82 DHCP snooping information in DHCP
packets by removing the **ip dhcp snooping information
option** statement from
***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


ip dhcp snooping information option


no ip dhcp snooping information option


default ip dhcp snooping information option


**Example**


These commands enable DHCP snooping on DHCP packets from ports on snooping-enabled
VLANs. DHCP snooping was previously enabled on the
switch.
```
`switch(config)# **ip dhcp snooping information option**
switch(config)# **show ip dhcp snooping**
DHCP Snooping is enabled
DHCP Snooping is operational
DHCP Snooping is configured on following VLANs:
  100
DHCP Snooping is operational on following VLANs:
  100
Insertion of Option-82 is enabled
  Circuit-id format: Interface name:Vlan ID
  Remote-id: 00:1c:73:1f:b4:38 (Switch MAC)
switch(config)#`
```


### ip dhcp snooping vlan


The **ip dhcp snooping vlan** command enables DHCP snooping on
specified VLANs. DHCP snooping provides a Layer 2 process that allows relay agents
to provide remote-ID and circuit-ID information in DHCP packets. DHCP servers use
this data to determine the originating port of DHCP requests and associate a
corresponding IP address to that port. Configure DHCP snooping on a global and VLAN
basis.


VLAN snooping on a specified VLAN requires each of these conditions:

- Enable DHCP snooping globally.

- Enable insertion of option-82 information in DHCP packets.

- Enable DHCP snooping on the specified VLAN.

- Enable DHCP relay on the corresponding VLAN interface.


If not enabling global DHCP snooping, the **ip dhcp snooping
vlan** command persists in
***running-config*** without any operational
affect.


The **no ip dhcp snooping information option** and
**default ip dhcp snooping information option**
commands disable DHCP snooping operability by removing the **ip dhcp
snooping information option** statement from
***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


ip dhcp snooping vlan
v_range


no ip dhcp snooping vlan
v_range


default ip dhcp snooping vlan
v_range


**Parameters**

- **v_range** - Specifies the range of VLANs to enable
DHCP snooping. Formats include a number, a number range, or a
comma-delimited list of numbers and ranges. Numbers range from
**1** to
**4094**.


**Example**


These commands enable DHCP snooping globally, DHCP snooping on VLAN interface
**100**, and DHCP snooping on
**vlan100**.
```
`switch(config)# **ip dhcp snooping**
switch(config)# **ip dhcp snooping information option**
switch(config)# **ip dhcp snooping vlan 100**
switch(config)# **interface vlan 100**
switch(config-if-Vl100)# **ip helper-address 10.4.4.4**
switch(config-if-Vl100)# **show ip dhcp snooping**
DHCP Snooping is enabled
DHCP Snooping is operational
DHCP Snooping is configured on following VLANs:
  100
DHCP Snooping is operational on following VLANs:
  100
Insertion of Option-82 is enabled
  Circuit-id format: Interface name:Vlan ID
  Remote-id: 00:1c:73:1f:b4:38 (Switch MAC)
switch(config)#`
```


### ip hardware fib ecmp
resilience


The **ip hardware fib ecmp resilience** command enables
resilient ECMP for the specified IP address prefix and configures a fixed number of
next hop entries in the hardware ECMP table for that prefix. In addition to
specifying the maximum number of next hop addresses that the table can contain for
the prefix, the command includes a redundancy factor that allows duplication of each
next hop address. The fixed table space for the address is the maximum number of
next hops multiplied by the redundancy factor.


Resilient ECMP is useful when it is undesirable for routes to be rehashed due to link
flap, as when using ECMP for load balancing.


The **no ip hardware fib ecmp resilience** and
**default ip hardware fib ecmp resilience** commands
restore the default hardware ECMP table management by removing the **ip
hardware fib ecmp resilience** command from
***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


ip hardware fib ecmp resilience
net_addr
capacity
nhop_max
redundancy
duplicates


no ip hardware fib ecmp resilience
net_addr


default ip hardware fib ecmp resilience
net_addr


**Parameters**

- **net_addr** - Specify the IP address prefix managed
by command. (CIDR or address-mask).

- **nhop_max** - Specify the maximum number of next-hop
addresses for specified IP address prefix. Value range varies by
platform:

- Helix: <**2** to
**64**>

- Trident: <**2** to
**32**>

- Trident II: <**2** to
**64**>

- **duplicates** - Specifies the redundancy factor.
Value ranges from **1** to
**128**.


**Example**


This command configures a hardware ECMP table space of 24 entries for the IP address
**10.14.2.2/24**. A maximum of six next-hop addresses
can be specified for the IP address. When the table contains six next-hop addresses,
each appears in the table four times. When the table contains fewer than six
next-hop addresses, each is duplicated until the 24 table entries are
filled.
```
`switch(config)# **ip hardware fib ecmp resilience 10.14.2.2/24 capacity 6 redundancy 4**
switch(config)#`
```


### ip hardware fib load-balance distribution


The **ip hardware fib load-balance distribution** command allows the configuration of
dynamic load balancing (DLB) on ECMP Groups. The **no** and **default**
versions of the command disables the feature and returns the configuration to the traditional hash-based load balancing.


**Command Mode**


Global Configuration


**Command Syntax**


**ip hardware fib load-balance distribution [dynamic | hash]
average-traffic-weight
average_traffic_weight_value
flow-set-size
flow_set_size_value
inactivity
inactivity_value
sampling-period
sampling_period
seed
hash_seed
member-selection [optimal always | optimal timer]**


**Parameters**


- **hash** - Specify to use hash-based load balancing, the
default behavior.

- **dynamic** - Specify to use dynamic load balancing with ECMP
groups.

- **average-traffic-weigh
average_traffic_weight_value** - Specifies a
value between 1 and 15 with a default value of 1. A higher weight value
gives preference to average values over instantaneous values.

- **flow-set-size
flow_set_size_value** - Specifies the number of
flow set entries allocated to each DLB group.

- **inactivity
inactivity_value** - Specifies the amount of
time for a flow set to be idle before reassigning to an optimal
port.


- **member-selection [optimal always
| optimal timer]** - Specifies when to select an
optimal port for the next packet in a flow.

- **optimal always** - Specifies to always
pick the optimal member whether or not the inactivity duration
has elapse.

- **optimal timer** - If the inactivity
duration has elapsed, pick the optimal member.

- **sampling-period
sampling_period** - Specify the duration
between two consecutive sampling of port state data with a default value
of 16 microseconds.

- **seed
hash_seed** - Specify a value for random number
generation by optimal candidate random selection process to select a
port when two or more ports have the same optimal quality.


**Example**


Use the following command to set the DLB member selection to optimal
always:

```
`switch(config)# **ip hardware fib load-balance distribution dynamic optimal always**`
```


Use the following command


### ip hardware fib next-hop resource optimization


The **ip hardware fib next-hop resource optimization** command
enables or disables the resource optimization features on the switch. By default,
EOS enables the feature on the switch.


The **no hardware fib next-hop resource optimization** command
removes all the resource optimization features running on the switch.


**Command Mode**


Global Configuration Mode


**Command Syntax**


ip hardware fib next-hop resource optimization
options


no ip hardware fib next-hop resource optimization
options


**Parameters**

- Use one of the following two options to configure this command:

- **disabled** - Disable hardware resource
optimization for adjacency programming.

- **thresholds** - Utilization percentage for
starting or stopping optimization. The resource utilization
percentage value ranges from 0 to 100. It can be set to low and
high.


**Examples**


- The following command disables all hardware resource optimization
features on the
switch:
```
`switch# **configure terminal**
switch(config)# **ip hardware fib next-hop resource optimization disabled**`
```

- The following command configures the thresholds for starting and
stopping the
optimization:
```
`switch(config)# **ip hardware fib next-hop resource optimization thresholds low 20 high 80**`
```


### ip hardware fib optimize


The **ip hardware fib optimize** command enables IPv4 route
scale. Restart the platform Layer 3 agent to ensure optimization of IPv4 routes with
the agent SandL3Unicast terminate command for the
configuration mode interface.


**Command Mode**


Global Configuration


**Command Syntax**


ip hardware fib optimize exact-match prefix-length
prefix-length
prefix-length




**Parameters**


**prefix-length** - Specifies the length of the prefix equal to
**12**, **16**,
**20**, **24**,
**28**, or **32**. Optionally,
add one additional prefix-length limited to the prefix-length of
**32**.


**Related Commands**


- The agent SandL3Unicast terminate command restarts
the Layer 3 agent to ensure optimization of IPv4 routes.

- The show platform arad ip route command shows
resources for all IPv4 routes in hardware. Routes with additional hardware
resources appear with an asterisk (*).

- The show platform arad ip route summary
command displays hardware resource usage of IPv4 routes.


**Examples**

- This configuration command allows configuring prefix lengths
**12** and **32**

```
`switch(config)# **ip hardware fib optimize exact-match prefix-length 12 32**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


One of the two prefixes in this command has a prefix-length of
**32**, required in the instance when
adding two prefixes. For this command to take effect, restart the
platform Layer 3 agent.

- This configuration command restarts the platform Layer 3 agent to ensure
optimization of IPv4
routes.
```
`switch(config)# **agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


Restarting the platform Layer 3 agent results in deletion of all IPv4
routes, and then re-added to the hardware.

- This configuration command allows configuring prefix lengths
**32** and
**16**.
```
`switch(config)# **ip hardware fib optimize exact-match prefix-length 32 16**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


One of the two prefixes in this command is a prefix-length of
**32**, required when adding two prefixes.
For this command to take effect, restart the platform Layer 3 agent.

- This configuration command restarts the platform Layer 3 agent to ensure
optimization of IPv4
routes.
```
`switch(config)# **agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


Restarting the platform Layer 3 agent results in deletion of all IPv4
routes, and then re-added to the hardware.

- This configuration command allows configuring prefix length
**24**.
```
`switch(config)# **ip hardware fib optimize exact-match prefix-length 24**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


In this instance, add one prefix-length, and does not require a
prefix-length of **32**. For this command to take
effect, restart the platform Layer 3 agent.

- This configuration command restarts the platform Layer 3 agent to ensure
optimization of IPv4
routes.
```
`switch(config)# **agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


Restarting the platform Layer 3 agent results in deletion of all IPv4
routes, and then re-added to the hardware.

- This configuration command allows configuring the prefix length of
**32**.
```
`switch(config)# **ip hardware fib optimize exact-match prefix-length 32**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are optimized`
```


For this command to take effect, restart the platform Layer 3 agent.

- This configuration command restarts the platform Layer 3 agent to ensure
optimization of IPv4
routes.
```
`switch(config)# **agent SandL3Unicast terminate**
SandL3Unicast was terminated`
```


Restarting the platform Layer 3 agent results in deletion of all IPv4
routes, and then re-added to the hardware.

- This configuration command disables configuring prefix lengths
**12** and
**32**.
```
`switch(config)# **no ip hardware fib optimize exact-match prefix-length 12 32**
! Please restart layer 3 forwarding agent to ensure IPv4 routes are not optimized`
```


One of the two prefixes in this command has a prefix-length of
**32**, required when configuring two
prefixes. For this command to take effect, restart the platform Layer 3
agent.


### ip hardware fib optimize prefixes


The **ip hardware fib optimize prefixes** command in the Global Configuration Mode reserves IPv4 optimized prefixes on
the default and non-default VRFs.


The **no** version of the command explicitly removes the configuration from the ***running-config*** on the switch.


**Command Mode**


Global Configuration


**Command Syntax**


**ip hardware fib optimize vrf vrf_name prefixes minimum count num_prefixes**


**no ip hardware fib optimize vrf vrf_name prefixes minimum count num_prefixes**


**Parameters**


 - **vrf
 vrf_name** - Specify the VRF to minimize prefixes.

- **prefixes minimum count
num_prefixes** - Specify the minimum number of prefixes to
optimize on the VRF.


**Example**


Use the following command to create reservations for 25 IPv4 optimized prefixes on VRF blue:


```
`switch(config)# ip hardware fib optimize vrf blue prefixes minimum count 25
! Please restart the SandL3Unicast agent to reserve space for optimized FIB prefixes`
```


### ip helper-address


The **ip helper-address** command enables the DHCP relay agent
on the Interface Configuration Mode and specifies a forwarding address for DHCP
requests. An interface configured with multiple helper-addresses forwards DHCP
requests to all specified addresses.


The **no ip helper-address** and **default ip
helper-address** commands remove the corresponding
**ip helper-address** command from
***running-config***. Commands that do not
specify an IP helper-address remove all helper-addresses from the interface.


**Command Mode**


Interface-Ethernet Configuration


Interface-Port-channel Configuration


Interface-VLAN Configuration


**Command Syntax**


ip helper-address
ipv4_addr [vrf
vrf_name][source-address
ipv4_addr | source-interface
interfaces]


no ip helper-address [ipv4_addr]


default ip helper-address [ipv4_addr]


**Parameters**

- **vrf**
**vrf_name** - Specifies the user-defined VRF for DHCP
server.

- **ipv4_addr** - Specifies the DHCP server address
accessed by interface.

- **source-address**
**ipv4_addr** - Specifies the source IPv4 address to
communicate with DHCP server.

- **source-interface**
**interfaces** - Specifies the source interface to
communicate with DHCP server. varnames include:

- **Ethernet**
**eth_num** -  Specifies the Ethernet
interface number.

- **Loopback**
**lpbck_num** - Specifies the loopback
interface number. Value ranges from **0**
to **1000**.

- **Management**
**mgmt_num** -  Specifies the management
interface number. Accepted values are **1**
and **2**.

- **Port-Channel**
{**int_num** |
**sub_int_num**} -  Specifies the
port-channel interface or subinterface number. Value of interface
ranges from **1** to
**2000**. Value of sub-interface
ranges from **1** to
**4094**.

- **Tunnel**
**tnl_num** - Specifies the tunnel interface
number. Value ranges from **0** to
**255**.

- **VLAN**
**vlan_num** - Specifies the Ethernet
interface number. Value ranges from **1**
to **4094**.


**Related Commands**

- ip dhcp relay always-on

- ip dhcp relay information option (Global)

- ip dhcp relay information option circuit-id


**Guidelines**


If specifying the source-address parameter, then the DHCP client receives an IPv4
address from the subnet of source IP address. The source-address must be one of the
configured addresses on the interface.


**Examples**

- This command enables DHCP relay on the VLAN interface
**200**; and configure the switch to forward
DHCP requests received on this interface to the server at
**10.10.41.15**.
```
`switch(config)# **interface vlan 200**
switch(config-if-Vl200)# **ip helper-address 10.10.41.15**
switch(config-if-Vl200)# **show active**
interface Vlan200
   ip helper-address 10.10.41.15
switch(config-if-Vl200)#`
```

- This command enables DHCP relay on the **interface ewthernet
1/2**; and configures the switch to use
**2.2.2.2** as the source IP address when
relaying IPv4 DHCP messages to the server at
**1.1.1.1**.
```
`switch(config)# **interface ethernet 1/2**
switch(config-if-Et1/2)# **ip helper-address 1.1.1.1 source-address 2.2.2.2**
switch(config-if-Et1/2)#`
```


### ip icmp redirect


The **ip icmp redirect** command enables the transmission of
ICMP redirect messages. Routers send ICMP redirect messages to notify data link
hosts of the availability of a better route for a specific destination.


The **no ip icmp redirect** disables the switch from sending
ICMP redirect messages.


**Command Mode**


Global Configuration


**Command Syntax**


ip icmp redirect


no ip icmp redirect


default ip icmp redirect


**Example**


This command disables the redirect
messages.
```
`switch(config)# **no ip icmp redirect**
switch(config)# **show running-config**
              <-------OUTPUT OMITTED FROM EXAMPLE-------->
!
no ip icmp redirect
ip routing
!
               <-------OUTPUT OMITTED FROM EXAMPLE-------->
switch(config)#`
```


### ip load-sharing


The **ip load-sharing** command provides the hash seed to an
algorithm the switch uses to distribute data streams among multiple equal-cost
routes to an individual IPv4 subnet.


In a network topology using Equal-Cost Multipath routing, all switches performing
identical hash calculations may result in hash polarization, leading to uneven load
distribution among the data paths. Hash polarization is avoided when switches use
different hash seeds to perform different hash calculations.


The **no ip load-sharing** and **default ip
load-sharing** commands return the hash seed to the default
value of zero by removing the **ip load-sharing** command from
***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


**ip load-sharing
hardware
seed**


**no ip load-sharing
hardware**


**default ip load-sharing
hardware**


**Parameters**

- **hardware** - The ASIC switching device. The
available options depend on the switch platform.

- **arad**

- **fm6000**

- **petraA**

- **trident**

- **seed**     The hash seed. Value ranges vary by
switch platform. The default value on all platforms is
**0**.

- when
**hardware**=**arad**     **seed**
ranges from **0** to
**2**.

- when
**hardware**=**fm6000**     **seed**
ranges from **0** to
**39**.

- when
**hardware**=**petraA**     **seed**
ranges from **0** to
**2**.

- when
**hardware**=**trident**     **seed**
ranges from **0** to
**5**.


**Example**


This command sets the IPv4 load sharing hash seed to one on FM6000 platform
switches.
```
`switch(config)# **ip load-sharing fm6000 1**
switch(config)#`
```


### ip local-proxy-arp


The **ip local-proxy-arp** command enables local proxy ARP
(Address Resolution Protocol) in the Interface Configuration Mode. When enabling
local proxy ARP, ARP requests received in the Interface Configuration Mode returns
an IP address even when the request comes from within the same subnet.


The **no ip local-proxy-arp** and **default ip
local-proxy-arp** commands disable local proxy ARP on the
configuration mode interface by removing the corresponding **ip
local-proxy-arp** command from
***running-config***.


**Command Mode**


Interface-Ethernet Configuration


Interface-Loopback Configuration


Interface-Management Configuration


Interface-Port-channel Configuration


Interface-VLAN Configuration


**Command Syntax**


ip local-proxy-arp


no ip local-proxy-arp


default ip local-proxy-arp


**Example**


These commands enable local proxy ARP on VLAN interface
**140**
```
`switch(config)# **interface vlan 140**
switch(config-if-Vl140)# **ip local-proxy-arp**
switch(config-if-Vl140)# **show active**
interface Vlan140
   ip local-proxy-arp
switch(config-if-Vl140)#`
```

.


### ip multicast count


The **ip multicast count** command enables the IPv4 multicast
route traffic counter of group and source addresses in either bytes or packets.


The **no ip multicast count** command deletes all multicast
counters including the routes of group and source addresses.


The **no ip multicast count *group_address
source_address***command removes the current
configuration of the specified group and source addresses. It does not delete the
counter because the wildcard is still active.


The **default ip multicast count** command reverts the current
counter configuration of multicast route to the default state.


**Command Mode**


Global Configuration


**Command Syntax**


**ip multicast count [group_address
[source_address] | bytes |
packets]**


**no ip multicast count [group_address
[source_address] | bytes |
packets]**


**default ip multicast count [group_address
[source_address] | bytes |
packets]**


**Parameters**


- **group_address** - Configures the multicast route
traffic count of the specified group address.

- **source_address** - Configures the multicast
route traffic count of the specified group and source
addresses.

- **bytes** - Configures the multicast route traffic
count to bytes.

- **packets** - Configures the multicast route traffic
count to packets.


**Guidelines**


This command is supported on the FM6000 platform only.


**Examples**

- This command configures the multicast route traffic count to
bytes.
```
`switch(config)# **ip multicast count bytes**`
```

- This command configures the multicast route traffic count of the specified
group and source
addresses.
```
`switch(config)# **ip multicast count 10.50.30.23 45.67.89.100**`
```

- This command deletes all multicast counters including the routes of group
and source
addresses.
```
`switch(config)# **no ip multicast count**`
```

- This command reverts the current multicast route configuration to the
default
state.
```
`switch(config)# **default ip multicast count**`
```


### ip proxy-arp


The **ip proxy-arp** command enables proxy ARP in the Interface
Configuration Mode. Proxy ARP is disabled by default. When enabled, the switch
responds to all ARP requests, including gratuitous ARP requests, with target IP
addresses that match a route in the routing table.


The **no ip proxy-arp** and **default ip
proxy-arp** commands disable proxy ARP on the Interface
Configuration Mode by removing the corresponding **ip
proxy-arp** command from ***running-config***.


**Command Mode**


Interface-Ethernet Configuration


Interface-Loopback Configuration


Interface-Management Configuration


Interface-Port-channel Configuration


Interface-VLAN Configuration


**Command Syntax**


ip proxy-arp


no ip proxy-arp


default ip proxy-arp


**Example**


This command enables proxy ARP on **interface ethernet
4**.
```
`switch(config)# **interface ethernet 4**
switch(config-if-Et4)# **ip proxy-arp**
switch(config-if-Et4)#`
```


### ip route


The **ip route** command creates a static route. The
destination can be a network segment, and the next-hop address can be either an IPv4
address or a routable port. When multiple routes exist to a destination prefix, the
route with the lowest administrative distance takes precedence.


By default, the administrative distance assigned to static routes is 1. Assigning a higher administrative distance to a static route configures it to be overridden by dynamic routing data. For example, a static route with an administrative distance value of 200 is overridden by OSPF intra-area routes, which have a default administrative distance of 110.


Route maps use tags to filter routes. The default tag value on static routes is
0.


Multiple routes with the same destination and the same administrative distance
comprise an Equal Cost Multi-Path (ECMP) route. The switch attempts to spread
outbound traffic equally through all ECMP route paths. EOS assigns all paths
comprising an ECMP identical tag values, and commands that change the tag value of a
path change the tag value of all paths in the ECMP.


The **no ip route** and **default ip
route** commands delete the specified static route by removing the
corresponding **ip route** command from
***running-config***. Commands that do not list a next-hop address
remove all **ip route** statements with the specified
destination from ***running-config***. If an **ip
route** statement exists for the same IP address in multiple VRFs,
each must be removed separately. Deleting a VRF deletes all static routes in a
user-defined VRF.


**Command Mode**


Global Configuration


**Command Syntax**


ip route [vrf_instance]
dest_net
next-hop
[distance][tag_varname][rt_name]


no ip route [vrf_instance]
dest_net
[next-hop][distance]


default ip route [vrf_instance]
dest_net
[next-hop][distance]


**Parameters**


- **vrf_instance** - Specifies the VRF instance to
modify.

- **no parameter** - Changes made to the default
VRF.

- **vrf**
**vrf_name** - Changes made to the specified
VRF.

- **dest_net** - Destination IPv4 subnet (CIDR or
address-mask notation).

- **next-hop** - Location or access method of next hop
device. Options include the following:

- **ipv4_addr**  -An IPv4 address.

- **null0** - Null0 interface.

- **ethernet**
**e_num** - Ethernet interface specified by
**e_num**.

- **loopback**
**l_num** - Loopback interface specified by
**l_num**.

- **management**
**m_num** - Management interface specified by
**m_num**.

- **port-channel**
**p_num** - Port-channel interface specified
by **p_num**.

- **vlan**
**v_num** - VLAN interface specified by
**v_num**.

- **VXLAN**
**vx_num** - VXLAN interface specified by
**vx_num**.

- **distance** Administrative distance assigned to the
route. Options include the following:

- **no parameter** - Route assigned default
administrative distance of one.

- **1-255** - The administrative distance
assigned to route.

- **tag_varname** - Static route tag. Options include
the following:

- **no parameter** - Assigns default static
route tag of **0**.

- **tag**
**t_value** - Static route tag value.
**t_value** ranges from
**0** to
**4294967295**.

- **rt_nameE** - Associates descriptive text to the
route. Options include the following:

- **no parameter**  - No text is associated with
the route.

- **name**
**descriptive_text** - Assign the specified
text to the route.


**Related Command**


The [ip route nexthop-group](/um-eos/eos-nexthop-groups#xx1145545) command creates
a static route that specifies a Nexthop Group to determine the Nexthop address.


**Example**


This command creates a static route in the default
VRF.
```
`switch(config)# **ip route 172.17.252.0/24 vlan 2000**
switch(config)#`
```


### ip routing


The **ip routing** command enables IPv4 routing. When enabling
IPv4 routing, the switch attempts to deliver inbound packets to destination IPv4
addresses by forwarding them to interfaces or next hop addresses specified by the
forwarding table.


The **no ip routing** and **default ip
routing** commands disable IPv4 routing by removing the
**ip routing** command from
***running-config***. When disabling IPv4
routing, the switch attempts to deliver inbound packets to their destination MAC
addresses. When this address matches the switch MAC address, EOS delivers the packet
to the CPU. EOS discards IP packets with IPv4 destinations that differ from the
switch address. The **delete-static-routes** varname removes
static entries from the routing table.


IPv4 routing is disabled by default.


**Command Mode**


Global Configuration


**Command Syntax**


ip routing [vrf_instance]


no ip routing
[delete_routes][vrf_instance


default ip routing
[delete_routes][vrf_instance]


**Parameters**

- **delete_routes** - Resolves routing table static entries
when routing is disabled.

- **no parameter** - Routing table retains
static entries.

- **delete-static-routes** - Removes static
entries from the routing table.

- **vrf_instance** - Specifies the VRF instance to
modify.

- **no parameter** -Changes made to the
default VRF.

- **vrf**
**vrf_name** - Changes made to the specified
user-defined VRF.


**Example**


This command enables IPv4
routing.
```
`switch(config)# **ip routing**
switch(config)#`
```


### ip source binding


Layer 2 Port-Channels support IP source guard (IPSG), not member ports. The IPSG
configuration on port channels supersedes the configuration on the physical member
ports. Therefore, source IP MAC binding entries should be configured on port
channels. When configured on a port channel member port, IPSG does not take effect
until you delete the port from the Port Channel configuration.


Note: IP source bindings are also used by static ARP inspection.


The **no ip source binding** and **default ip source
binding** commands exclude parameters from IPSG filtering, and
set the default for **ip source binding**.


**Command Mode**


interface-Ethernet Configuration


**Command Syntax**


ip source binding
[ip_address][mac_address]
vlan [vlan_range]
interface [interface]


no ip source binding
[ip_address][mac_address]
vlan [vlan_range]
interface [interface]


default ip source binding
[ip_address][mac_address]
vlan [vlan_range]
interface [interface]


**Parameters**

- **ip_address** - Specifies the IP ADDRESS.

- **mac_address** - Specifies the MAC ADDRESS.

- **vlan
vlan_range** - Specifies the VLAN ID range.

- **interface
interface** - Specifies the Ethernet
interface.


**Related Commands**

- ip verify source

- show ip verify source


**Example**


This command configures source IP-MAC binding entries to IP address
**10.1.1.1**, MAC address
**0000.aaaa.1111**, VLAN ID
**4094**, and **interface ethernet
36**.
```
`switch(config)# **ip source binding 10.1.1.1 0000.aaaa.1111 vlan 4094 interface
ethernet 36**
switch(config)#`
```


### ip verify source


The **ip verify source** command
configures IP source guard (IPSG) applicable only to Layer 2 ports. When configured
on Layer 3 ports, IPSG does not take effect until this interface converts to Layer
2.


Layer 2 Port-Channels support IPSG, not member ports. The IPSG
configuration on port channels supersedes the configuration on the physical member
ports. Therefore, source IP MAC binding entries should be configured on port
channels. When configured on a port channel member port, IPSG does not take effect
until you delete the port from the Port Channel configuration.


The
**no ip verify source** and **default ip
verify source** commands exclude VLAN IDs from IPSG filtering,
and set the default for **ip verify
source**.


**Command Mode**


Interface-Ethernet
Configuration


**Command Syntax**


ip verify source vlan
[vlan_range]


no ip verify source
[vlan_range]


default ip verify
source


**Parameters**


**vlan_range**
- Specifies the VLAN ID range.

**Related Commands**

- ip source binding

- show ip verify source


**Example**

This command excludes VLAN IDs
**1** through **3** from IPSG
filtering. When enabled on a trunk port, IPSG filters the inbound IP packets on all
allowed VLANs. IP packets received on VLANs **4** through
**10** on **Ethernet 36** filter
by IPSG, while permitting those received on VLANs **1**
through
**3**.
```
`switch(config)# **no ip verify source vlan 1-3**
switch(config)# **interface ethernet 36**
switch(config-if-Et36)# **switchport mode trunk**
switch(config-if-Et36)# **switchport trunk allowed vlan 1-10**
switch(config-if-Et36)# **ip verify source**
switch(config-if-Et36)#`
```


### ip verify


The **ip verify** command configures Unicast Reverse Path
Forwarding (uRPF) for inbound IPv4 packets on the configuration mode interface. uRPF
verifies the accessibility of source IP addresses in packets that the switch
forwards.


uRPF defines two operational modes: strict mode and loose mode.

- **Strict mode** - uRPF verifies that a packetreceived on the interface
with the routing table entry specifies for its return packet.

- **Loose mode** - uRPF validation does not consider the inbound packet’s
ingress interface only if a valid return path exists.


The **no ip verify** and **default ip
verify** commands disable uRPF on the configuration mode
interface by deleting the corresponding **ip verify** command
from ***running-config***.


**Command Mode**


Interface-Ethernet Configuration


Interface-Loopback Configuration


Interface-Management Configuration


Interface-Port-Channel Configuration


Interface-VLAN Configuration


**Command Syntax**


ip verify unicast source reachable-via
rpf_mode


no ip verify unicast


default ip verify unicast


**Parameters**


**rpf_mode** - Specifies the uRPF mode. Options include:

- **any** - Loose mode.

- **rx** - Strict mode.

- **rx allow-default** - Strict mode. All inbound
packets forward if a default route is defined.


**Guidelines**


The first IPv4 uRPF implementation briefly disrupts IPv4 unicast routing. Subsequent
**ip verify** commands on any interface do not disrupt
IPv4 routing.


**Examples**

- This command enables uRPF loose mode on **VLAN interface
17**.
```
`switch(config)# **interface vlan 17**
switch(config-if-Vl17)# **ip verify unicast source reachable-via any**
switch(config-if-Vl17)# **show active**
 interface Vlan17
   ip verify unicast source reachable-via any
switch(config-if-Vl17)#`
```

- This command enables uRPF strict mode on **VLAN interface
18**.
```
`switch(config)# **interface vlan 18**
switch(config-if-Vl18)# **ip verify unicast source reachable-via rx**
switch(config-if-Vl18)# **show active**
 interface Vlan18
   ip verify unicast source reachable-via rx
switch(config-if-Vl18)#`
```


### ipv4 routable 240.0.0.0/4


The **ipv4 routable 240.0.0.0/4** command assignes an class E
addresses to an interface. When configured, the class E address traffic are routed
through BGP, OSPF, ISIS, RIP, static routes and programmed to the FIB and kernel. By
default, this command is disabled.


The **no ipv4 routable 240.0.0.0/4** and **default
ipv4 routable 240.0.0.0/4** commands disable IPv4 Class E
routing by removing the **ipv4 routable 240.0.0.0/4** command
from ***running-config***.


IPv4 routable **240.0.0.0/4** routing is disabled by
default.


**Command Mode**


Router General Configuration


**Command Syntax**


ipv4 routable 240.0.0.0/4


no ipv4 routable 240.0.0.0/4


default ipv4 routable 240.0.0.0/4


**Example**


These commands configure an IPv4 Class E (**240/4**) address to
an interface.
```
`switch(config)# **router general**
switch(config-router-general)# **ipv4 routable 240.0.0.0/4**`
```


### load-balance cluster


The **load-balance cluster** command enters the Cluster Load Balancing (CLB) Configuration Mode
and configure parameters for cluster load-balancing on a network. The **no** version of the command
removes the configuration from the ***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


**load-balance cluster**


**no load-balance cluster**


**Parameters**


- **load-balance cluster** - Enters the Cluster Load Balancing (CLB) Configuration Mode.


**Example**


Use the following command to enter the Cluster Load Balancing (CLB) Configuration Mode:


```
`switch(config)# **load-balance cluster**
switch(config-clb)#`
```


### load-balance method


The **load-balance** command in the Cluster Load Balancing
Configuration Mode configures the method of load-balancing traffic on the cluster.
Currently, EOS supports Round-Robin and Spine types of load balancing.


The **no** version of the command deletes the configuration from the ***running-config***.


**Command Mode**


Cluster Load Balancing Configuration


**Command Syntax**


**load-balance method [flow round-robin] [spine port-index]**


**no load-balance method [flow round-robin] [spine
port-index]**


**Parameters**


- **load-balance method flow round-robin** - Specify the load-balancing method as round-robin for flows.

- **load-balance method spine port-index** - Specify the load-balancing method as port index for spines.


**Examples**


Use the following commands to configure round-robin as the load-balancing flow method:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **load-balance method flow round-robin**
switch(config-clb)#`
```


Use the following commands to configure port-index as the load-balancing spine method:


```
`switch(config)# **load-balance cluster**
            switch(config-clb)# **load-balance method spine port-index**
            switch(config-clb)#`
```


### member Ethernet


The **member Ethernet** command in the Port Group Host Configuration Mode configures per port hardware interfaces for cluster load balancing on the switch.


The **no** version of the command deletes the configuration from the ***running-config***.


**Command Mode**


Cluster Load Balancing Configuration


Port Group Host Configuration


**Command Syntax**


**member Ethernet interface_number**


**no member Ethernet interface_number**


**Parameters**


- **member Ethernet interface_number** - Configure the Ethernet hardware interface number from 1 to 46 per port group.


**Example**


Add Ethernet 1 hardware interface to MyPortGroup:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **port group host MyPortGroup**
switch(config-clb-port-host-MyPortGroup)# **member Ethernet 1**`
```




### platform barefoot bfrt vrf


The **platform barefoot bfrt vrf** command configures the
forwarding plane agent on supported platforms to restart and listen on the
configured VRF for connections. If left unconfigured, the switch uses the default
VRF for the IP and port for the BfRuntime server.


**Command Mode**


Global Configuration


**Command Syntax**


platform barefoot bfrt vrf
vrf_name


**Parameter**


**VRF name** - Specify the name for the configured
VRFconnections.


**Example**


These commands configure the forwarding plane agent to restart and listen on the
configured VRF for
connections.
```
`switch(config)# **vrf instance management**
switch(config-vrf-management)# **exit**
switch(config)# **platform barefoot bfrt 0.0.0.0 50052**
switch(config)# **platform barefoot bfrt vrf <VRF name>**
switch(config)# **int management1**
switch(config-if-Ma1)# **vrf management**`
```


### platform trident forwarding-table
partition


The **platform trident forwarding-table partition** command
provides a shared table memory for L2, L3 and algorithmic LPM entries that can be
partitioned in different ways.


Instead of fixed-size tables for L2 MAC entry tables, L3 IP forwarding tables, and
Longest Prefix Match (LPM) routes, the tables can be unified into a single shareable
forwarding table.


Note: Changing the Unified Forwarding Table mode causes the forwarding agent to restart,
briefly disrupting traffic forwarding on all ports.


The **no platform trident forwarding-table partition** and
**default platform trident forwarding-table
partition** commands remove the  **platform trident
forwarding-table partition** command from
***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


platform trident forwarding-table partition
size


no platform trident forwarding-table partition


default platform trident forwarding-table partition


**Parameters**


**size**       Size of partition. Options include the
following:

- **0**      288k l2 entries, 16k host entries, 16k lpm
entries.

- **1**      224k l2 entries, 80k host entries, 16k lpm
entries.

- **2**      160k l2 entries, 144k host entries, 16k lpm
entries.

- **3**      96k l2 entries, 208k host entries, 16k lpm
entries.


The default value is **2** (160k l2 entries, 144k host entries,
16k lpm entries).


**Examples**

- This command sets the single shareable forwarding table to option 2 that
supports 160k L2 entries, 144k host entries, and 16k LPM
entries.
```
`switch(config)# **platform trident forwarding-table partition 2**
switch(config)`
```

- This command sets the single shareable forwarding table to option 3 that
supports 96k L2 entries, 208k host entries, and 16k LPM entries. Since the
switch was previously configured to option 2, you’ll see a warning notice
before the changes are
implemented.
```
`switch(config)# **platform trident forwarding-table partition 3**

Warning: StrataAgent will restart immediately`
```


### platform trident routing-table
partition


The **platform trident routing-table partition** command
manages the partition sizes for the hardware LPM table that stores IPv6 routes of
varying sizes.


An IPv6 route of length /64 (or shorter) requires half the hardware resources of an
IPv6 route longer than /64. The switch installs routes of varying lengths in
different table partitions. This command specifies the size of these partitions to
optimize table usage.


Note: Changing the routing table partition mode causes the forwarding agent to restart,
briefly disrupting traffic forwarding on all ports.


The **no platform trident routing-table partition** and
**default platform trident routing-table partition**
commands restore the default partitions sizes by removing the **platform
trident routing-table partition** command from
***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


platform trident routing-table partition
size


no platform trident routing-table partition


default platform trident routing-table partition


**Parameters**


**size**      Size of partition. Options include the
following:

- **1**      16k IPv4 entries, 6k IPv6 (/64 and smaller)
entries, 1k IPv6 (any prefix length).

- **2**      16k IPv4 entries, 4k IPv6 (/64 and smaller)
entries, 2k IPv6 (any prefix length).

- **3**      16k IPv4 entries, 2k IPv6 (/64 and smaller)
entries, 3k IPv6 (any prefix length).
The default value is
**2** (16k IPv4 entries, 4k IPv6 (/64 and
smaller) entries, 2k IPv6 (any prefix length).


**Restrictions**


Partition allocation cannot be changed from the default setting when enabling uRPF
for IPv6 traffic.


**Example**


This command sets the shareable routing table to option **1**
that supports **6K** prefixes equal to or shorter than
**/64** and **1K** prefixes
longer than
**/64**.
```
`switch(config)# **platform trident routing-table partition 1**
switch(config)`
```


### port group host


The **port group host** command enters the Port Group Host Configuration mode and configures additional port parameters for Cluster Load Balancing by identifying the ports
connected to the GPU server.


The **no** version of the command deletes the configuration from the ***running-config***.


**Command Mode**


Cluster Load Balancing Configuration


Port Host Group Configuration


**Command Syntax**


**port group host word**


**no port group host word**


**Parameters**


- **port group host word** - Specify a name for the port group host.


**Example**


Use the following commands to create a port group host, MyPortGroup, and enter Port Host Configuration Mode:


```
`switch(config)# **load-balance cluster**
switch(config-clb)# **port host group MyPortGroup**
switch(config-clb-port-host-MyPortGroup)#`
```


### rib fib policy


The **rib fib policy** command enables FIB policy for a
particular VRF under router general configuration mode. The FIB policy can be
configured to advertise only specific RIB routes and exclude all other routes.


For example, a FIB policy can be configured that does not place routes associated
with a specific origin in the routing table. These routes do not forward data
packets and these routes do not advertise by the routing protocol to neighbors.


The **no rib fib policy** and **default rib fib
policy** commands restore the switch to its default state by
removing the corresponding rib fib policy command from
***running-config***.


**Command Mode**


Router General Configuration


**Command Syntax**


rib [ipv4 | ipv6]
fib policy
name


no rib [ipv4 | ipv6]
fib policy
name


default rib [ipv4 | ipv6]
fib policy
name


**Parameters**

- **ipv4** - IPv4 configuration commands.

- **ipv6** - IPv6 configuration commands.

- **name** - Route map name.


**Example**


The following example enables FIB policy for IPv4 in the default VRF, using the route
map,
**map1**.
```
`Switch(config)# **router general**
Switch(config-router-general)# **vrf default**
Switch(config-router-general-vrf-default)# **rib ipv4 fib policy map1**`
```


### show arp


The **show arp** command displays all ARP tables. This command
differs from the show ip arp command in that it shows MAC
bindings for all protocols, whereas show ip arp only displays
MAC address – IP address bindings. Addresses display with their host name by
including the ***resolve*** argument.


**Command Mode**


EXEC


**Command Syntax**


show arp
[vrf_inst][format][host_addr][host_name][intf][mac_addr][data]


**Parameters**


The **vrf_inst** and **format**
parameters are always listed first and second. The **data**
parameter is always listed last. All other parameters can be placed in any order.

- **vrf_inst** - Specifies the VRF instance to display
data.

- **no parameter** - Context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF instance.
System default VRF is specified by
**default**.

- **format** - Displays format of host address. Options
include the following:

- **no parameter** - Entries associate hardware address with an
IPv4 address.

- **resolve** - Enter associate hardware address
with a host name (if it exists).

- **host_addr** -  IPv4 address to filter routing table
entries. Options include the following:

- **no parameter** - Routing table entries not filtered by host
address.

- **ipv4_addr** - Table entries matching
specified IPv4 address.

- **host_name** - Host name to filter routing table
entries. Options include the following:

- **no parameter** - Routing table entries not filtered by host
name.

- **host**
**hostname** - Entries matching
**hostname** (text).

- **intf** - Interfaces for which command displays
status.

- **no parameter** - Routing table entries not filtered by
interface.

- **interface ethernet**
**e_num** - Routed Ethernet interface
specified by **e_num**.

- **interface loopback**
**l_num** - Routed loopback interface
specified by **l_num**.

- **interface management**
**m_num** - Routed management interface
specified by **m_num**.

- **interface port-channel**
**p_num** - Routed port channel Interface
specified by **p_num**.

- **interface vlan**
**v_num** - VLAN interface specified by
**v_num**.

- **interface VXLAN**
**vx_num** - VXLAN interface specified by
**vx_num**.

- **mac_addr** - MAC address to filter routing table
entries. Options include the following:

- **no parameter** - Routing table entries not filtered by
interface MAC address.

- **mac_address**
**mac_address** - Entries matching
**mac_address** (dotted hex notation –
H.H.H).

- **data** - Detail of information provided by command.
Options include the following:

- **no parameter** - Routing table entries.

- **summary** - Summary of ARP table
entries.

- **summary total** - Number of ARP table entries.


**Related Commands**


The cli vrf command specifies the context-active VRF.


**Example**


This command displays the ARP
table.
```
`switch> **show arp**
Address         Age (min)  Hardware Addr   Interface
172.22.30.1             0  001c.730b.1d15  Management1
172.22.30.133           0  001c.7304.3906  Management1
switch>`
```


### show arp agent


The **show arp agent** command displays the aggregate of all ARP entries that the CLI and other switch
agents requested the ARP agent to install in EOS.


**Command Mode**


EXEC


**Command Syntax**


show arp agent[ipv4 | ipv6]
[cache | dynamic | capacity
| [interface
interface]


**Parameters**


- **[ipv4 | ipv6]** - Display details about
IPv4 or IPv6 parameters.

- **cache** - Display neighbor cache information.

- **dynamic** - Display the capacity of the dynamic neighbor
resolutions.

- **capacity** - Display the configured capacity of address
resolutions.

- **interface
interface** - Specify the interface to display ARP
agent details.


**Examples**


Use the following command to display IPv4 ARP agent details for Ethernet interface
1:
```
`switch# **show arp agent ipv4 cache dynamic capacity interface ethernet 1 summary**
Ethernet1
  Cache Entry Kind: dynamic
  Capacity: 100
  Entries: 5`
```


Use the following command to display IPv6 ARP agent details for Ethernet interface
1:
```
`switch# **show arp agent ipv6 cache dynamic capacity interface ethernet 1 summary**
Ethernet1
  Link-local excluded
  Cache Entry Kind: dynamic
  Capacity: 250
  Entries: 5`
```


Executing the command without the **summary** parameter displays
the list of addresses tracked towards
capacity:
```
`switch# **show arp agent ipv4 cache dynamic capacity interface ethernet 1**
Ethernet1
  Cache Entry Kind: dynamic
  Capacity: 100
  Entries: 5
  10.0.0.1
  10.0.0.2
  10.0.0.3
  10.0.0.4
  10.0.0.5`
```


```
`switch# **show arp agent ipv6 cache dynamic capacity interface ethernet 1**
  Ethernet1
  Link-local excluded
  Cache Entry Kind: dynamic
  Capacity: 250
  Entries: 5
  1::1
  1::2
  1::3
  1::4
  1::5`
```


### show dhcp server


Use the **show dhcp server** command to display DHCP server information.


**Command Mode**


EXEC


**Command Syntax**



show dhcp server [ipv4 | ipv6 |
leases | vrf]


**Parameters**

- **ipv4** Displays details related to IPv4.

- **ipv6** Displays details related to IPv6.

- **leases** Displays active leases.

- **A.B.C.D/E** IPv4 subnet.

- **NAME** Subnet name.



**Examples**

- The following output displays DHCPv4.



```
`switch# **show dhcp server ipv4**
IPv4 DHCP Server is active
Debug log is enabled
DNS server(s): 10.2.2.2
DNS domain name: mydomain
Lease duration: 1 days 0 hours 0 minutes
TFTP server:
myserver (Option 66)
10.0.0.3 (Option 150)
TFTP file: fileFoo
Active Leases: 1
IPv4 DHCP interface status:
   Interface   Status
-------------------------------------------------
   Ethernet1   Inactive (Could not determine VRF)
   Ethernet2   Inactive (Not in default VRF)
   Ethernet3   Inactive (Kernel interface not created yet)
   Ethernet4   Inactive (Not up)
   Ethernet5   Inactive (No IP address)
   Ethernet6   Active

Vendor information:
Vendor ID: default
  Sub-options         Data
---------------- ----------------
      1          192.0.2.0, 192.0.2.1

Vendor ID: vendorFoo
  Sub-options       Data
---------------- -----------
      2            192.0.2.2
      3            “data”

Subnet: 10.0.0.0/8
Subnet name: subnetFoo
Range: 10.0.0.1 to 10.0.0.10
DNS server(s): 10.1.1.1 10.2.2.2
Lease duration: 3 days 3 hours 3 minutes
Default gateway address: 10.0.0.3
TFTP server:
subnetServerFoo (Option 66)
10.0.0.4 (Option 150)
TFTP boot file: subnetFiletftp
Active leases: 1
Reservations:
MAC address: 1a1b.1c1d.1e1f
IPv4 address: 10.0.0.1

MAC address: 2a2b.2c2d.2e2f
IPv4 address: 10.0.0.2`
```

- In this example, DHCPv6 is configured with subnet
 **fe80::/10** while being enabled on
**Ethernet1** with address
**fe80::1/64** and on
 **Ethernet3** with address
**fe80::2/64**.
```
`switch# **show dhcp server ipv6**
IPv6 DHCP server is active
Debug log is enabled
DNS server(s): fe80::6
DNS domain name: testaristanetworks.com
Lease duration: 1 days 3 hours 30 minutes
Active leases: 0
IPv6 DHCP interface status:
   Interface    Status
--------------- ------
   Ethernet1    Active
   Ethernet3    Active

Subnet: fe80::/10
Subnet name: foo
Range: fe80::1 to fe80::3
DNS server(s): fe80::4 fe80::5
Direct: Inactive (Multiple interfaces match this subnet: Ethernet1 Ethernet3)
Relay: Active
Active leases: 0`
```

- This example illustrates when multiple subnets match an interface. In this example,
 DHCPv6 is configured with subnets **fc00::/7** and
**fe80::/10** while being enabled on **Ethernet1** with
 address **fe80::1/10** and
 **fc00::1/7**.
```
`switch# **show dhcp server ipv6**
IPv6 DHCP server is active
DNS server(s):  fc00::2
DNS domain name: testaristanetworks.com
Lease duration: 1 days 3 hours 30 minutes
Active leases: 0
IPv6 DHCP interface status:
   Interface    Status
--------------- ------
   Ethernet1    Active

Subnet: fc00::/7
Subnet name: data
Range: fc00::1 to fc00::5
DNS server(s): fc00::6 fc00::8
Direct: Inactive (This and other subnets match interface Ethernet1)
Relay: Active

Active leases: 0

Subnet: fe80::/10
Subnet name: bar
Direct: Inactive (This and other subnets match interface Ethernet1)
Relay: Active

Active leases: 0`
```

- After disabling a subnet, the **show dhcp server** command
 displays the disable message with a reason. The number of active leases of the
 disabled subnets displays as **0**. In this example, there are
 overlapping subnets.
```
`switch# **show dhcp server**
IPv4 DHCP Server is active
DNS server(s): 10.2.2.2
Lease duration: 1 days 0 hours 0 minutes
Active Leases: 0
IPv4 DHCP interface status:
   Interface   Status
-------------------------------------------------
   Ethernet1   Active

Subnet: 10.0.0.0/24 (Subnet is disabled - overlapping subnet 10.0.0.0/8)
Range: 10.0.0.1 to 10.0.0.10
DNS server(s): 10.3.3.3 10.4.4.4
Default gateway address: 10.0.0.4
Active leases: 0

Subnet: 10.0.0.0/8 (Subnet is disabled - overlapping subnet 10.0.0.0/24)
DNS server(s):
Default gateway address: 10.0.0.3
Active leases: 0`
```

- In this example, the display output shows overlapping
 ranges.
```
`switch# **show dhcp server**
IPv4 DHCP Server is active
DNS server(s): 10.2.2.2
Lease duration: 1 days 0 hours 0 minutes
Active Leases: 0
IPv4 DHCP interface status:
   Interface   Status
-------------------------------------------------
   Ethernet1   Active

Subnet: 10.0.0.0/8 (Subnet is disabled - range 10.0.0.9-10.0.0.12 overlaps with an existing pool)
Range: 10.0.0.1 to 10.0.0.10
Range: 10.0.0.9 to 10.0.0.12
DNS server(s): 10.3.3.3 10.4.4.4
Default gateway address: 10.0.0.4
Active leases: 0`
```

- This example displays duplicate static IP address
 reservation.
```
`Subnet: 10.0.0.0/8 (Subnet is disabled - ipv4-address 10.0.0.11 is reserved more than once)
Subnet name:
DNS server(s):
Default gateway address: 10.0.0.3
Active leases: 0
Reservations:
MAC address: 1a1b.1c1d.1e1f
IPv4 address: 10.0.0.11

MAC address: 2a2b.2c2d.2e2f
IPv4 address: 10.0.0.11`
```

- Use the **show dhcp server leases** command to display
 detailed information about the IP addresses allocated by the DHCP Server (including
 the IP address, the expected end time for that address, the time when the address is
 handed out, and the equivalent MAC
 address).
```
`switch# **show dhcp server leases**
10.0.0.10
End: 2019/06/20 17:44:34 UTC
Last transaction: 2019/06/19 17:44:34 UTC
MAC address: 5692.4c67.460a

2000:0:0:40::b
End: 2019/06/20 18:06:33 UTC
Last transaction: 2019/06/20 14:36:33 UTC
MAC address: 165a.a86d.ffac`
```




### show dhcp server leases


Use the **show dhcp server leases** command to display DHCP server lease information.


**Command Mode**


EXEC


**Command Syntax**



**show dhcp server leases [ipv4 | ipv6**]


**Parameters**

- **ipv4** - Displays details related to IPv4.

- **ipv6** - Displays details related to IPv6.


**Example**


Use the **show dhcp server leases** command to display detailed
information about the IP addresses allocated by the DHCP Server including the IP
address, the expected end time for that address, the time when assigning the address,
and the equivalent MAC
address.
```
`switch# **show dhcp server leases**
10.0.0.10
End: 2019/06/20 17:44:34 UTC
Last transaction: 2019/06/19 17:44:34 UTC
MAC address: 5692.4c67.460a

2000:0:0:40::b
End: 2019/06/20 18:06:33 UTC
Last transaction: 2019/06/20 14:36:33 UTC
MAC address: 165a.a86d.ffac`
```


### show hardware capacity


The **show hardware capacity** command displays the utilization
of the hardware resources:


**Command Mode**


Privileged EXEC


**Command Syntax**


**show hardware capacity**


**Example**


The following command is used to show the utilization of the hardware resources:

```
`switch# **show hardware capacity**
Forwarding Resources Usage

Table   Feature         Chip    Used	Used    Free	Committed    Best Case  High
                                Entries   (%)      Entries    Entries      Max        Watermark
                                                                                      Entries
------ --------------- ------- ---------- ------- ---------- ------------ ----------- ---------
ECMP                              0  	0%      4095       0     	4095        0
ECMP     Mpls                     0  	0%      4095       0     	4095        0
ECMP     Routing                  0  	0%      4095       0     	4095        0
ECMP     VXLANOverlay             0  	0%      4095       0     	4095        0
ECMP     VXLANTunnel              0  	0%      3891       0     	3891        0`
```


### show hardware resource DlbEcmpGroupTable agent *


The following platforms use the **show hardware resource DlbEcmpGroupTable agent *** command:


- DCS-7050CX4

- DCS-7050DX4-32S-F

- DCS-7050PX4-32S-F

- DCS-7050SDX4

- DCS-7050SPX4

- 7358X4-SC


**Command Mode**


Privileged EXEC


**Command Syntax**


show hardware resource DlbEcmpGroupTable agent *


**Example**


Use the following command to display information about DLB and ECMP
groups:
```
`switch# **show hardware resource DlbEcmpGroupTable agent ***
Resource: bcm56881_b0::Common::DlbEcmpGroupTable
Feature agent: StrataL3Unicast
Unit id: 511
View: entry
eId      OC   flowBase     flowSize    memPtr  inDur   member0Port    member0PortValid   ...
---     ---   --------     --------    —----  —---   —----------    —---------------    ...
  2       1        512            1        2     50            11                   1    ...`
```


### show hardware resource l3 summary


The **show hardware resource l3 summary** command displays a summary of used hardware entries and the total available capacity for Layer 3
features such as next-hops and ECMP groups. The command allows assessing the health of the forwarding plane and determining if the switch approaches resource limits.


**Command Mode**


Privileged EXEC


**Command Syntax**


**show hardware resource l3 summary**




**Example**


Enter the command to display the following information:


```
`(config)# **show hardware resource l3 summary**
Source lookup : disabled
Adjacency sharing : disabled
Route deletion delay : 0.0 seconds

L3 interfaces : 1/4096

Nexthops : 59/32768
Overlay nexthops : 50/24576
Underlay nexthops : 9/24576
Shared Overlay and Underlay nexthop tables : True
Tunnel Nexthops : 0/8192

Overlay ECMP groups : 0/4096
Overlay ECMP members : 0/65536
Underlay ECMP groups : 0/4096
Underlay ECMP members : 0/65536
Shared Overlay and Underlay ECMP member tables : True
Tunnel ECMP groups : 0/4096
Tunnel ECMP members : 0/8192

IPv4 routes : 67
IPv6 routes : 44
IPv4 unprogrammed routes : 0
IPv6 unprogrammed routes : 0
IPv4 multicast(*, G) routes : 0/32768
IPv6 multicast(*, G) routes : 0/32768
IPv4 multicast(S, G) routes : 0/32768
IPv6 multicast(S, G) routes : 0/16384

ALPM mode : 3-Level
Memory format : narrow mode
TCAM usage : 5/2304
Level-2 cells : 2/6144
Level-2 buckets : 1/1024
Level-2 mem geometry : 1024 (buckets), 6 (banks)
Level-3 cells : 23/65536
Level-3 buckets : 5/8192
Level-3 mem geometry : 8192 (buckets), 8 (banks)
Pivots : 2 (ipv4 : 1, ipv6 : 1)
Subpivots : 5 (ipv4 : 2, ipv6 : 3)
ALPM routes : 111 (ipv4 : 67, ipv6 : 44)

Multicast replication groups : 6/16384
Repl head entries : 0/147456
Repl list entries : 0/147456

Mystation TCAM entries : 1/128

Virtual ports : 2/8192`
```


Table 4. Display Output

| Field Name
| Description
|


| **Source lookup**
| Unicast Reverse Path Forwarding (uRPF) enabled or disabled.
|


| **Adjacency sharing**
| Enabled or disabled.
|


| **Route deletion delay**
| Indicates, in *seconds*, the delay of route deletion.
|


| **L3 interfaces x/n**
| x indicates the number of configured L3 ports.
n indicates the number of possible L3 ports.
|


| **Nexthops x/n**
| x indicates the total number of next-hops.
n indicates the maximum number of possible next-hops.
|


| **Overlay nexthops x/n**
| x indicates the number of L3 next-hops plus
VXLAN overlay next-hops.
n indicates the
maximum number of L3 next-hops plus VXLAN overlay next-hops.


x indicates the number of L3 next-hops.*


n indicates the maximum number of L3
next-hops.*
|


| **Underlay nexthops x/n**
| x indicates the number of VXLAN underlay
next-hops plus HER next-hops plus underlay multicast routing
next-hops.
n indicates the maximum
number of L3 next-hops plus VXLAN overlay next-hops.


x indicates the number of VXLAN underlay
next-hops plus HER next-hops.*


n indicates the maximum number of VXLAN underlay
next-hops.*
|


| **Shared Overlay and Underlay nexthop tables**
| **False** or
**True***
|


| **Tunnel Nexthops x/n**
| Not applicable
x indicates the number of
VXLAN underlay next-hops plus HER next-hops.*


n indicates the maximum possible VXLAN overlay
next-hops.*
|


| **Overlay ECMP groups x/n**
| x indicates the number of VXLAN overlay ECMP
groups.
n indicates the maximum
possible VXLAN overlay groups.


x indicates the number of L3 routing ECMP
groups.*


n indicates the maximum possible number of L3
routing ECMP groups.*
|


| **Overlay ECMP members x/n**
| x indicates the number of VXLAN overlay ECMP
groups.
n indicates the maximum
possible VXLAN overlay members.


x indicates the number of normal L3 ECMP
groups.*


n indicates the maximum
possible number of L3 ECMP members.*
|


| **Underlay ECMP groups x/n**
| x indicates the number of VXLAN underlay ECMP
groups plus L3 routing ECMP groups.
n indicates
the maximum possible of combined groups.


x indicates the number of VXLAN underlay ECMP
groups.*


n indicates the maximum possible number of VXLAN
underlay ECMP groups.*
|


| **Underlay ECMP members x/n**
| x indicates the number of VXLAN underlay ECMP
groups plus L3 routing ECMP members.
n
indicates the maximum possible number of combined members.


x indicates the number of VXLAN underlay ECMP
groups.*


n indicates the maximum possible number
of VXLAN underlay ECMP members.*
|


| **Shared Overlay and Underlay ECMP member tables**
| Always True or Always False*.
|


| **Tunnel ECMP groups : x/n**
| Not Applicable
x indicates the number of
VXLAN overlay ECMP groups.*


n indicates the maximum possible number of VXLAN
underlay ECMP groups.*
|


| **Tunnel ECMP members : x/n**
| Not Applicable
x indicates the number of
VXLAN overlay ECMP members.*


n indicates the maximum possible number of VXLAN
underlay ECMP members.*
|


| **IPv4 routes**
| Indicates the number of programmed IPv4 routes.
|


| **IPv6 routes**
| Indicates the number of programmed IPv6 routes.
|


| **IPv4 unprogrammed routes**
| Indicates the number of unprogrammed IPv4 routes.
|


| **IPv6 unprogrammed routes**
| Indicates the number of unprogrammed IPv6 routes.
|


| **Host table usage : x/n**
| x indicates the number of host table entries
used.
n indicates the total number of
host table entries used.

 Not Applicable*
|


| **IPv4 unicast routes : x/n**
| x indicates the number of unicast IPv4 routes.

n indicates the total number of
possible IPv4 routes.

 Not Applicable*
|


| **IPv6 unicast routes : x/n**
| x indicates the number of unicast IPv6 routes.

n indicates the total number of
possible IPv6 routes.

 Not Applicable*
|


| **IPv4 multicast(*, G) routes : x/n**
| x indicates the number of IPv4 multicast
routes from any source to multicast group.
n
indicates the maximum number of possible IPv4 multicast routes
from any source to multicast group.


Not
Applicable*
|


| **IPv6 multicast(*, G) routes : x/n**
| x indicates the number of IPv6 multicast
routes from any source to multicast group.
n
indicates the maximum number of possible IPv6 multicast routes
from any source to multicast group.

 Not Applicable*
|


| **IPv4 multicast(S, G) routes : x/n**
| x indicates the number of IPv4 multicast
routes from a source IP to a multicast group.
n
indicates the maximum number of IPv4 multicast routes from a
source IP to a multicast group.

 Not Applicable*
|


| **IPv6 multicast(S, G) routes : x/n**
| x indicates the number of IPv6 multicast
routes from a source IP to a multicast group.
n
indicates the maximum number of IPv6 multicast routes from a
source IP to a multicast group.

 Not Applicable*
|


| **Memory format**
| Narrow or wide mode.
|


| **TCAM usage : x/n**
| x indicates the number of TCAM entries on the switch.

n indicates the maximum number of programmable TCAM entries on the switch.
|


| **Level-2 cells** : x/n**
| x indicates the number of cells used on the switch.

n indicates the total number of cells in the ALPM level 2 table on the switch.
|


| **Level-2 buckets** : x/n**
| x indicates the number of buckets used on the switch.

n indicates the total number of buckets in the ALPM level 2 table on the switch.
|


| **Level-2 mem geometry x(buckets),n(banks)**
| Indicates the number of buckets and banks on the switch.
|


| **Level-3 cells** : x/n**
| x indicates the number of cells used on the switch.

n indicates the total number of cells in the ALPM level 3 table on the switch.
|


| **Level-3 buckets** : x/n**
| x indicates the number of buckets used on the switch.

n indicates the total number of buckets in the ALPM level 3 table on the switch.
|


| **Level-3 mem geometry x(buckets),n(banks)**
| x indicates the number of Level 3 buckets used.

n indicates the number of Level 3 banks used.
|


| **Pivots :  n (ipv4 : x , ipv6 : y)**
| n indicates the number of pivots in the APLM
tree.
x indicates the number of IPv4
pivots.


y indicates the number of IPv6 pivots.
|


| **Subpivots : n (ipv4 : x , ipv6 : y)**>
| n indicates the number of subpivots in the
APLM tree.
x indicates the number of IPv4
subpivots.


y indicates the number of
IPv6 subpivots.
|


| **ALPM routes : n (ipv4 : x , ipv6 : y)**
| n indicates the number of APLM routes.

x indicates the number of IPv4 APLM
routes.


y indicates the number of IPv6 APLM
routes.
|


| **Multicast replication groups : x/n**
| x indicates the number of multicast
replication groups programmed, includes L3MC, L2MC
group.
n indicates the total number of
multicast replication groups programmed, includes L3MC, L2MC
group.

 Not applicable*
|


| **Repl head entries : x/n**
| x indicates the number of Repl head entries
programmed.
n indicates the total
number of Repl head entries programmed.

 Not
applicable*
|


| **Repl list entries : x/n**
| x indicates the number of Repl list entries
programmed.
n indicates the total number of
Repl list entries programmed.


Not applicable*
|


| **Mystation TCAM entries : x/n**
| x indicates the number of Mystation TCAM entries programmed.

n indicates the total number of Mystation TCAM entries programmed.
|


| **Virtual ports : x/n**
| x indicates the number of virtual ports.

n indicates the maximum possible number of virtual ports.
|


*****Applies to the following platforms:




 - DCS-7060X6-32PE-F

 - DCS-7060X6-32PE-N

 - DCS-7060X6-64PE-F




### show interface tunnel


The **show interface tunnel** command displays the interface
tunnel information.


**Command Mode**


EXEC


**Command Syntax**


show interface tunnel
number


**Parameter**


**number** - Specifies the tunnel interface number.


**Example**


This command displays tunnel interface configuration information for tunnel interface
**10**.
```
`switch# **show interface tunnel 10**

Tunnel10 is up, line protocol is up (connected)
 Hardware is Tunnel, address is 0a01.0101.0800
 Internet address is 192.168.1.1/24
 Broadcast address is 255.255.255.255
 Tunnel source 10.1.1.1, destination 10.1.1.2
 Tunnel protocol/transport GRE/IP
   Key disabled, sequencing disabled
   Checksumming of packets disabled
 Tunnel TTL 10, Hardware forwarding enabled
 Tunnel TOS 10
 Path MTU Discovery
 Tunnel transport MTU 1476 bytes
 Up 3 seconds`
```


### show ip


The **show ip** command displays IPv4 routing, IPv6 routing,
IPv4 multicast routing, and VRRP status on the switch.


**Command Mode**


EXEC


**Command Syntax**


show ip


**Example**


This command displays IPv4 routing
status.
```
`switch> **show ip**

IP Routing : Enabled
IP Multicast Routing : Disabled
VRRP: Configured on 0 interfaces

IPv6 Unicast Routing : Enabled
IPv6 ECMP Route support : False
IPv6 ECMP Route nexthop index: 5
IPv6 ECMP Route num prefix bits for nexthop index: 10

switch>`
```


### show ip arp


The **show ip arp** command displays ARP cache entries that map
an IPv4 address to a corresponding MAC address. The table displays addresses by the
host names when the command includes the ***resolve***
argument.


**Command Mode**


EXEC


**Command Syntax**


show ip arp
[vrf_inst][format][host_addr][host_name][intf][mac_addr][data]


**Parameters**


The **vrf_inst** and **format**
parameters list first and second. The **data** parameter lists
last. All other parameters can be placed in any order.

- **vrf_inst** - Specifies the VRF instance to display
data.

- **no parameter** - Specifies the Context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF instance.
Specifies the system default VRF
**default**.

- **format** - Displays format of host address. The
options include the following:

- **no parameter** - Displays entries associated hardware address
with an IPv4 address.

- **resolve** - Displays the specific associated
hardware address with a host name (if it exists).

- **host_addrR** - Specifies the IPv4 address to filter
routing table entries. The options include the following:

- **no parameter** - Routing table entries not filtered by host
address.

- **ipv4_addr**   - Table entries matching
specified IPv4 address.

- **host_name** - Host name by to filter routing table
entries. The options include the following:

- **no parameter** - Routing table entries not filtered by host
name.

- **host**
**hostname** - Entries with matching
**hostname** (text).

- **interface_name** - Interfaces to display status.

- **no parameter** - Routing table entries not filtered by
interface.

- **interface ethernet**
**e_num** - Routed Ethernet interface
specified by **e_num**.

- **interface loopback**
**l_num** - Routed loopback interface
specified by **l_num**.

- **interface management**
**m_num** - Routed management interface
specified by **m_num**.

- **interface port-channel**
**p_num**  - Routed port channel Interface
specified by **p_num**.

- **interface vlan**
**v_num** - VLAN interface specified by
**v_num**.

- **interface VXLAN**
**vx_num**  - VXLAN interface specified by
**vx_num**.

- mac_addr  - MAC address to filter routing table entries.
The options include the following:

- **no parameter** - Routing table entries not filtered by
interface MAC address.

- **mac_address**
**mac_address** - Entries with matching
**mac_address** (dotted hex notation –
H.H.H).

- **data** - Details of information provided by command.
The varnames include the following:

- **no parameter** - Routing table entries.

- **summary** - Summary of ARP table
entries.

- **summary total** - Number of ARP table
entries.


**Examples**

- This command displays ARP cache entries that map MAC addresses to IPv4
addresses.
```
`switch> **show ip arp**

Address         Age (min)  Hardware Addr   Interface
172.25.0.2              0  004c.6211.021e  Vlan101, Port-Channel2
172.22.0.1              0  004c.6214.3699  Vlan1000, Port-Channel1
172.22.0.2              0  004c.6219.a0f3  Vlan1000, Port-Channel1
172.22.0.3              0  0045.4942.a32c  Vlan1000, Ethernet33
172.22.0.5              0  f012.3118.c09d  Vlan1000, Port-Channel1
172.22.0.6              0  00e1.d11a.a1eb  Vlan1000, Ethernet5
172.22.0.7              0  004f.e320.cd23  Vlan1000, Ethernet6
172.22.0.8              0  0032.48da.f9d9  Vlan1000, Ethernet37
172.22.0.9              0  0018.910a.1fc5  Vlan1000, Ethernet29
172.22.0.11             0  0056.cbe9.8510  Vlan1000, Ethernet26
switch>`
```

- This command displays ARP cache entries that map MAC addresses to IPv4
addresses. The ouput displays host names assigned to IP addresses in place
of the
address.
```
`switch> **show ip arp resolve**

Address         Age (min)  Hardware Addr   Interface
green-vl101.new         0  004c.6211.021e  Vlan101, Port-Channel2
172.22.0.1              0  004c.6214.3699  Vlan1000, Port-Channel1
orange-vl1000.n         0  004c.6219.a0f3  Vlan1000, Port-Channel1
172.22.0.3              0  0045.4942.a32c  Vlan1000, Ethernet33
purple.newcompa         0  f012.3118.c09d  Vlan1000, Port-Channel1
pink.newcompany         0  00e1.d11a.a1eb  Vlan1000, Ethernet5
yellow.newcompa         0  004f.e320.cd23  Vlan1000, Ethernet6
172.22.0.8              0  0032.48da.f9d9  Vlan1000, Ethernet37
royalblue.newco         0  0018.910a.1fc5  Vlan1000, Ethernet29
172.22.0.11             0  0056.cbe9.8510  Vlan1000, Ethernet26
switch>`
```


### show ip arp inspection
statistics


The **show ip arp inspection statistics** command displays the
statistics of inspected ARP packets. For a specified VLAN specified, the output
displays only VLANs with ARP inspection enabled. If no VLAN specified, the output
displays all VLANs with ARP inspection enabled.


**Command Mode**


EXEC


**Command Syntax**


show ip arp inspection statistics [vlan
[vid]|[interface]
interface
intf_slot | intf_port]


**Parameters**


- **vid** - Specifies the VLAN interface ID.

- **interface** - Specifies the interface (e.g.,
Ethernet).

- **intf_slot** - Specifies the interface
slot.

- **intf_port** - Specifies the interface
port.

- **INTF** - Specifies the VLAN interface slot and
port.


**Related Commands**

- ip arp inspection limit

- ip arp inspection trust

- ip arp inspection vlan


**Examples**

- This command display statistics of inspected ARP packets for VLAN
**10**.
```
`switch(config)# **show ip arp inspection statistics vlan 10**

Vlan : 10
--------------
ARP
Req Forwarded = 20
ARP Res Forwarded = 20
ARP Req Dropped = 1
ARP Res Dropped = 1
Last invalid ARP:
Time: 10:20:30 ( 5 minutes ago )
Reason: Bad IP/Mac match
Received on: Ethernet 3/1
Packet:
  Source MAC: 00:01:00:01:00:01
  Dest MAC: 00:02:00:02:00:02
  ARP Type: Request
  ARP Sender MAC: 00:01:00:01:00:01
  ARP Sender IP: 1.1.1

switch(config)#`
```

- This command displays ARP inspection statistics for Ethernet interface
**3/1**.
```
`switch(config)# **show ip arp inspection statistics ethernet interface 3/1**
interface : 3/1
--------
ARP Req Forwarded = 10
ARP Res Forwarded = 10
ARP Req Dropped = 1
ARP Res Dropped = 1

Last invalid ARP:
Time: 10:20:30 ( 5 minutes ago )
Reason: Bad IP/Mac match
Received on: VLAN 10
Packet:
  Source MAC: 00:01:00:01:00:01
  Dest MAC: 00:02:00:02:00:02
  ARP Type: Request
  ARP Sender MAC: 00:01:00:01:00:01
  ARP Sender IP: 1.1.1

switch(config)#`
```


### show ip arp inspection
vlan


The **show ip arp inspection vlan** command displays the
configuration and operation state of ARP inspection. For a VLAN range specified, the
output displays only VLANs with ARP inspection enabled. If no VLAN specified, the
output displays all VLANs with ARP inspection enabled. The operation state turns to
***Active*** when hardware becomes ready to
trap ARP packets for inspection.


**Command Mode**


EXEC


**Command Syntax**


show ip arp inspection vlan [list]


**Parameters**


**list** - Specifies the VLAN interface number.


**Related Commands**

- ip arp inspection limit

- ip arp inspection trust

- show ip arp inspection statistics


**Example**


This command displays the configuration and operation state of ARP inspection for
VLANs **1** through
**150**.
```
`switch(config)# **show ip arp inspection vlan 1 - 150**

VLAN 1
----------
Configuration
: Enabled
Operation State : Active
VLAN 2
----------
Configuration
: Enabled
Operation State : Active
{...}
VLAN 150
----------
Configuration
: Enabled
Operation State : Active

switch(config)#`
```


### show ip dhcp relay counters


The **show ip dhcp relay counters** command displays the number
of DHCP packets received, forwarded, or dropped on the switch and on all interfaces
enabled as DHCP relay agents.


**Command Mode**


EXEC


**Command Syntax**


show ip dhcp relay counters


**Example**


This command displays the IP DHCP relay counter
table.
```
`switch> **show ip dhcp relay counters**

          |  Dhcp Packets  |
Interface | Rcvd Fwdd Drop |         Last Cleared
----------|----- ---- -----|---------------------
  All Req |  376  376    0 | 4 days, 19:55:12 ago
 All Resp |  277  277    0 |
          |                |
 Vlan1000 |    0    0    0 | 4 days, 19:54:24 ago
 Vlan1036 |  376  277    0 | 4 days, 19:54:24 ago

switch>`
```


### show ip dhcp relay


The **show ip dhcp relay** command displays the DHCP relay
agent configuration status on the switch.


**Command Mode**


EXEC


**Command Syntax**


show ip dhcp relay


**Example**


This command displays the DHCP relay agent configuration
status.
```
`switch> **show ip dhcp relay**
DHCP Relay is active
DHCP Relay Option (82)is enabled
DHCP Relay vendor-specific suboption (9) under information option (82)
DHCP Smart Relay is enabled
Interface: Vlan100
  DHCP Smart Relay is disabled
  DHCP servers: 10.4.4.4
switch>`
```


### show ip dhcp snooping
counters


The **show ip dhcp snooping counters** command displays
counters that track the quantity of DHCP request and reply packets received by the
switch. The output displays data for each VLAN or aggregated for all VLANs with
counters for packets dropped.


**Command Mode**


EXEC


**Command Syntax**


show ip dhcp snooping counters
[counter_typedebug]


**Parameters**


**counter_type** - Displays the type of counter.

- **no parameter** - Command displays counters for each VLAN.

- **debug** - Command displays aggregate counters and
drop cause counters.


**Examples**

- This command displays the number of DHCP packets sent and received on each
VLAN.
```
`switch> **show ip dhcp snooping counters**

     | Dhcp Request Pkts | Dhcp Reply Pkts |
Vlan |  Rcvd  Fwdd  Drop | Rcvd Fwdd  Drop | Last Cleared
-----|------ ----- ------|----- ---- ------|-------------
 100 |     0     0     0 |    0    0     0 |  0:35:39 ago

switch>`
```

- This command displays the number of DHCP packets sent on the
switch.
```
`switch> **show ip dhcp snooping counters debug**
Counter                       Snooping to Relay Relay to Snooping
----------------------------- ----------------- -----------------
Received                                      0                 0
Forwarded                                     0                 0
Dropped - Invalid VlanId                      0                 0
Dropped - Parse error                         0                 0
Dropped - Invalid Dhcp Optype                 0                 0
Dropped - Invalid Info Option                 0                 0
Dropped - Snooping disabled                   0                 0

Last Cleared:  3:37:18 ago
switch>`
```


### show ip dhcp snooping
hardware


The **show ip dhcp snooping hardware** command displays
internal hardware DHCP snooping status on the switch.


**Command Mode**


EXEC


**Command Syntax**


show ip dhcp snooping hardware


**Example**


This command DHCP snooping hardware
status.
```
`switch> **show ip dhcp snooping hardware**
DHCP Snooping is enabled
DHCP Snooping is enabled on following VLANs:
    None
    Vlans enabled per Slice
        Slice:  FixedSystem
        None
switch>`
```


### show ip dhcp snooping


The **show ip dhcp snooping** command displays the DHCP
snooping configuration.


**Command Mode**


EXEC


**Command Syntax**


show ip dhcp snooping


**Example**


This command displays the switch’s DHCP snooping
configuration.
```
`switch> **show ip dhcp snooping**
DHCP Snooping is enabled
DHCP Snooping is operational
DHCP Snooping is configured on following VLANs:
  100
DHCP Snooping is operational on following VLANs:
  100
Insertion of Option-82 is enabled
  Circuit-id format: Interface name:Vlan ID
  Remote-id: 00:1c:73:1f:b4:38 (Switch MAC)
switch>`
```


### show ip hardware fib summary


The **show ip hardware fib summary** command displays the
statistics of the RECMP.


**Command Mode**


Privileged EXEC


**Command Syntax**


show ip hardware fib summary


**Example**


The following command is used to show the statistics of
RECMP:
```
`switch# **show ip hardware fib summary**
Fib summary
-----------
Adjacency sharing: disabled
BFD peer event: enabled
Deletion Delay: 0
Protect default route: disabled
PBR: supported
URPF: supported
ICMP unreachable: enabled
Max Ale ECMP: 600
UCMP weight deviation: 0.0
Maximum number of routes: 0
Fib compression: disabled
**Resource optimization for adjacency programming: enabled
Adjacency resource optimization thresholds: low 20, high 80**`
```


**About the Output**


The last two lines of the output displays if feature is enabled and the corresponding
threshold values for starting and stopping the optimization process.


### show ip interface


The **show ip interface** command displays the status of specified
interfaces that are configured as routed ports. The command provides the following
information:

- Interface description

- Internet address

- Broadcast address

- Address configuration method

- Proxy-ARP status

- MTU size


**Command Mode**


EXEC


**Command Syntax**


show ip interface [interface_name]
[vrf_inst]


**Parameters**


- **interface_name** - Interfaces for which command displays
status.

- **no parameter** - All routed interfaces.

- **ipv4_addr** - Neighbor IPv4 address.

- **ethernet**
**e_range** - Routed Ethernet interfaces specified by
**e_range**.

- **loopback**
**l_range** - Routed loopback interfaces specified by
**l_range**.

- **management**
**m_range** - Routed management interfaces specified by
**m_range**.

- **port-channel**
**p_range** -  Routed port channel Interfaces specified by
**p_range**.

- **vlan**
**v_range** - VLAN interfaces specified by
**v_range**.

- **VXLAN**
**vx_range** - VXLAN interfaces specified by
**vx_range**.

- **vrf_inst** - Specifies the VRF instance for which data is
displayed.

- **no parameter** - Context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF instance. System
default VRF is specified by **default**.


**Examples**

- This command displays IP status of configured VLAN interfaces numbered between
**900** and
**910**.
```
`switch> **show ip interface vlan 900-910**
! Some interfaces do not exist
Vlan901 is up, line protocol is up (connected)
  Description: ar.pqt.mlag.peer
  Internet address is 170.23.254.1/30
  Broadcast address is 255.255.255.255
  Address determined by manual configuration
  Proxy-ARP is disabled
  MTU 9212 bytes
Vlan903 is up, line protocol is up (connected)
  Description: ar.pqt.rn.170.23.254.16/29
  Internet address is 170.23.254.19/29
  Broadcast address is 255.255.255.255
  Address determined by manual configuration
  Proxy-ARP is disabled
  MTU 9212 bytes`
```

- This command displays the configured TCP Maximum Segment Size (MSS) ceiling value of
**1436** bytes for an Ethernet interface
**25**.

```
`switch> **show ip interface ethernet 25**
Ethernet25 is up, line protocol is up (connected)
  Internet address is 10.1.1.1/24
  Broadcast address is 255.255.255.255
  IPv6 Interface Forwarding : None
  Proxy-ARP is disabled
  Local Proxy-ARP is disabled
  Gratuitous ARP is ignored
  IP MTU 1500 bytes
  IPv4 TCP MSS egress ceiling is 1436 bytes`
```


### show ip interface brief


Use the **show ip interface brief** command output to display
the status summary of the specified interfaces that are configured as routed ports.
The command provides the following information for each specified interface:

- IP address

- Operational status

- Line protocol status

- MTU size


**Command Mode**


EXEC


**Command Syntax**


**show ip interface [interface_name]
[vrf_inst] brief**


**Parameters**

- **interface_name** - Interfaces for which command
displays status.

- **no parameter** -  All routed
interfaces.

- **ipv4_addr** - Neighbor IPv4 address.

- **ethernet**
**e_range** - Routed Ethernet interfaces
specified by **e_range**.

- **loopback**
**l_range** -Routed loopback interfaces
specified by **l_range**.

- **management**
**m_range** -  Routed management interfaces
specified by **m_range**.

- **port-channel**
**p_range** -Routed port channel Interfaces
specified by **p_range**.

- **vlan**
**v_range** - VLAN interfaces specified by
**v_range**.

- **VXLAN**
**vx_range** - VXLAN interface range specified
by **vx_range**.

- **vrf_inst** - Specifies the VRF
instance for which data is displayed.

- **no parameter** - Context-active VRF.

- **vrf**
**vrf_name** -Specifies name of VRF
instance. System default VRF is specified by
**default**.


**Example**This command displays the summary status of VLAN interfaces
**900-910**.
```
`switch> **show ip interface vlan 900-910 brief**

! Some interfaces do not exist
Interface              IP Address         Status     Protocol         MTU
Vlan901                170.33.254.1/30    up         up              9212
Vlan902                170.33.254.14/29   up         up              9212
Vlan905                170.33.254.17/29   up         up              1500
Vlan907                170.33.254.67/29   up         up              9212
Vlan910                170.33.254.30/30   up         up              9212`
```


### show ip route


The **show ip route** command displays routing table entries
that are in the Forwarding Information Base (FIB), including static routes, routes
to directly connected networks, and dynamically learned routes. Multiple equal-cost
paths to the same prefix are displayed contiguously as a block, with the destination
prefix displayed only on the first line.


The **show running-config** command displays configured
commands not in the FIB.


**Command Mode**


EXEC


**Command Syntax**


**show ip route
[vrf_instance][address][route_type][info_level][prefix]**


**Parameters**


The **vrf_instance** and **address**
parameterslist first and second, respectively. All other parameters can be placed
in any order.

- **vrf_instance** - Specifies the VRF instance to
display data.

- **no parameter** - Context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF instance.
System default VRF is specified by
**default**.

- **address** - Filters routes by IPv4 address or
subnet.

- **no parameter** - All routing table entries.

- **ipv4_addr** - Routing table entries matching
specified address.

- **ipv4_subnet** - Routing table entries
matching specified subnet (CIDR or address-mask).

- **route_type** - Filters routes by specified protocol
or origin. varnames include:

- **no parameter** - All routing table entries.

- **aggregate** - Entries for BGP aggregate
routes.

- **bgp** - Entries added through BGP
protocol.

- **connected** - Entries for routes to networks
directly connected to the switch.

- **isis** - Entries added through ISIS
protocol.

- **kernel** - Entries appearing in Linux kernel
but not added by EOS software.

- **ospf** - Entries added through OSPF
protocol.

- **rip** - Entries added through RIP
protocol.

- **static** - Entries added through CLI
commands.

- **vrf** - Displays routes in a VRF.

- **Iinfo_level** - Filters entries by next hop
connection. varnames include:

- **no parameter**  - Filters routes whose next hops are directly
connected.

- **detail** - Displays all routes.

- **prefix** - Filters routes by prefix.

- **no parameter** - Specific route entry that matches the address
parameter.

- **longer-prefixes** -  All subnet route
entries in range specified by address parameter.


**Related Command**


The cli vrf command specifies the context-active VRF.


**Examples**

- This command displays IPv4 routes learned through
BGP.
```
`switch> **show ip route bgp**
Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B I - iBGP, B E - eBGP,
       R - RIP, A - Aggregate

 B E    170.44.48.0/23 [20/0] via 170.44.254.78
 B E    170.44.50.0/23 [20/0] via 170.44.254.78
 B E    170.44.52.0/23 [20/0] via 170.44.254.78
 B E    170.44.54.0/23 [20/0] via 170.44.254.78
 B E    170.44.254.112/30 [20/0] via 170.44.254.78
 B E    170.53.0.34/32 [1/0] via 170.44.254.78
 B I    170.53.0.35/32 [1/0] via 170.44.254.2
                             via 170.44.254.13
                             via 170.44.254.20
                             via 170.44.254.67
                             via 170.44.254.35
                             via 170.44.254.98`
```

- This command displays the unicast IP routes installed in the
system.
```
`switch# **show ip route**
 VRF name: default
Codes: C - connected, S - static, K - kernel,
 O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
 E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
 N2 - OSPF NSSA external type2, B I - iBGP, B E - eBGP,
 R - RIP, I - ISIS, A B - BGP Aggregate, A O - OSPF Summary,
 NG - Nexthop Group Static Route

Gateway of last resort is not set
 C 10.1.0.0/16 is directly connected, Vlan2659
 C 10.2.0.0/16 is directly connected, Vlan2148
 C 10.3.0.0/16 is directly connected, Vlan2700
 S 172.17.0.0/16 [1/0] via 172.24.0.1, Management1
 S 172.18.0.0/16 [1/0] via 172.24.0.1, Management1
 S 172.19.0.0/16 [1/0] via 172.24.0.1, Management1
 S 172.20.0.0/16 [1/0] via 172.24.0.1, Management1
 S 172.22.0.0/16 [1/0] via 172.24.0.1, Management1
 C 172.24.0.0/18 is directly connected, Management1`
```

- This command displays the leaked routes from a source
VRF.
```
`switch# **show ip route vrf VRF2 20.0.0.0/8**
...
S L      20.0.0.0/8 [1/0] (source VRF VRF1) via 10.1.2.10, Ethernet1`
```

- This example displays an IPv4 route with Forwarding Equivalency Class (FEC)
with an IPv4 next hop and an IPv6 next hop route.

```
`switch#**show ip route 10.1.0.0/23**
   VRF: default
   Source Codes:
   C - connected, S - static, K - kernel,
   O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
   E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
   N2 - OSPF NSSA external type2, B - Other BGP Routes,
   B I - iBGP, B E - eBGP, R - RIP, I L1 - IS-IS level 1,
   I L2 - IS-IS level 2, O3 - OSPFv3, A B - BGP Aggregate,
   A O - OSPF Summary, NG - Nexthop Group Static Route,
   V - VXLAN Control Service, M - Martian,
   DH - DHCP client installed default route,
   DP - Dynamic Policy Route, L - VRF Leaked,
   G  - gRIBI, RC - Route Cache Route,
   CL - CBF Leaked Route

**S       10.1.0.0/23 [1/0]
                    via 2000:0:0:43::2, Ethernet2
                    via 10.0.1.2, Ethernet4**`
```


### show ip route age


The **show ip route age** command displays the time when the
route for the specified network was present in the routing table. It does not
account for the changes in parameters like metric, next-hop etc.


**Command Mode**


EXEC


**Command Syntax**


**show ip route
address
age**


**Parameters**


**address** - Filters routes by IPv4 address or subnet.

- **ipv4_addr** - Routing table entries matching
specified address.

- **ipv4_subnet** - Routing table entries matching
specified subnet (CIDR or address-mask).


**Example**


This command shows the amount of time since the last update to IP route
**172.17.0.0/20**.
```
`switch> **show ip route 172.17.0.0/20 age**
Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B I - iBGP, B E - eBGP,
       R - RIP, I - ISIS, A - Aggregate

 B E    172.17.0.0/20 via 172.25.0.1, **age 3d01h**
switch>`
```


### show ip route gateway


The **show ip route gateway** command displays IP addresses of
all gateways (next hops) used by active routes.


**Command Mode**


EXEC


**Command Syntax**


show ip route [vrf_instance]
gateway


**Parameters**


**vrf_instance** - Specifies the VRF instance for which data is
displayed.

- **no parameter** - Context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF instance. System
default VRF is specified by **default**.


**Related Commands**


The cli vrf command specifies the context-active VRF.


**Example**


This command displays next hops used by active
routes.
```
`switch> **show ip route gateway**
The following gateways are in use:
   172.25.0.1 Vlan101
   172.17.253.2 Vlan3000
   172.17.254.2 Vlan3901
   172.17.254.11 Vlan3902
   172.17.254.13 Vlan3902
   172.17.254.17 Vlan3903
   172.17.254.20 Vlan3903
   172.17.254.66 Vlan3908
   172.17.254.67 Vlan3908
   172.17.254.68 Vlan3908
   172.17.254.29 Vlan3910
   172.17.254.33 Vlan3911
   172.17.254.35 Vlan3911
   172.17.254.105 Vlan3912
   172.17.254.86 Vlan3984
   172.17.254.98 Vlan3992
   172.17.254.99 Vlan3992
switch>`
```


### show ip route host


The **show ip route host** command displays all host routes in
the host forwarding table. Host routes have a destination prefix of the entire
address ( prefix = **255.255.255.255** or mask =
**/32**). Each entry includes a code of the route’s
purpose:

- **F** - Static routes from the FIB.

- **R**  - Routes defined because the IP address is an interface
address.

- **B** - Broadcast address.

- **A** - Routes to any neighboring host for which the switch has an ARP
entry.


**Command Mode**


EXEC


**Command Syntax**


show ip route [vrf_instance]
host


**Parameters**


**vrf_instance** - Specifies the VRF instance to display
data.

- **no parameter** - Context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF instance. System
default VRF is specified by **default**.


**Related Commands**


The cli vrf command specifies the context-active VRF.


**Example**


This command displays all host routes in the host forwarding
table.
```
`switch> **show ip route host**
R - receive B - broadcast F - FIB, A - attached

F   127.0.0.1 to cpu
B   172.17.252.0 to cpu
A   172.17.253.2 on Vlan2000
R   172.17.253.3 to cpu
A   172.17.253.10 on Vlan2000
B   172.17.253.255 to cpu
B   172.17.254.0 to cpu
R   172.17.254.1 to cpu
B   172.17.254.3 to cpu
B   172.17.254.8 to cpu
A   172.17.254.11 on Vlan2902
R   172.17.254.12 to cpu

F   172.26.0.28 via 172.17.254.20 on Vlan3003
                via 172.17.254.67 on Vlan3008
                via 172.17.254.98 on Vlan3492
                via 172.17.254.2 on Vlan3601
                via 172.17.254.13 on Vlan3602
via 172.17.253.2 on Vlan3000
F   172.26.0.29 via 172.25.0.1 on Vlan101
F   172.26.0.30 via 172.17.254.29 on Vlan3910
F   172.26.0.32 via 172.17.254.105 on Vlan3912
switch>`
```


### show ip route match tag


The **show ip route match tag** command displays the route tag
assigned to the specified IPv4 address or subnet. Route tags are added to static
routes for use by route maps.


**Command Mode**


EXEC


**Command Syntax**


**show ip route [vrf_instance]
address
match tag**


**Parameters**

- **VRF_INSTANCE** - Specifies the VRF instance to
display data.

- **no parameter** - Context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF instance.
System default VRF is specified by
**default**.

- **address** - Displays routes of specified IPv4
address or subnet.

- **ipv4_addr** - Routing table entries
matching specified IPv4 address.

- **ipv4_subnet** - Routing table entries
matching specified IPv4 subnet (CIDR or address-mask).


**Example**


This command displays the route tag for the specified
subnet.
```
`switch> **show ip route 172.17.50.0/23 match tag**
Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B I - iBGP, B E - eBGP,
       R - RIP, I L1 - IS-IS level 1, I L2 - IS-IS level 2,
       O3 - OSPFv3, A B - BGP Aggregate, A O - OSPF Summary,
       NG - Nexthop Group Static Route, V - VXLAN Control Service,
       DH - DHCP client installed default route, M - Martian

 O E2   172.17.50.0/23 tag 0

switch>`
```


### show ip route summary


The **show ip route summary** command displays the number of
routes, categorized by destination prefix, in the routing table.


**Command Mode**


EXEC


**Command Syntax**


show ip route [vrf_instance]
summary


**Parameters**


**vrf_instance** - Specifies the VRF instance for which data
is displayed.

- **no parameter** - Context-active VRF.

- **vrf**
**vrf_name** - Specifies name of VRF instance. System
default VRF is specified by **default**.


**Example**


This command displays a summary of the routing table
contents.
```
`switch> **show ip route summary**
Route Source         Number Of Routes
-------------------------------------
connected                   15
static                       0
ospf                        74
  Intra-area: 32 Inter-area:33 External-1:0 External-2:9
  NSSA External-1:0 NSSA External-2:0
bgp                          7
  External: 6 Internal: 1
internal                    45
attached                    18
aggregate                    0
switch>`
```


### show ip verify source


The **show ip verify source**
command displays the IP source guard (IPSG) configuration, operational states, and
IP-MAC binding entries for the configuration mode interface.


**Command
Mode**


EXEC


**Command Syntax**


show ip
verify source [vlan |
detail]


**Parameters**

- **vlan** - Displays all VLANs configured in
**no ip verify source vlan**.

- **detail** - Displays all source IP-MAC binding
entries configured for IPSG.


**Related Commands**

- ip source binding

- ip verify source


**Examples**

- This command verifies the IPSG configuration and operational
states.
```
`switch(config)# **show ip verify source**
Interface       Operational State
--------------- ------------------------
Ethernet1       IP source guard enabled
Ethernet2       IP source guard disabled`
```

- This command displays all VLANs configured in **no ip verify
source vlan**. Hardware programming errors, e.g.,VLAN
classification failed, indicate in the operational state. If an error
occurs, this VLAN considered as enabled for IPSG. Traffic on this VLAN
filters by
IPSG.
```
`switch(config)# **show ip verify source vlan**
IPSG disabled on VLANS: 1-2
VLAN            Operational State
--------------- ------------------------
1               IP source guard disabled
2               Error: vlan classification failed`
```

- This command displays all source IP-MAC binding entries configured for IPSG.
If programmed into hardware, a source binding entry considered active.
Permits IP traffic matching any active binding entry. If configured. a
source binding entry on an interface or a VLAN with the operational state of
IPSG disabled, this entry does not install in the hardware, in which case an
“IP source guard disabled” state displays. If a port channel has no member
port configured, binding entries configured for this port channel do not
install in hardware, and a “Port-Channel down” state
displays.
```
`switch(config)# **show ip verify source detail**
Interface      IP Address  MAC Address     VLAN  State
-------------- ----------- --------------- ----- ------------------------
Ethernet1      10.1.1.1    0000.aaaa.1111   5     active
Ethernet1      10.1.1.5    0000.aaaa.5555   1     IP source guard disabled
Port-Channel1  20.1.1.1    0000.bbbb.1111   4     Port-Channel down`
```


### show platform arad ip
route summary


The **show platform arad ip route summary** command shows
hardware resource usage of IPv4 routes.


**Command Mode**


EXEC


**Command Syntax**


show platform arad ip route summary


**Related Commands**

- The agent SandL3Unicast terminate command enables
restarting the layer 3 agent to ensure IPv4 routes are optimized.

- The ip hardware fib optimize command enables IPv4
route scale.

- The show platform arad ip route command shows
resources for all IPv4 routes in hardware. Routes that use the additional
hardware resources will appear with an asterisk.


**Example**


This command shows hardware resource usage of IPv4
routes.
```
`switch(config)# **show platform arad ip route summary**
Total number of VRFs: 1
Total number of routes: 25
Total number of route-paths: 21
Total number of lem-routes: 4

switch(config)#`
```


### show platform arad ip
route


The **show platform arad ip route** command shows resources for
all IPv4 routes in hardware. Routes that use the additional hardware resources will
appear with an asterisk.


**Command Mode**


EXEC


**Command Syntax**


show platform arad ip route


**Related Commands**

- The agent SandL3Unicast terminate command enables
restarting the Layer 3 agent to ensure IPv4 routes are optimized.

- The ip hardware fib optimize command enables IPv4
route scale.

- The show platform arad ip route summary command
shows hardware resource usage of IPv4 routes.


**Examples**

- This command displays the platform unicast forwarding routes. In this
example, the ACL label field in the following table is
**4094** by default for all routes. If an IPv4
egress RACL is applied to an SVI, all routes corresponding to that VLAN will
have an ACL label value. In this case, the ACL Label field value is
2.
```
`switch# **show platform arad ip route**
 Tunnel Type: M(mpls), G(gre)

-------------------------------------------------------------------------------
|                                Routing Table                                |
|
|------------------------------------------------------------------------------
|VRF|   Destination    |      |                    |     | Acl   |             |
ECMP| FEC | Tunnel
| ID|   Subnet         | Cmd  |       Destination  | VID | Label |  MAC / CPU
Code |Index|Index|T Value

-------------------------------------------------------------------------------
|0  |0.0.0.0/8         |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1031 | -
|0  |10.1.0.0/16       |TRAP | CoppSystemL3DstMiss|2659 | - | ArpTrap | - |1030 | -
|0  |10.2.0.0/16       |TRAP | CoppSystemL3DstMiss|2148 | - | ArpTrap | - |1026 | -
|0  |172.24.0.0/18     |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1032 | -
|0  |0.0.0.0/0         |TRAP | CoppSystemL3LpmOver|0    | - | SlowReceive | -
|1024 | -
|0  |10.1.0.0/32*      |TRAP | CoppSystemIpBcast  |0    | - | BcastReceive | -
|1027 | -
|0  |10.1.0.1/32*      |TRAP | CoppSystemIpUcast  |0    | - | Receive | - |32766| -
|0  |10.1.255.1/32*    |ROUTE| Po1                |2659 |4094 | 00:1f:5d:6b:ce:45
| - |1035 | -
|0  |10.1.255.255/32*  |TRAP | CoppSystemIpBcast  |0    | - | BcastReceive | -
|1027 | -
|0  |10.3.0.0/32*      |TRAP | CoppSystemIpBcast  |0    | - | BcastReceive | -
|1027 | -
|0  |10.3.0.1/32*      |TRAP | CoppSystemIpUcast  |0    | - | Receive | - |32766| -
|0  |10.3.255.1/32*    |ROUTE| Et18               |2700 |2 | 00:1f:5d:6b:00:01
| - |1038 | -
...........................................................`
```

- This command shows resources for all IPv4 routes in hardware. Routes that
use the additional hardware resources will appear with an
asterisk.
```
`switch(config)# **show platform arad ip route**
Tunnel Type: M(mpls), G(gre)
* - Routes in LEM

-------------------------------------------------------------------------------
|                              Routing Table                     |             |
|------------------------------------------------------------------------------
|VRF|  Destination |     |                   |    |Acl  |                 |ECMP
| FEC | Tunnel
|ID |    Subnet    | Cmd |    Destination    |VID |Label| MAC / CPU Code
|Index|Index|T Value

-------------------------------------------------------------------------------
|0  |0.0.0.0/8       |TRAP |CoppSystemL3DstMiss|0   | -   |ArpTrap          |  -
|1030 |   -
|0  |100.1.0.0/32    |TRAP |CoppSystemIpBcast  |0   | -   |BcastReceive     |  -
|1032 |   -
|0  |100.1.0.0/32    |TRAP |CoppSystemIpUcast  |0   | -   |Receive          |  -
|32766|   -
|0  |100.1.255.255/32|TRAP |CoppSystemIpBcast  |0   | -   |BcastReceive     |  -
|1032 |   -
|0  |200.1.255.255/32|TRAP |CoppSystemIpBcast  |0   | -   |BcastReceive     |  -
|1032 |   -
|0  |200.1.0.0/16    |TRAP |CoppSystemL3DstMiss|1007| -   |ArpTrap          |  -
|1029 |   -
|0  |0.0.0.0/0       |TRAP |CoppSystemL3LpmOver|0   | -   |SlowReceive      |  -
|1024 |   -
|0  |4.4.4.0/24*     |ROUTE|Et10               |1007| -   |00:01:00:02:00:03|  -
|1033 |   -
|0  |10.20.30.0/24*  |ROUTE|Et9                |1006| -   |00:01:00:02:00:03|  -
|1027 |   -

switch(config)#`
```


### show platform barefoot bfrt


The **show platform barefoot bfrt** command displays
information about the current BfRuntime server configuration.


**Command Mode**


EXEC


**Command Syntax**


show platform barefoot bfrt


**Parameters**


**no parameter** - Specify the state of the system.


**Example**


The following output is for a system where the BfRuntime server has been
configured.
```
`(switch)# **show platform barefoot bfrt**
Namespace: management
FixedSystem:0.0.0.0:50052`
```


### show platform fap eedb
ip-tunnel gre interface tunnel


The **show platform fap eedb ip-tunnel gre interface tunnel**
command verifies the tunnel encapsulation programming for the tunnel interface.


**Command Mode**


EXEC


**Command Syntax**


**show platform fap eedb ip-tunnel gre interface tunnel
number**


**Parameter**


**number** - Specifies the tunnel interface number.


**Example**


These commands verify the tunnel encapsulation programming for the **tunnel
interface
10**.
```
`switch# **show platform fap eedb ip-tunnel gre interface tunnel 10**
----------------------------------------------------------------------------
|                                                  Jericho0                   |
|                                 GRE Tunnel Egress Encapsulation DB
|
|--------------------------------------------------------------------------|
| Bank/ | OutLIF | Next   | VSI  | Encap | TOS  | TTL | Source | Destination|
OamLIF| OutLIF | Drop|
| Offset|        | OutLIF | LSB  | Mode  |      |     | IP     | IP         | Set
| Profile|     |
|--------------------------------------------------------------------------|
| 3/0   | 0x6000 | 0x4010 | 0    | 2     | 10   | 10  | 10.1.1.1 | 10.1.1.2 | No
| 0      | No  |

switch# **show platform fap eedb ip-tunnel**
-------------------------------------------------------------------------------
|                                                  Jericho0                     |
|                                     IP Tunnel Egress Encapsulation DB
|
|------------------------------------------------------------------------------
| Bank/ | OutLIF | Next   | VSI | Encap| TOS | TTL | Src | Destination | OamLIF
| OutLIF  | Drop|
| Offset|        | OutLIF | LSB | Mode | Idx | Idx | Idx | IP          | Set    |
Profile |     |
|------------------------------------------------------------------------------
| 3/0   | 0x6000 | 0x4010 | 0   | 2    | 9   | 0   | 0   | 10.1.1.2    | No     |
0       | No  |`
```


### show platform fap tcam
summary


The **show platform fap tcam summary** command displays
information about the TCAM bank that is allocated for GRE packet termination lookup.


**Command Mode**


EXEC


**Command Syntax**


**show platform fap tcam summary**


**Example**


This command verifies if the TCAM bank is allocated for GRE packet termination
lookup.
```
`switch# **show platform fap tcam summary**

Tcam Allocation (Jericho0)
Bank        Used By                Reserved By
---------- ----------------------- -----------
0           dbGreTunnel             -`
```


### show platform trident
forwarding-table partition


The **show platform trident forwarding-table partition**
command displays the size of the L2 MAC entry tables, L3 IP forwarding tables, and
Longest Prefix Match (LPM) routes.


**Command Mode**


Privileged EXEC


**Command Syntax**


show platform trident forwarding-table partition


show platform trident forwarding-table partition flexible


**Examples**

- The **show platform trident forwarding-table
partition** command displays the Trident forwarding table
information.
```
`switch(config)# **show platform trident forwarding-table partition**
L2 Table Size: 96k
L3 Host Table Size: 208k
LPM Table Size: 16k
switch(config)#`
```

- The **show platform trident forwarding-table partition
flexible** shows the banks allocated for ALPM as
well.
```
`switch(config)# **show platform trident forwarding-table partition flexible**
--------------------------------------------------
Minimum L2 entries             = 32768
Minimum L3 entries             = 16384
Maximum L2 entries             = 262144
Maximum L3 entries             = 262144
Maximum Exact Match entries    = 131072
L2 entries per bucket          = 4
L3 entries per bucket          = 4
Exact Match entries per bucket = 2
Maximum entries per bucket     = 4
Maximum shared buckets         = 65536
Maximum entries per bank       = 32768
Maximum shared banks           = 8
ALPM entries per bank          = 46080
ALPM                           = Enabled
--------------------
# UFT bank details #
--------------------
S - Shared UFT bank, D - Dedicated UFT bank
+-------------+------------+------+------------+--------------+
| Physical ID |  Feature   | Type | Logical ID | Hash Offset  |
+-------------+------------+------+------------+--------------+
|      0      |     L2     |  D   |     0      |     0x4      |
|      1      |     L2     |  D   |     1      |     0xe      |
|      2      |    ALPM    |  S   |    N/A     |      0       |
|      3      |    ALPM    |  S   |    N/A     |      0       |
|      4      |    ALPM    |  S   |    N/A     |      0       |
|      5      |    ALPM    |  S   |    N/A     |      0       |
|      6      |     L2     |  S   |     2      |     0xc      |
|      7      | ExactMatch |  S   |     0      |     0xc      |
|      8      | ExactMatch |  S   |     1      |     0xf      |
|      9      |     L3     |  S   |     2      |     0xc      |
|      10     |     L3     |  D   |     0      |     0x0      |
|      11     |     L3     |  D   |     1      |     0x8      |
+-------------+------------+------+------------+--------------+`
```


### show platform trident l3 shadow dlb-ecmp-group-control


The **show platform trident l3 shadow dlb-ecmp-group-control** displays information about
Dynamic Load Balancing with ECMP groups.


**Command Mode**


Privileged EXEC


**Command Syntax**


show platform trident l3 shadow dlb-ecmp-group-control


**Example**


Use the following command to display information about DLB and ECMP
groups:
```
`switch# show platform trident l3 shadow dlb-ecmp-group-control
     DLB_ECMP_GROUP_CONTROL:
     eId  size path baseAddr flowSize memPtr flowBase OC mode inDur
     ---- ---- ---- -------- -------- ------ -------- -- ---- ------
        1    3    0    136      1        1      256      1  0    500

Legend:
eId = Entry ID
size = Primary Group Size
path = Primary Path Threshold
baseAddr = Group Port To Member Base Address
flowSize = Flow Set Size
memPtr = Group Membership Pointer
flowBase = Flow Set Base
OC = Enable Optimal Candidate
mode = Port Assignment Mode
inDur = Inactivity Duration`
```


The output displays the following information:

- **Entry ID** - Indicates the dynamic load balance
group ID.

- **Primary Group Size** - Indicates the number of
members in the DLB group.

- **Enable optimal candidate** - Indicates the least
loaded member or predefined member selection. Always set to
1 to ensure the selection of the least loaded member.

- **Inactivity duration** - Indicates the inactivity
period. If the switch does not receive new packets from a particular flow
within this duration, then the optimal member becomes the new member for the
flow. Represented in microseconds.


### show rib route ip


The **show rib route ip** command displays a list of IPv4
Routing Information Base (RIB) routes.


**Command Mode**


EXEC


**Command Syntax**


show rib route ip [vrf
vrf_name][prefix][route_type]


**Parameters**


- **vrf**
**vrf_name** - Displays RIB routes from the specified
VRF.

- **prefix** - Displays routes filtered by the specified
IPv4 information. Options include the following:

- **ip_address** - Displays RIB routes filtered
by the specified IPv4 address.

- **ip_subnet_mask** - Displays RIB routes
filtered by the specified IPv4 address and subnet mask.

- **ip_prefix** - Displays RIB routes filtered
by the specified IPv4 prefix.

- **route_type** - Displays routes filtered by the
specified route type. Options include the following:

- **bgp** - Displays RIB routes filtered by
BGP.

- **connected** - Displays RIB routes filtered
by connected routes.

- **dynamicPolicy** - Displays RIB routes
filtered by dynamic policy routes.

- **host** - Displays RIB routes filtered by
host routes.

- **isis** - Displays RIB routes filtered by
IS-IS routes.

- **ospf** - Displays RIB routes filtered by
OSPF routes.

- **ospf3** - Displays RIB routes filtered by
OSPF3 routes.

- **reserved** - Displays RIB routes filtered by
reserved routes.

- **route-input** - Displays RIB routes filtered
by route-input routes.

- **static** - Displays RIB routes filtered by
static routes.

- **vrf** - Displays routes in a VRF.

- **vrf-leak** - Displays leaked routes in a
VRF.


**Examples**

- This command displays IPv4 RIB static
routes.
```
`switch# **show rib route ip static**
VRF name: default, VRF ID: 0xfe, Protocol: static
Codes: C - Connected, S - Static, P - Route Input
       B - BGP, O - Ospf, O3 - Ospf3, I - Isis
       > - Best Route, * - Unresolved Nexthop
       L - Part of a recursive route resolution loop
>S    10.80.0.0/12 [1/0]
         via 172.30.149.129 [0/1]
            via Management1, directly connected
>S    172.16.0.0/12 [1/0]
         via 172.30.149.129 [0/1]
            via Management1, directly connected
switch#`
```

- This command displays IPv4 RIB connected
routes.
```
`switch# **show rib route ip connected**
VRF name: default, VRF ID: 0xfe, Protocol: connected
Codes: C - Connected, S - Static, P - Route Input
       B - BGP, O - Ospf, O3 - Ospf3, I - Isis
       > - Best Route, * - Unresolved Nexthop
       L - Part of a recursive route resolution loop
>C    10.1.0.0/24 [0/1]
         via 10.1.0.102, Ethernet1
>C    10.2.0.0/24 [0/1]
         via 10.2.0.102, Ethernet2
>C    10.3.0.0/24 [0/1]
         via 10.3.0.102, Ethernet3
switch#`
```

- This command displays routes leaked through VRF leak
agent.
```
`switch# **show rib route ip vrf VRF2 vrf-leak**
VRF: VRF2, Protocol: vrf-leak
...
>VL    20.0.0.0/8 [1/0] source VRF: VRF1
          via 10.1.2.10 [0/0] type ipv4
             via 10.1.2.10, Ethernet1`
```


### show rib route fib policy excluded


The **show rib route fib policy excluded** command displays the
RIB routes filtered by FIB policy. The **fib policy excluded**
parameter displays the RIB routes excluded from programming into
FIB, by FIB policy.


**Command Mode**


EXEC


**Command Syntax**


show rib route [ipv4 | ipv6]
fib policy excluded


**Example**


The following example displays the RIB routes excluded by the FIB policy using the
**fib policy excluded** option of the **show
rib route**
command.
```
`switch# **show rib route ipv6 fib policy excluded**
switch# **show rib route ip bgp fib policy excluded**

VRF name: default, VRF ID: 0xfe, Protocol: bgp
Codes: C - Connected, S - Static, P - Route Input
       B - BGP, O - Ospf, O3 - Ospf3, I - Isis
       > - Best Route, * - Unresolved Nexthop
       L - Part of a recursive route resolution loop
>B    10.1.0.0/24 [200/0]
         via 10.2.2.1 [115/20] type tunnel
            via 10.3.5.1, Ethernet1
         via 10.2.0.1 [115/20] type tunnel
            via 10.3.4.1, Ethernet2
            via 10.3.6.1, Ethernet3
>B    10.1.0.0/24 [200/0]
         via 10.2.2.1 [115/20] type tunnel
            via 10.3.5.1, Ethernet1
         via 10.2.0.1 [115/20] type tunnel
            via 10.3.4.1, Ethernet2
            via 10.3.6.1, Ethernet3`
```


### show rib route summary


The **show rib route summary** command displays information
about the routes present in the Routing Information Base.


**Command Mode**


EXEC


**Command Syntax**


show rib route summary [info_level]


**Parameters**


- **no parameter** - Displays data in one table with the summary of all
routes in the RIB for default VRF.

- **brief** - Displays one table with the summary of all
routes across all configured VRFs.

- **ip** - Displays one table with the summary of all
IPv4 in the RIB for default VRF.

- **ipv6** - Displays one table with the summary of all
IPv4 in the RIB for default VRF.

- **vrf
vrf_Name** - Displays one table with the summary of
all routes in the Routing Information Base for the specified VRF.

- **vrf all** - Displays one table with the summary of
all routes in the Routing Information Base for each configured VRF.

- info_level - Displays the amount of information. Options
include the following:

- **Display Values**

- **VRF** - VRF RIB displayed.

- **Route Source** - Source for the route.

- **Number of Routes** - Number of routes for each
source.


**Examples**

- The following displays data in one table with the summary of all routes
in the RIB for default VRF.


```
`switch> **show rib route summary**
VRF: default
Route Source         Number Of Routes
-------------------- ----------------
BGP                                 1
Connected                           4
Dynamic policy                      0
IS-IS                               0
OSPF                                0
OSPFv3                              0
RIP                                 0
Route input                         2
Static                              0
VRF leak                            0`
```

- The following displays data in one table with the summary of all routes
across all configured VRFs.


```
`switch> **show rib route summary brief**
Route Source         Number Of Routes
-------------------- ----------------
BGP                                 2
Connected                           8
Dynamic policy                      0
IS-IS                               0
OSPF                                0
OSPFv3                              0
RIP                                 0
Route input                         4
Static                              0
VRF leak                            0`
```

- The following displays data in one table with the summary of all IPv4
routes in the RIB for default VRF.


```
`switch> **show rib route summary ip**
VRF: default
Route Source         Number Of Routes
-------------------- ----------------
BGP                                 1
Connected                           4
Dynamic policy                      0
IS-IS                               0
OSPF                                0
OSPFv3                              0
RIP                                 0
Route input                         2
Static                              0
VRF leak                            0`
```

- The following displays data in one table with the summary of all IPv6
routes in the RIB for default VRF.


```
`switch> **show rib route summary ipv6**
VRF: default
Route Source         Number Of Routes
-------------------- ----------------
BGP                                 0
Connected                           0
Dynamic policy                      0
IS-IS                               0
OSPF                                0
OSPFv3                              0
RIP                                 0
Route input                         0
Static                              0
VRF leak                            0`
```

- The following displays data in one table with the summary of all routes
in the RIB for the VRF named **red**.


```
`switch> **show rib route summary vrf red**
VRF: red
Route Source         Number Of Routes
-------------------- ----------------
BGP                                 1
Connected                           4
Dynamic policy                      0
IS-IS                               0
OSPF                                0
OSPFv3                              0
RIP                                 0
Route input                         2
Static                              0
VRF leak                            0`
```

- The following displays data in one table with the summary of all routes
in the RIB for each configured VRF.


```
`switch> **show rib route summary vrf all**
VRF: red
Route Source         Number Of Routes
-------------------- ----------------
BGP                                 1
Connected                           4
Dynamic policy                      0
IS-IS                               0
OSPF                                0
OSPFv3                              0
RIP                                 0
Route input                         2
Static                              0
VRF leak                            0

VRF: default
Route Source         Number Of Routes
-------------------- ----------------
BGP                                 1
Connected                           4
Dynamic policy                      0
IS-IS                               0
OSPF                                0
OSPFv3                              0
RIP                                 0
Route input                         2
Static                              0
VRF leak                            0`
```


### show routing-context
vrf


The **show routing-context vrf** command displays the
context-active VRF. The context-active VRF determines the default VRF that
VRF-context aware commands use when displaying routing table data from a specified
VRF.


**Command Mode**


EXEC


**Command Syntax**


show routing-context vrf


**Related Commands**


The cli vrf command specifies the context-active VRF.


**Example**


This command displays the context-active
VRF.
```
`switch> **show routing-context vrf**
Current VRF routing-context is PURPLE
switch>`
```


### show snapshot counters ecmp history


The **show snapshot counters ecmp history** displays information about the AGM configuration.


**Command Mode**


EXEC


**Command Syntax**


show snapshot counters ecmp history


**Parameters**


- **Request ID** - Identifies the snapshot Request ID to use for the **clear**
command.

- **Output directory URL** - Identifies the snapshot storage location.

- **Complete** - Identifies the snapshot completion status.

- **Poll Interval** - Identifies the configured polling interval for the snapshot.

- **Total poll count** - Identifies the total number of hardware
counters collected.

- **Start time** and **Stopped time** - Identifies the system time when the snapshot
started and stopped.

- **L2 Adjacency ID** and **Interfaces** -
The summary of the ECMP groups monitored by AGM.


**Example**


Use the **show snapshot counters ecmp history** to display
information about the
configuration.
```
`switch# **show snapshot counters ecmp history**
Request ID: 17
Output directory URL: file:/var/tmp/ecmpMonitor
Output file name(s): ecmpMonitor-17-adj1284.ctr, ecmpMonitor-17-adj1268.ctr
Complete: True
Poll interval: 1000 microseconds
Total poll count: 59216
Start time: 2024-06-17 17:58:36
Stop time: 2024-06-17 17:59:36

L2 Adjacency ID       Interfaces
--------------------- ----------------------------------------------------
1268                  Ethernet54/1, Ethernet41/1, Ethernet1/1, Ethernet57/1
1284                  Ethernet20/1, Ethernet35/1, Ethernet41/1, Ethernet8/1, Ethernet1/1`
```




### show tunnel fib static
interface gre


The **show tunnel fib static interface gre** command displays
the Forwarding Information Base (FIB) information for a static interface GRE tunnel.


**Command Mode**


EXEC


**Command Syntax**


show tunnel fib static interface gre
number


**Parameter**


**number** - Specifies the tunnel index number.


**Example**


This command display the interface tunnel configuration with GRE
configured.
```
`switch# **show tunnel fib static interface gre 10**

Type 'Static Interface', index 10, forwarding Primary
   via 10.6.1.2, 'Ethernet6/1'
      GRE, destination 10.1.1.2, source 10.1.1.1, ttl 10, tos 0xa`
```




### show vrf


The **show vrf** command displays the VRF name, RD, supported
protocols, state and included interfaces for the specified VRF or for all VRFs on
the switch.


**Command Mode**


EXEC


**Command Syntax**


show vrf [vrf_instance]


**Parameters**


vrf_instance - Specifies the VRF instance to display.

- **no parameter** - Displays information for all
VRFs.

- **vrf**
**vrf_name** - Displays information for the specified
user-defined VRF.


**Example**


This command displays information for the VRF named
**purple**.
```
`switch> **show vrf purple**
Vrf      RD          Protocols  State       Interfaces
-------- ----------- ---------- ----------- --------------
purple   64496:237   ipv4       no routing  Vlan42, Vlan43

switch>`
```


### start snapshot counters


The **start snapshot counters ecmp** allows the monitoring of packets and bytes traversing the members of the
configured ECMP groups on the switch with a high time resolution.


**Command Mode**


Global Configuration Mode


**Command Syntax**


start snapshot counters
ecmp
poll
interval
interval [milliseconds |
microseconds] duration
duration
seconds
destination_url


**Parameters**

- **interval
interval** - Specify at least 100 microseconds. EOS
does not guarantee the interval, and the actual poll interval may depend on the
system load as well as the number and size of configured ECMP groups. Valid
values include milliseconds and microseconds.

- **duration
duration
seconds** - Specify the duration for collecting data. A
maximum of 3600 seconds can be configured.

- **destination_url** - Optionally, provide a destination
URL for data storage.

- **file** - The path must start with
**/tmp** or
**/tmp**. The files store in the non-persistent
storage.

- **flash** - Files store in persistent
storage.


**Example**


To begin collecting data on the switch at 100 millisecond intervals for 1800 seconds, use
the following
command:
```
`switch(config)#**start snapshot counters ecmp poll interval 100 milliseconds duration 1800 seconds**`
```


### tcp mss ceiling


The **tcp mss ceiling** command configures the Maximum Segment
Size (MSS) limit in the TCP header on the configuration mode interface and enables
TCP MSS clamping.


The **no tcp mss ceiling** and the **default tcp mss
ceiling** commands remove any MSS ceiling limit previously
configured on the interface.


Note: Configuring a TCP MSS ceiling on any Ethernet or tunnel interface enables TCP MSS
clamping on the switch as a whole. Without hardware support, clamping routes all TCP
SYN packets through software, even on interfaces where no TCP MSS ceiling has been
configured. This significantly limits the number of TCP sessions the switch can
establish per second, and can potentially cause packet loss if the CPU traffic
exceeds control plane policy limits.


**Command Mode**


Interface-Ethernet Configuration


Subinterface-Ethernet Configuration


Interface-Port-channel Configuration


Subinterface-Port-channel Configuration


Interface-Tunnel Configuration


Interface-VLAN Configuration


**Command Syntax**


tcp mss ceiling {ipv4
segment size  | ipv6
segment size}{egress |
ingress}


no tcp mss ceiling


default tcp mss ceiling


**Parameters**

- **ipv4**
**segment size** The IPv4 segment size value in bytes.
Values range from **64** to
**65515**.

- **ipv6**
**segment size** The IPv6 segment size value in
bytes. Values range from **64** to
**65495**. This option is not supported on
Sand platform switches (Qumran-MX, Qumran-AX, Jericho, Jericho+).

- **egress** The TCP SYN packets that are forwarded from
the interface to the network.

- **ingress** The TCP SYN packets that are received from
the network to the interface. Not supported on Sand platform switches.


**Guidelines**

- On Sand platform switches (Qumran-MX, Qumran-AX, Jericho, Jericho+), this
command works only for egress, and is supported only on IPv4 unicast packets
entering the switch.

- Clamping can only be configured in one direction per interface and works
only on egress on Sand platform switches.

- To configure ceilings for both IPv4 and IPv6 packets, both configurations
must be included in a single command; re-issuing the command overwrites any
previous settings.

- Clamping configuration has no effect on GRE transit packets.


**Example**


These commands configure **interface ethernet 5** as a routed
port, then specify a maximum MSS ceiling value of **1458**
bytes in TCP SYN packets exiting that port. This enables TCP MSS clamping on the
switch.
```
`switch(config)# **interface ethernet 5**
switch(config-if-Et5)# **no switchport**
switch(config-if-Et5)# **tcp mss ceiling ipv4 1458 egress**
switch(config-if-Et5)#`
```


### tunnel


The **tunnel** command configures options for
protocol-over-protocol tunneling. Because Interface-Tunnel Configuration Mode does not
provide a group change mode, ***running-config*** changes
immediately after executing the commands. The **exit** command
does not affect the configuration.


The **no tunnel** command deletes the specified tunnel
configuration.


**Command Mode**


Interface-tunnel Configuration


**Command Syntax**


tunnel
options


no tunnel
options


**Parameters**

- **options** - Specifies the various tunneling options
as listed below.

- **destination** - Specifies the destination address of
the tunnel.

- **ipsec** - Secures the tunnel with the IPsec
address.

- **key** - Sets the tunnel key.

- **mode** - Specifies the tunnel encapsulation
method.

- **path-mtu-discovery** - Enables the Path MTU
discovery on tunnel.

- **source** - Specifies the source of the
tunnel packets.

- **tos** - Sets the IP type of service
value.

- **ttl** - Sets time to live value.

- **underlay** - Specifies the tunnel underlay.


**Example**


These commands place the switch in interface-tunnel configuration mode for
**interface Tunnel 10** and with GRE tunnel configured
on the interfaces
specified.
```
`switch(config)# **ip routing**
switch(config)# **interface Tunnel 10**
switch(config-if-Tu10)# **tunnel mode gre**
switch(config-if-Tu10)# **ip address 192.168.1.1/24**
switch(config-if-Tu10)# **tunnel source 10.1.1.1**
switch(config-if-Tu10)# **tunnel destination 10.1.1.2**
switch(config-if-Tu10)# **tunnel path-mtu-discovery**
switch(config-if-Tu10)# **tunnel tos 10**
switch(config-if-Tu10)# **tunnel ttl 10**`
```


### vrf (Interface mode)


The **vrf** command adds the configuration mode interface to
the specified VRF. You must create the VRF first, using the vrf instance command.


The **no vrf** and **default vrf**
commands remove the configuration mode interface from the specified VRF by deleting
the corresponding **vrf** command from
***running-config***.


All forms of the **vrf** command remove all IP addresses
associated with the configuration mode interface.


**Command Mode**


Interface-Ethernet Configuration


Interface-Loopback Configuration


Interface-Management Configuration


Interface-Port-channel Configuration


Interface-VLAN Configuration


**Command Syntax**


vrf [vrf_name]


no vrf [vrf_name]


default vrf [vrf_name]


**Parameters**


**vrf_name** - Displays the name of configured VRF.


**Examples**

- These commands add the configuration mode interface (**vlan
20**) to the VRF named
**purple**.
```
`switch(config)# **interface vlan 20**
switch(config-if-Vl20)# **vrf purple**
switch(config-if-Vl20)#`
```

- These commands remove the configuration mode interface from VRF
**purple**.
```
`switch(config)#  **interface vlan 20**
switch(config-if-Vl20)# **no vrf purple**
switch(config-if-Vl20)#`
```


### vrf instance


The **vrf instance** command places the switch in VRF
configuration mode for the specified VRF. If the named VRF does not exist, this
command creates it. The number of user-defined VRFs supported varies by
platform.


To add an interface to the VRF once created, use the vrf (Interface mode) command.


The **no vrf instance** and **default vrf
instance** commands delete the specified VRF instance by
removing the corresponding **vrf instance** command from
***running-config***. This also removes all IP
addresses associated with interfaces that belong to the deleted VRF.


The **exit** command returns the switch to global configuration
mode.


**Command Mode**


Global Configuration


**Command Syntax**


vrf instance [vrf_name]


no vrf instance [vrf_name]


default vrf instance [vrf_name]


**Parameters**


**vrf_name** - The name of the configured VRF. The names
**main** and **default** are
reserved.


**Example**


This command creates a VRF named **purple** and places the
switch in VRF configuration mode for that
VRF.
```
`switch(config)# **vrf instance purple**
switch(config-vrf-purple)#`
```
