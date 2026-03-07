<!-- Source: https://www.arista.com/um-eos/eos-ingress-and-egress-per-port-for-ipv4-and-ipv6-counters -->
<!-- Scraped: 2026-03-06T20:50:41.080Z -->

# Ingress and Egress Per-Port for IPv4 and IPv6 Counters


This feature supports per-interface ingress and egress packet and byte counters for IPv4
and IPv6.


This section describes Ingress and Egress per-port for IPv4 and IPv6 counters, including
configuration instructions and command descriptions.


Topics covered by this chapter include:


- Configuration

- Show commands

- Dedicated ARP Entry for TX IPv4 and IPv6 Counters

- Considerations


## Configuration


IPv4 and IPv6 ingress counters (count **bridged and routed**
traffic, supported only on front-panel ports) can be enabled and disabled using the
**hardware counter feature ip in**
command:


```
`**[no] hardware counter feature ip in**`
```


For IPv4 and IPv6 ingress and egress counters that include only
**routed** traffic (supported on Layer3 interfaces such as
routed ports and L3 subinterfaces only), use the following commands:


Note: The DCS-7300X, DCS-7250X, DCS-7050X, and DCS-7060X platforms
do not require configuration for IPv4 and IPv6 packet counters for only routed
traffic. They are collected by default. Other platforms (DCS-7280SR, DCS-7280CR, and
DCS-7500-R) need the feature enabled.


```
`**[no] hardware counter feature ip in layer3**`
```


```
`**[no] hardware counter feature ip out layer3**`
```


### hardware counter feature ip


Use the **hardware counter feature ip** command to enable ingress
and egress counters at Layer 3. The **no** and **default** forms of the command
disables the feature. The feature is enabled by default.


**Command Mode**


Configuration mode


**Command Syntax**


**hardware counter feature ip in|out layer3**


**no hardware counter feature ip in|out layer3**


**default hardware counter feature in|out layer3**


**Example**


This example enables ingress and egress ip counters for Layer 3.
```
`**switch(config)# hardware counter feature in layer3**`
```


```
`**switch(config)# hardware counter feature out layer3**`
```


## Show commands


Use the [**show interfaces counters ip**](/um-eos/eos-ethernet-ports#xzx_RbdvgrfI6B) command to
display IPv4, IPv6 packets, and octets.


**Example**


```
`switch# **show interfaces counters ip**
Interface   IPv4InOctets    IPv4InPkts     IPv6InOctets    IPv6InPkts
Et1/1            0               0               0               0
Et1/2            0               0               0               0
Et1/3            0               0               0               0
Et1/4            0               0               0               0
...
Interface  IPv4OutOctets  IPv4OutPkts    IPv6OutOctets   IPv6OutPkts
Et1/1            0               0               0               0
Et1/2            0               0               0               0
Et1/3            0               0               0               0
Et1/4            0               0               0               0
...`
```


You can also query the output from the **show interfaces counters
ip** command through snmp via the ARISTA-IP-MIB.


To clear the IPv4 or IPv6 counters, use the [**clear
counters**](/um-eos/eos-ethernet-ports#topic_dnd_1nm_vnb) command.


**Example**
```
`switch# **clear counters**`
```


## Dedicated ARP Entry for TX IPv4 and IPv6 Counters


IPv4/IPv6 egress Layer 3 (**hardware counter feature ip out layer3**)
counting on DCS-7280SR, DCS-7280CR, and DCS-7500-R platforms work based on ARP entry of
the next hop. By default, IPv4's next-hop and IPv6's next-hop resolve to the same MAC
address and interface that shared the ARP entry.


To differentiate the counters between IPv4 and IPv6, disable
**arp** entry sharing with the following command:


```
`**ip hardware fib next-hop arp dedicated**`
```




            Note: This command is required for IPv4 and IPv6 egress counters
                to operate on the DCS-7280SR, DCS-7280CR, and DCS-7500-R platforms.




## Considerations






                - Packet sizes greater than 9236 bytes are not counted by per-port IPv4 and IPv6 counters.

                - Only the DCS-7260X3, DCS-7368, DCS-7300, DCS-7050SX3, DCS-7050CX3, DCS-7280SR,
                    DCS-7280CR and DCS-7500-R platforms support the **hardware counter feature ip in** command.

                - Only the DCS-7280SR, DCS-7280CR and DCS-7500-R platforms support the **hardware counter feature ip [in|out] layer3** command.
