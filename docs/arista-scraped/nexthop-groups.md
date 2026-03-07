<!-- Source: https://www.arista.com/en/um-eos/eos-nexthop-groups -->
<!-- Scraped: 2026-03-06T20:51:48.731Z -->

# Nexthop Groups


These sections describe the Nexthop groups:

- Next-hop Group Description

- Next-hop Group Configuration

- Nexthop Group commands


## Next-hop Group Description


Each routing table entry provides the next hop address to a specified destination. A next-hop
address consists of the address of the next device on the path to the entry specified
destination.


A next-hop group uses a data structure that defines a list of next-hop addresses and a tunnel
type for packets routed to the specified address. When an IP route statement specifies a
next-hop group as the next-hop address, the switch configures a static route with a next-hop
group member as the next-hop address and encapsulates packets forwarded to that address as
required by the group tunnel type.


Configure the next-hop group size as a parameter that specifies the number of entries that the
group contains. Group entries not explicitly configured are filled with drop routes. The
switch uses ECMP hashing to select the address within the next-hop group when forwarding
packets. When a packet’s hash selects a drop route, the switch drops the packet.


Next-hop groups are supported on Trident platform switches and has the following restrictions:

- Each switch can support 512 IPv4 or IPv6 Tunnels

- Next-hop groups can contain 256 next-hops.

- The switch supports 1024 next-hop groups.

- Multiple routes can share a tunnel.

- Tunnels do not support IP multicast packets.


Next-hop groups support IP-in-IP tunnels. The entry IP address family within a particular
next-hop group cannot be mixed. They must be all IPv4 or all IPv6 entries.


## Next-hop Group Configuration


Next-hop groups are configured and modified in next-hop-group configuration mode. After a group
is created, it is associated to a static route through an ip route nexthop-group statement.


These tasks are required to configure a next-hop group and apply it to a static route.

- Creating and Editing Next-hop
Groups

- Configuring a Group’s Encapsulation
Parameters

- Configuring the Group’s Size

- Creating Next-hop Group Entries

- Displaying Next-hop Groups

- Applying a Next-hop Group to a Static
Route


### Creating and Editing Next-hop Groups


Create next-hop groups using the nexthop-group command that specifies an
unconfigured group. The switch enters ***nexthop-group*** configuration mode
for the new group. ***Nexthop-group*** mode is also accessible for modifying
existing groups. When in ***nexthop-group*** configuration mode, the
**show active** command displays the group’s
configuration.


- This command creates a next-hop group named
**NH-1**.
```
`switch(config)# **nexthop-group NH-1**
switch(config-nexthop-group-NH-1)#`
```

- These commands enter ***nexthop-group*** configuration mode for the
group named **NH3**, then displays the previously
configured group
parameters.
```
`switch(config)# **nexthop-group NH3**
switch(config-nexthop-group-NH3)#show active
 nexthop-group NH3
   size 4
   ttl 10
   entry 0 tunnel-destination 10.14.21.3
   entry 1 tunnel-destination 10.14.21.5
   entry 2 tunnel-destination 10.14.22.5
   entry 3 tunnel-destination 10.14.22.6
switch(config-nexthop-group-NH3)#`
```


### Configuring Group Encapsulation Parameters


Packets in static routes associated with the next-hop group are encapsulated to support the
group’s tunnel type. Nexthop groups support IP-in-IP tunnels. The group also defines
the source IP address and TTL field contents included in the packet
encapsulation.


- This command configures the TTL setting to **32** for
nexthop group **NH-1** encapsulation
packets.
```
`switch(config)# **nexthop-group NH-1**
switch(config-nexthop-group-NH-1)# **ttl 32**
switch(config-nexthop-group-NH-1)# **show active**
 nexthop-group NH-1
   size 128
   ttl 32
switch(config-nexthop-group-NH-1)#`
```


The address is inserted
in the encapsulation source IP fields is specified by tunnel-source (Next-hop Group).

- These commands create **interface loopback 100**, assign
an IP address to the interface, then specifies that address as the tunnel source
for packets designated by next-hop-group
**NH-1**.
```
`switch(config)# **interface loopback 100**
switch(config-if-Lo100)# **ip address 10.1.1.1/32**
switch(config-if-Lo100)# **exit**
switch(config)# **nexthop-group NH-1**
switch(config-nexthop-group-NH-1)# **tunnel-source intf loopback 100**
switch(config-nexthop-group-NH-1)# **show active**
 nexthop-group NH-1
   size 256
   ttl 32
   tunnel-source intf Loopback100
switch(config-nexthop-group-NH-1)#`
```

Configure the nexthop
group tunnel to become active in the tunnel RIB only if a viable nexthop
group exists. A nexthop group becomes viable when it meets specific
reachability and programming criteria determined by one or more underlying
entries resolving in the Forwarding Information Base (FIB) and has
programmability. By default, IP tunnels become active even if no viable
nexthop group exists. To override this behavior, use the following
commands:
```
`switch(config)# **router general**
switch(config-router-general)# **tunnel nexthop-group unresolved invalid**
switch(config-router-general)#`
```


### Configuring IP-in-IP Encapsulation


Through IP-in-IP encapsulation, IP packets matching a static Nexthop-Group route encapsulate
within an IP-in-IP tunnel and forward.


This command configures a static Nexthop-Group route and an IP-in-IP Nexthop-Group
for IP-in-IP
encapsulation.
```
`switch(config)# **ip route 124.0.0.1/32 nexthop-group abc**
switch(config)# **nexthop-group abc type ip-in-ip**
switch(config-nexthop-group-abc)# **size 512**
switch(config-nexthop-group-abc)# **tunnel-source 1.1.1.1**
switch(config-nexthop-group-abc)# **entry 0 tunnel-destination 1.1.1.2**
switch(config-nexthop-group-abc)# **entry 1 tunnel-destination 10.1.1.1**
switch(config-nexthop-group-abc)# **ttl 64**
switch(config-nexthop-group-abc)#`
```


### Configuring the Group’s Size


The group’s size specifies the number of entries in the group. A group can contain up to
**256** entries, which is the default size. The
group’s size is specified by size (Nexthop Group).


This command configures the next-hop group **NH-1** to contain
**128**
entries.
```
`switch(config)# **nexthop-group NH-1**
switch(config-nexthop-group-NH-1)# **size 128**
switch(config-nexthop-group-NH-1)# **show active**
 nexthop-group NH-1
   size 128
   ttl 64
switch(config-nexthop-group-NH-1)#`
```


### Creating Next-hop Group Entries


Each entry specifies a next-hop address that is used to forward packets. A next-hop group
contains one entry statement for each next-hop address. The group size specifies the
number of entry statements the group may contain. Each entry statement is assigned
an index number to distinguish it from other entries within the group, and entry
index numbers range from zero to the group size minus one.


Next-hop group entries are configured by entry (Next-hop Group).


- These commands set the next-hop group size at four entries, then create three
entries. eos drops packets hashed to the fourth
entry.
```
`switch(config)# **nexthop-group NH-1**
switch(config-nexthop-group-NH-1)# **size 4**
switch(config-nexthop-group-NH-1)# **entry 0 tunnel-destination 10.13.4.4**
switch(config-nexthop-group-NH-1)# **entry 1 tunnel-destination 10.15.4.22**
switch(config-nexthop-group-NH-1)# **entry 2 tunnel-destination 10.15.5.37**
switch(config-nexthop-group-NH-1)# **show active**
 nexthop-group NH-1
   size 4
   ttl 64
   entry 0 tunnel-destination 10.13.4.4
   entry 1 tunnel-destination 10.15.4.22
   entry 2 tunnel-destination 10.15.5.37
switch(config-nexthop-group-NH-1)#`
```

- These commands configure a next-hop group with three IPv6 next-hop
entries.
```
`switch(config)# **nexthop-group nhg-v6-mpls type ip**
switch(config-nhg-v6-mpls)# **size 3**
switch(config-nhg-v6-mpls)# **entry 0 nexthop 2002::6401:1**
switch(config-nhg-v6-mpls)# **entry 1 nexthop 2002::6404:1**
switch(config-nhg-v6-mpls)# **entry 2 nexthop 2002::6404:2**
switch(config-nhg-v6-mpls)#`
```

- These commands configure an IPv4 route to point to the next-hop group
**nhg-v6-mpls**. (Both IPv4 routes and IPv6 routes
can point to this next-hop
group.)
```
`switch# **ip route 100.5.0.0/16 Nexthop-Group nhg-v6-mplsp**
switch#`
```


### Displaying Next-hop Groups


The show nexthop-group command displays a group configured parameters.


This command displays the properties of the nexthop group named
**NH-1**.
```
`switch> **show nexthop-group NH-1**
Name             Id       type     size   ttl    sourceIp
NH-1             4        ipInIp   256    64     0.0.0.0
switch>`
```


### Applying a Next-hop Group to a Static Route


The ip route nexthop-group associates a next-hop group with a specified
destination address and configures the encapsulation method for packets tunneled to
that address.


This command creates a static route in the default VRF, using the next-hop group of
**NH-1** to determine the next hop
address.
```
`switch(config)# **ip route 10.17.252.0/24 nexthop-group NH-1**
switch(config)#`
```


The **show ip route** command displays the routing table for a
specified VRF. Routes that utilize a next-hop group entry are noted with a route
type code of **NG**.


This command displays a routing table that contains a static route with its next-hop
specified by a next-hop group.


```
`switch> **show ip route**
Codes: C - connected, S - static, K - kernel,
       O - OSPF, IA - OSPF inter area, E1 - OSPF external type 1,
       E2 - OSPF external type 2, N1 - OSPF NSSA external type 1,
       N2 - OSPF NSSA external type2, B I - ibgp, B E - ebgp,
       R - RIP, I - ISIS, A B - bgp Aggregate, A O - OSPF Summary,
       NG - Nexthop Group Static Route

Gateway of last resort is not set

 C      10.3.3.1/32 is directly connected, Loopback0
 C      10.9.1.0/24 is directly connected, Ethernet51/3
 C      10.10.10.0/24 is directly connected, Ethernet51/1
 S      10.20.0.0/16 [20/0] via 10.10.10.13, Ethernet51/1
 C      10.10.11.0/24 is directly connected, Ethernet3
 NG     10.10.3.0/24 [1/0] via ng-test1, 5
 C      10.17.0.0/20 is directly connected, Management1
 S      10.17.0.0/16 [1/0] via 10.17.0.1, Management1
 S      10.18.0.0/16 [1/0] via 10.17.0.1, Management1
 S      10.19.0.0/16 [1/0] via 10.17.0.1, Management1
 S      10.20.0.0/16 [1/0] via 10.17.0.1, Management1
 S      10.22.0.0/16 [1/0] via 10.17.0.1, Management1

switch>`
```


### Support for IPv6 Link-Local Addresses in Next-hop Groups Entries


IPv6 Link-local addresses in Next-hop Groups entries support IPv6 link-local next-hops
belonging to a Next-hop Group. Only the MPLS Next-hop Group supports IPv6 and because of
this, IPv6 is limited to getting support only by the Nexthop Group of MPLS. An advantage
is that you can use these devices even when they are not configured with globally
routable IPv4 or IPv6 addresses.


#### Configuration


An MPLS next-hop group with IPv6 address now accepts an interface if the IPv6
address is a link-local. Note the use of percentages between the IPv6 address and the
interface.
```
`switch(config)# **nexthop-group nhg1 type mpls**
switch(config-nexthop-group-nhg1)# **entry 0 push label-stack 606789 nexthop fe80::fe80:2%Ethernet2**
switch(config-nexthop-group-nhg1)# **entry 1 push label-stack 204164 nexthop fe80::fe80:2%Ethernet3**`
```


#### Show commands


Use the **show nexthop-group** command to display the current
status of the nexthop-groups.
```
`switch# **show nexthop-group**
nhg1
  Id                1
  Type              mpls
  Size              12
  Entries (left most label is the top of the stack)
    0  push label-stack 606789   nexthop fe80::fe80:2
         Tunnel destination directly connected, Ethernet2
         00:d4:27:77:e9:77, Ethernet2
    1  push label-stack 204164   nexthop fe80::fe80:2
         Tunnel destination directly connected, Ethernet3
         00:79:21:32:0f:32, Ethernet3`
```


#### Limitations


Review the following limitations for the support of IPv6 link-local address in nexthop
group entries:

- Only the nexthop-group of MPLS supports an IPv6 address. Therefore, link-local
IPv6 addresses are only supported for this type of nexthop-group.

- Nexthop-groups are configured and exist in the default VRF. The link-local IPv6
addresses for nexthop-group entries can only be resolved for interfaces in the
default VRF.


## Nexthop Group commands


**Nexthop commands**

- entry (Next-hop Group)

- ip route nexthop-group

- nexthop-group

- size (Nexthop Group)

- ttl (Next-hop Group)

- tunnel-source (Next-hop Group)


**Nexthop Show Command**

- show nexthop-group


### entry (Next-hop Group)


The **entry** command defines a next-hop entry in the
***nexthop group*** configuration mode . Each next-hop entry
specifies a next-hop IP address for static routes to which the next-hop group is
assigned. The group size (size (Nexthop Group)) specifies the
quantity of entries a group contains. Each entry is created by an individual
command. Entries within a group are distinguished by an index number.


The **no entry** and **default entry** commands delete the specified nexthop group entry, as referenced by index number, by removing the corresponding **entry** statement from ***running-config.***


**Command Mode**


Nexthop-group Configuration


**Command Syntax**


entry
index
tunnel-destination
ipv4_address


no entry
index


default entry
index


**Parameters**

- **index** - Entry index. Values range from **0** to
**group-size – 1**.

- **ipv4_address** - Nexthop IPv4 address.

- **group-size** - the group’s entry capacity as
specified by the size (Nexthop Group) command.


**Example**


These commands sets the next-hop group size at four entries, then creates three
next-hop entries. eos drops packets hashed to the fourth
entry.
```
`switch(config)# **nexthop-group NH-1**
switch(config-nexthop-group-NH-1)# **size 4**
switch(config-nexthop-group-NH-1)# **entry 0 tunnel-destination 10.13.4.4**
switch(config-nexthop-group-NH-1)# **entry 1 tunnel-destination 10.15.4.22**
switch(config-nexthop-group-NH-1)# **entry 2 tunnel-destination 10.15.5.37**
switch(config-nexthop-group-NH-1)# **show active**
 nexthop-group NH-1
   size 4
   ttl 64
   entry 0 tunnel-destination 10.13.4.4
   entry 1 tunnel-destination 10.15.4.22
   entry 2 tunnel-destination 10.15.5.37
switch(config-nexthop-group-NH-1)#`
```


### ip route nexthop-group


The **ip route nexthop-group** command creates a static route.
The destination is a network segment. The next-hop address is one of the IP
addresses that comprise the specified next-hop group. Packets forwarded as a result
of this command are encapsulated as specified by the tunnel-type parameter of the
specified next-hop group.


When multiple routes exist to a destination prefix, the route with the lowest
administrative distance takes precedence. When a route created through this command
has the same administrative distance as another static route (ECMP), the route that
was created earliest has preference; ***running-config***
stores static routes in the order that they are created.


By default, the administrative distance assigned to static routes is
**1**. Assigning a higher administrative distance to a
static route configures it to be overridden by dynamic routing data. For example, a
static route with a distance value of **200** is overridden by
OSPF intra-area routes, which have a default distance of
**110**.


The **no ip route nexthop-group** and **default ip
route nexthop-group** commands delete the specified route by
removing the corresponding **ip route nexthop-group** command
from ***running-config***. **ip route
nexthop-group** statements for an IP address in multiple VRFs
must be removed separately.


A **no ip route** or **default ip route**
command without a next-hop parameter deletes all corresponding **ip route
nexthop-group** statements. Deleting a user-defined VRF also
deletes its static routes.


**Command Mode**


Global Configuration


**Command Syntax**


ip route [VRF_INST
dest_net
nexthop-group
nhgp_name
[dist][TAG_OPTION][RT_NAME]


no ip route [VRF_INST]
dest_net [nexthop-group
nhgroup_name][distance]


default ip route [VRF_INST] dest_net
 [nexthop-group
nhgroup_name][distance]


**Parameters**

- **VRF_INST**      Specifies the VRF instance being
modified.

- **no parameter**      Changes are made to the default VRF.

- **vrf**
**vrf_name**      Changes are made to the
specified VRF.

- **dest_net**      Destination IPv4 subnet (CIDR or
address-mask notation).

- **nhgp_name**      Name of next-hop group.

- **dist** Administrative distance assigned to route.
Options include:

- **no parameter**      Route assigned default administrative
distance of one.

- **1-255**      The administrative distance
assigned to route.

- **TAG_OPTION**      Static route tag. Options
include:

- **no parameter**      Assigns default static route tag of
**0**.

- **tag**
**t_value**       Static route tag value.
**t_value** ranges from
**0** to
**4294967295**.

- **RT_NAME**       Associates descriptive text to the
route. Options include:

- **no parameter**       No text is associated with the route.

- **name**
**descriptive_text**      The specified text
is assigned to the route.


**Related commands**


The **[ip route](/um-eos/eos-ipv4#xx1144639)** command creates a static route that
specifies the next-hop address without using next-hop groups.


**Example**


This command creates a static route in the default VRF, using the next-hop group of
**NH-1** to determine the next hop
address.
```
`switch(config)# **ip route 10.17.252.0/24 nexthop-group NH-1**
switch(config)#`
```


### nexthop-group


The **nexthop-group** command places the switch in
***nexthop-group*** configuration mode, through which next-hop
groups are created or modified. The command also specifies the tunnel protocol for
extracting payload from encapsulated packets that arrive through an IP address upon
which the group is applied.


A next-hop group is a data structure that defines a list of next-hop addresses and
the encapsulation process for packets routed to the specified address. The command
either accesses an existing ***nexthop group*** configuration or creates a
new group if it specifies a non-existent group. Supported tunnel protocols include
IP ECMP and IP-in-IP.


The ***nexthop-group*** configuration mode is not a group change mode;
***running-config*** is changed immediately
upon entering commands. Exiting the ***nexthop-group*** configuration mode
does not affect ***running-config***. The
**exit** command returns the switch to
***global*** configuration mode.


The **no nexthop-group** and **default
nexthop-group**commands delete previously configured commands in
the specified **nexthop-group** mode. When the command does not
specify a group, it removes all next-hop-groups. When the command specifies a tunnel
type without naming a group, it removes all next-hop-groups of the specified
type.


**Command Mode**


Global Configuration


****


Command Syntax


nexthop-group
group_name
 type
TUNNEL_TYPE


no nexthop-group
[group_name][type
TUNNEL_TYPE]


default nexthop-group
[group_name][typeTUNNEL_TYPE]


**Parameters**

- **group_name** Nexthop group name.

- **TUNNEL_TYPE** Tunnel protocol of the nexthop-group.
Options include:

- **ip** ECMP nexthop.

- **ip-in-ip** IP in IP tunnel.

- **gre** Encapsules the Layer 3 protocols
overs IP networks.

- **mpls-over-gre** Tunnels MPLS over a non-MPLS
network.

- entry Nexthop Group Entry
Configuration.

- size Nexthop Group Entry Size.

- tos Tunnel encapsulation IP type of
service.

- ttl  Tunnel encapsulation TTL value.

- tunnel-source Source Interface or
Address.


**commands Available in Nexthop-group Configuration Mode**

- entry (Next-hop Group)

- size (Nexthop Group)

- ttl (Next-hop Group)

- tunnel-source (Next-hop Group)


**Restrictions**


Tunnel type availability varies by switch platform.


**Examples**


- This command creates a nexthop group named **NH-1**
that specifies ECMP
nexthops.
```
`switch(config)# **nexthop-group NH-1 type ip**
switch(config-nexthop-group-NH-1)#`
```

- This command exits nexthop-group mode for the **NH-1**
nexthop
group.
```
`switch(config-nexthop-group-NH-1)# **exit**
switch(config)#`
```

- These commands creates a nexthop group **NH-2** of type
MPLS over
GRE.
```
`switch(config)# **nexthop-group NH-2 type mpls-over-gre**
switch(config-nexthop-group-NH-2)# **tunnel-source 11.1.1.1**
switch(config-nexthop-group-NH-2)# **ttl 32**
switch(config-nexthop-group-NH-2)# **tos 20**
switch(config-nexthop-group-NH-2)# **entry 0 push label-stack 16000 tunnel-destination 11.1.1.2**
switch(config)# **ip route 100.1.1.1/32 Nexthop-Group NH-2**

Counters for nexthop group may be enabled using the following command
switch(config)# **hardware counter feature nexthop**`
```


### show nexthop-group


The **show nexthop-group** command displays properties of the
specified nexthop group.


**Command Mode**


EXEC


**Command Syntax**


show nexthop-group
nhgroup_name [VRF_INST]


**Parameters**


- **nhgroup_name** Name of the group displayed by
command.

- **VRF_INST** Specifies the VRF instance for which data
is displayed.

- **no parameter**     Context-active VRF.

- **vrf**
**vrf_name** Specifies the name of VRF
instance. System default VRF is specified by
**default**.


**Related commands**


The show nexthop-group command places the switch in the
***nexthop-group*** configuration mode to create a new group or
modify an existing group.


**Example**


This command displays the nexthop group
information.
```
`switch(config)# **show nexthop-group**
  Id         107
  Type       mplsOverGre
  Size       1  (auto size enabled, programmed size 1)
  TTL        32
  Source IP  11.1.1.1
  Entries (left most label is the top of the stack)
    0  push label-stack 16000   tunnel-destination 11.1.1.2
         Tunnel destination directly connected, Ethernet1
         00:00:aa:aa:aa:aa, Ethernet1

With nexthop group counter enabled
switch(config)# **show nexthop-group**
  Id         1
  Type       mplsOverGre
  Size       1  (auto size enabled, programmed size 1)
  TTL        64
  Source IP  0.0.0.0
  Entries (left most label is the top of the stack)
    0  push label-stack 16000   tunnel-destination 1.1.1.2
         Tunnel destination directly connected, Ethernet1
         00:00:aa:aa:aa:aa, Ethernet1
         0 packets, 0 bytes

switch(config)#**show nexthop-group summary**
Number of Nexthop Groups configured: 1
Number of unprogrammed Nexthop Groups: 0

  Nexthop Group Type   Configured
-------------------- ------------
       MPLS over GRE            1

  Nexthop Group Size   Configured
-------------------- ------------
                   1            1`
```


### size (Nexthop Group)


The **size** command configures the quantity of next-hop
entries in the Nexthop-Group Configuration Mode . Each entry specifies a next-hop IP
address for static routes to assign to the group. Configure entries with the entry (Next-hop Group) command. The default size is
**256** entries.


The **no size** and **default size**
commands restore the size of the configuration mode nexthop group to the default
value of **256** by removing the corresponding
**size** command from
***running-config***.


**Command Mode**


Nexthop-group Configuration


**Command Syntax**


size
entry_size


no size
entry_size


default size
entry_size


**Parameter**


**entry_size** Group size (entries). Value ranges from
**1** to **255** with a
default value of **256**.


**Example**


This command configures the next-hop group **NH-1** to contain
**128**
entries.
```
`switch(config)# **nexthop-group NH-1**
switch(config-nexthop-group-NH-1)# **size 128**
switch(config-nexthop-group-NH-1)# **show active**
 nexthop-group NH-1
   size 128
   ttl 64
switch(config-nexthop-group-NH-1)#`
```


### ttl (Next-hop Group)


The **ttl** command specifies the number entered into the TTL
(time to live) encapsulation field of packets transmitted to the address designated
by the configuration mode next-hop group. The default TTL value is
**64**.


The **no ttl** and **default ttl**
commands restore the default TTL value written into TTL fields for the ***nexthop
group*** configuration mode by deleting the corresponding
**ttl** command from
***running-config***.


**Command Mode**


Nexthop-group Configuration


**Command Syntax**


ttl
hop_expiry


no ttl
hop_expiry


default ttl
hop_expiry


**Parameters**


**hop_expiry**     Period that the packet remains valid
(seconds or hops) Value ranges from **1** to
**64**.


**Restrictions**


This command is available only to Next-hop groups for tunnels of type
**IP-in-IP**, **GRE**,
**MPLS**, and **MPLS over
GRE**.


**Related commands**


The nexthop-group command places the
switch in the ***nexthop-group*** configuration mode.


**Examples**

- This command configures the **ttl** setting to
**32** for next-hop group
**NH-1**
packets.
```
`switch(config)# **nexthop-group NH-1**
switch(config-nexthop-group-NH-1)# **ttl 32**
switch(config-nexthop-group-NH-1)# **show active**
 nexthop-group NH-1
   size 128
   ttl 32
switch(config-nexthop-group-NH-1)#`
```

- This command restores the **no ttl** setting for
next-hop group **NH-1**
packets.
```
`switch(config-nexthop-group-NH-1)# **no ttl**
switch(config-nexthop-group-NH-1)# **show active nexthop-group NH-1**
   size 128
   ttl 64
switch(config-nexthop-group-NH-1)#`
```


### tunnel-source (Next-hop Group)


The **tunnel-source** command specifies the address that is
entered into the source IP address encapsulation field of packets that are
transmitted as designated by the ***nexthop group*** configuration mode .
The command may directly specify an IP address or specify an interface from which an
IP address is derived. The default source address IP address is
**0.0.0.0**.


The **no
tunnel-source** and **default
tunnel-source** commands remove the source IP address setting from
the configuration mode nexthop group by deleting the
**tunnel-source** command from
***running-config***.


**Command
Mode**


Nexthop-group Configuration


**Command
Syntax**


tunnel-source
SOURCE


no tunnel-source
SOURCE


default tunnel-source
SOURCE


**Parameters**

**SOURCE**
IP address or derivation interface. Options include:

- **ipv4_addr**      An IPv4 address.

- **intf ethernet**
**e_num**     Ethernet interface specified by
**e_num**.

- **intf loopback**
**l_num**     Loopback interface specified by
**l_num**.

- **intf management**
**m_num**     Management interface specified by
**m_num**.

- **intf port-channel**
**p_num**     Port-channel interface specified by
**p_num**.

- **intf vlan**
**v_num**     VLAN interface specified by
**v_num**.


**Restrictions**


This command is available only to Nexthop
groups for tunnels of type **ip-in-ip**.

**Related
commands**

The nexthop-group command places the switch in the
***nexthop-group*** configuration
mode.


**Example**

These commands create **interface
loopback 100**, assign an IP address to the interface, then
specifies that address as the tunnel source for packets designated by nexthop-group
**NH-1**.
```
`switch(config)# **interface loopback 100**
switch(config-if-Lo100)# **ip address 10.1.1.1/32**
switch(config-if-Lo100)# **exit**

switch(config)# **nexthop-group NH-1**
switch(config-nexthop-group-NH-1)# **tunnel-source intf loopback 100**
switch(config-nexthop-group-NH-1)# **show active nexthop-group NH-1**
   size 256
   ttl 64
   tunnel-source intf Loopback100
switch(config-nexthop-group-NH-1)# **show nexthop-group NH-1**
Name             Id       type     size   ttl    sourceIp
NH-1             2        ipInIp   256    64     10.1.1.1

switch(config-nexthop-group-NH-1)#`
```


### tunnel nexthop-group unresolved


The **tunnel nexthop-group unresolved** command in the Router General Configuration Mode
installs a nexthop-group tunnel only if a viable nexthop group exists. Using this command overrides the default behavior of creating a nexthop-group
tunnel even if no viable nexthop-group exists for the configuration.


The **no | default** versions of the command removes the configuration from the ***running-config*** on the switch.


**Command Mode**


Router General Configuration


**Command Syntax**


**tunnel nexthop-group unresolved invalid**


**no tunnel nexthop-group unresolved invalid**


**default tunnel nexthop-group unresolved invalid**


**Parameters**


- **tunnel** - Specifies using a tunnel for the configuration.

- **nexthop-group** - Applies the configuration to nexthop groups.

- **unresolved** - Specifies applying the command to unreachable destinations.

- **invalid** - Do not install the tunnel in the routing table.


**Example**


Use the following commands to apply the configuration to the switch:


```
`switch(config)# **router general**
switch(config-router-general)# **tunnel nexthop-group unresolved invalid**
switch(config-router-general)`
```
