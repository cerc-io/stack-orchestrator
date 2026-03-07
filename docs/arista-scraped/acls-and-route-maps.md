<!-- Source: https://www.arista.com/um-eos/eos-acls-and-route-maps -->
<!-- Scraped: 2026-03-06T20:50:54.818Z -->

# ACLs and Route Maps


The switch uses rule-based lists to control packet access to ports and to select routes for redistribution to routing domains defined by dynamic routing protocols.


This section describes the construction of Access Control Lists (ACLs), prefix lists, and route maps and includes the following topics:


- Introduction

- Access Control Lists

- Service ACLs

- Sub-interface ACLs

- RACL Sharing on SVIs

- Route Maps

- Prefix Lists

- Port ACLs with User-Defined Fields

- ACL, Route Map, and Prefix List Commands


## Introduction


The following provides an introduction to Access Control Lists (ACL), Service ACLs, Route Maps, Prefix Lists, and Router Access Control List (RACL) Divergence:


The switch processes ACLs, Service ACLs, route maps, and prefix lists in order, beginning with the first rule and continuing until a match is found.


An ACL contains a list of rules that control the inbound and outbound flow of packets into Ethernet interfaces, subinterfaces, port-channel interfaces, or the switch control plane. The switch supports implementing various filtering criteria, including IP and MAC addresses and TCP/UDP ports, with include/exclude options without compromising its performance or feature set. Filtering syntax is the industry standard.


Note: EOS supports egress IPv4 and IPv6 Port Access Control Lists (PACLs) by default. To enable egress MAC PACLs, add the configuration to the current TCAM profile.


A Service ACL applies a control-plane process to control connections to, or packets processed by, the agent process.


A route map contains a list of rules that control the redistribution of IP routes into a protocol domain based on criteria such as route metrics, access control lists, next-hop addresses, and route tags. Additionally, route maps can modify route parameters during redistribution.


A prefix list contains a list of rules that defines route redistribution access for a specified IP address space. Route maps often use prefix lists to filter routes.


The RACL divergence optimizes hardware resource usage on each forwarding ASIC. EOS installs ACLs only on the hardware components corresponding to the member interfaces of the SVIs with an applied ACL, and saves hardware resources and scales the RACLs to a larger configuration.
Tip: Use the **show** commands to display the interface mapping, Ternary Content Addressable Memory (TCAM) entries, and TCAM utilization information.


## Access Control Lists


These sections describe access control lists:


- ACL Types

- ACL Configuration

- Applying ACLs


### ACL Types


The switch supports the following ACL types:


- **IPv4** matches on IPv4 source or destination addresses, with L4 modifiers including protocol, port number, IPsec tunnel interfaces, and DSCP value.

- **IPv6** matches on IPv6 source or destination addresses, with L4 modifiers including protocol, port number, or GRE tunnel interface.

- **Standard IPv4** matches only on source IPv4 addresses.

- **Standard IPv6** matches only on source IPv6 addresses.

- **MAC** matches on L2 source and destination addresses.


ACLs can also be made dynamic using **payload**, turning them into a User-Defined Field (UDF) alias for use in other ACLs.


#### ACL Structure


An ACL is an ordered list of rules that defines access restrictions for the entities (the control plane or an interface) to which it is applied. Route maps also use ACLs to select routes for redistribution into specified routing domains.


ACL rules specify the data to which packet contents are compared when filtering data.


- The interface forwards packets that match all commands in a permit rule.

- The interface drops packets that match all commands in a deny rule.

- The interface drops packets that do not match at least one rule.


Upon its arrival at an interface, the switch compares a packet’s fields to the first rule of the ACL applied to the interface. Packets that match the rule are forwarded (permit rule) or dropped (deny rule). The process continues whereby the switch compares packets that do not match the rule to the next rule in the list and continues until the packet either matches a rule or the rule list is exhausted. The interface drops packets that do not match a rule.


The sequence number designates the rule's placement in the ACL.


#### ACL Rules


The switch compares an ACL rule's command list to inbound and outbound packet fields. When all of a rule’s criteria match a packet’s contents, the interface performs the action specified by the rule.


The set of available commands depends on the ACL type and the specified protocol within the rule. The following is a list of commands available for supported ACL types:


##### IPv4 ACL Rule Parameters


All rules in IPv4 ACLs include the following criteria:


- **Protocol**: The packet’s IP protocol. Valid rule inputs include:


- Protocol name for a limited set of common protocols.

- Assigned protocol number for all IP protocols.

- **Source Address**: The packet’s source IPv4 address. Valid rule inputs include:


- A subnet address (CIDR or address mask). Discontiguous masks are supported.

- A host IP address (dotted decimal notation.)

- Using ***any*** to denote that the rule matches all source addresses.

- **Destination Address**: The packet’s destination IP address. Valid rule inputs include:


- A subnet address (CIDR or address mask). Discontiguous masks are supported.

- A host IP address (dotted decimal notation.)

- Using ***any*** to denote that the rule matches all destination addresses.


All rules in IPv4 ACLs ***may*** include the following criteria:


- **Fragment**: Rules filter on the fragment bit.

- **Time-to-live**: Compares the packet TTL (time-to-live) value to a specified value and is valid in ACLs applied to the control plane. The validity of ACLs applied to the data plane varies by switch platform. Comparison options include:


- **Equal:** Packets match if the packet value equals the statement value.

- **Greater than:** Packets match if the packet value is greater than the statement value.

- **Less than:** Packets match if the packet value is less than the statement value.

- **Not equal:** Packets match if the packet value does not equal the statement value.


The availability of the following optional criteria depends on the specified protocol:


- **Source Ports / Destination Ports**: A rule filters on ports when the specified protocol supports IP address-port combinations. Rules provide one of these port filtering values:


- Using ***any*** denotes that the rule matches all ports.

- A list of ports that matches the packet port. The maximum list size is 10 ports.

- Negative port list. The rule matches any port not in the list. The maximum list size is 10 ports.

- Integer (lower bound): The rule matches any port with a number larger than the integer.

- Integer (upper bound): The rule matches any port with a number smaller than the integer.

- Range integers: The rule matches any port whose number is between the integers.

- **Flag bits**: Rules filter TCP packets on flag bits.

- **Message type**: Rules filter ICMP type or code.

- **Tracked**: Matches packets in existing ICMP, UDP, or TCP connections and is valid in ACLs applied to the control plane. The validity of ACLs applied to the data plane varies by switch platform.


##### IPv6 ACL Rule Parameters


Note: When calculating the size of ACLs, be aware that Arista switches install four rules in every IPv6 ACL so that ICMPv6 neighbor discovery packets bypass the default drop rule.


All rules in IPv6 ACLs include the following criteria:


- **Protocol**: All rules filter on the packet’s IP protocol field. Rule input options include:


- Protocol name for a limited set of common protocols.

- Assigned protocol number for all IP protocols.

- **Source Address**: The packet’s source IPv6 address. Valid rule inputs include:


- An IPv6 prefix (CIDR). Discontiguous masks are supported.

- A host IP address (dotted decimal notation).

- Using ***any*** to denote that the rule matches all addresses.

- **Destination Address**: The packet’s destination IP address. Valid rule inputs include:


- A subnet address (CIDR or address mask). Discontiguous masks are supported.

- A host IP address (dotted decimal notation).

- Using ***any*** to denote that the rule matches all addresses.


All rules in IPv6 ACLs ***may*** include the following criteria:


- **Fragment**: Rules filter on the fragment bit.

- ***HOP***     Compares the packet’s hop-limit value to a specified value. Comparison options include:


- **eq**: Packets match if the hop-limit value equals the statement value.

- **gt**: Packets match if the hop-limit value is greater than the statement value.

- **lt**: Packets match if the hop-limit value is less than the statement value.

- **neq**: Packets match if the hop-limit value is not equal to the statement value.


The availability of the following optional criteria depends on the specified protocol:


- **Source Ports / Destination Ports**: A rule filters on ports when the specified protocol supports IP address-port combinations. Rules provide one of these port filtering values:


- Using ***any*** denotes that the rule matches all ports.

- A list of ports that matches the packet port. The maximum list size is 10 ports.

- Negative port list. The rule matches any port not in the list. The maximum list size is 10 ports.

- Integer (lower bound): The rule matches any port with a number larger than the integer.

- Integer (upper bound): The rule matches any port with a number smaller than the integer.

- Range integers: The rule matches any port whose number is between the integers.

- **Flag bits**: Rules filter TCP packets on flag bits.

- **Message type**: Rules filter ICMP type or code.

- **Tracked**: Matches packets in existing ICMP, UDP, or TCP connections and is valid in ACLs applied to the control plane. The validity of ACLs applied to the data plane varies by switch platform.


##### Standard IPv4 and IPv6 ACL Rule Parameters


Note: When calculating the size of ACLs, be aware that Arista switches install four rules in every IPv6 ACL so that ICMPv6 neighbor discovery packets bypass the default drop rule.


Standard ACLs filter only on the source address.


##### MAC ACL Rule Parameters


MAC ACLs filter traffic on a packet’s layer 2 header. Criteria that MAC ACLs use to filter packets include:


- **Source Address** and **Mask**: The packet’s source MAC address. Valid rule inputs include:


- MAC address range (address mask in 3x4 dotted hexadecimal notation).

- Using ***any*** to denote that the rule matches all source addresses.

- **Destination Address** and **Mask**: The packet’s destination MAC address. Valid rule inputs include:


- MAC address range (address mask in 3x4 dotted hexadecimal notation).

- Using ***any*** to denote that the rule matches all destination addresses.

- **Protocol**: The packet’s protocol as specified by its EtherType field contents. Valid inputs include:


- Protocol name for a limited set of common protocols.

- Assigned protocol number for all protocols.


#### Creating and Modifying Lists


The switch provides configuration modes for creating and modifying ACLs. The command that enters an ACL configuration mode specifies the name of the list that the mode modifies. When the configuration mode is exited, the switch saves the list to the running configuration.


- ACLs are created and modified in ACL configuration mode.

- Standard ACLs are created and modified in Standard-ACL-configuration mode.

- MAC ACLs are created and modified in MAC-ACL-configuration mode.


Lists created in one mode cannot be modified in any other mode.


A sequence number determines a rule's position within a list. New rules are inserted into a list based on their sequence numbers. You can reference a rule's sequence number to delete it from a list.


ACL Configuration describes procedures for configuring ACLs.


#### Implementing Access Control Lists


Implement an Access Control List (ACL) by assigning the list to an Ethernet interface, subinterface, port channel interface, or control plane. The switch assigns a default ACL to the control plane unless the configuration contains a valid control-plane ACL assignment statement. Ethernet and port-channel interfaces are not assigned an ACL by default. Apply standard ACLs to interfaces in the same manner as other ACLs.


IPv4 and MAC ACLs are separately applied for inbound and outbound packets. An interface or subinterface can be assigned multiple ACLs, with a limit of one ACL per packet direction per ACL type. A subset of all available switches supports Egress ACLs. The control plane does not support egress ACLs.


Applying ACLs describes procedures for applying ACLs to interfaces or the control plane.


#### ACL Rule Tracking


ACL rule tracking determines how ACL rules impact traffic on the interfaces where those rules are applied. ACLs provide two tracking mechanisms:


- **ACL logging**: Logs a syslog entry when a packet matches specified ACL rules.

- **ACL counters**: ACL counters increment when a packet matches a rule in specified ACLs.


##### ACL Logging


ACL rules provide a **log** option that produces a log message when a packet matches the rule. ACL logging creates a syslog entry when a packet matches an ACL rule where logging is enabled. Packets that match a logging-enabled ACL rule are copied to the CPU by the hardware. These packets trigger the creation of a syslog entry. The information provided in the entry depends on the ACL type or the protocol specified by the ACL. The system applies hardware rate limiting to packets written to the CPU, which prevents potential Denial-of-Service attacks. The logging rate is also limited in software to avoid creating syslog lists that are too large for human operators to use in practical ways.


ACL Rule Tracking Configuration describes procedures for configuring and enabling ACL logging.


##### ACL Counters


The system assigns an ACL counter to each ACL rule. The activity of the ACL counters for rules within a list depends on the list’s counter state. When the list is in a counting state, the ACL counter of a rule increments when the rule matches a packet. When the list is in a non-counting state, the counter does not increment. A list’s counter state applies to all rules in the ACL. The default state for new ACLs is non-counting.


The system maintains the values of the counters for all rules in the list when an ACL changes from a counting state to a non-counting state or is no longer applied to any interfaces that increment counters. The counters do not reset. When the ACL returns to counting mode or is applied to an interface that increments counters, the counter operation continues from its last value.


Counters never decrement and are reset only through CLI commands.


ACL Rule Tracking Configuration describes procedures for configuring and enabling ACL counters.


#### Egress ACL Counters


Egress ACL counters count the number of packets matching rules associated with egress ACLs applied to various interfaces in a switch. 7050 and 7060 series switches maintain these counters for every TCAM rule. On these platforms, commands such as **show platform trident tcam**, **show platform trident counters**, and **show ip access-list** always display packet counters greater than zero.


Other switches do not enable counters by default. You must configure counters for each ACL. The **show hardware counter** and **show ip access-list** commands display the counters.


##### Configuring Egress ACL Counters


7050 and 7060 series switches enable egress ACL counters and do not require configuration.


For other platforms, to enable egress ACL counters for a specific ACL, use the **counters per-entry** command in the ACL's configuration mode.


**Example**


As shown in the following example, configure the **counters per-entry** command in the ACL configuration mode.


```
`switch(config)# **ip access-list acl1**
switch(config-acl-acl1)# **counters per-entry**`
```


Enabling Egress Counters Globally

7050 and 7060 series switches enable egress counters.


For other switches, enable IPv4 and IPv6 egress ACL counters in the global configuration mode using the **hardware counter feature acl out** command.


**Example**


The following examples show how to enable IPv4 and IPv6 egress ACL counters:

```
`switch(config)# **hardware counter feature acl out ipv4**
switch(config)#`
```


```
`switch(config)# **hardware counter feature acl out ipv6**
switch(config)#`
```


Disabling Egress Counters Globally

For 7050 and 7060 series switches, egress counters cannot be disabled.


For other switches, disable IPv4 and IPv6 egress ACL counters in the global configuration mode by using the **hardware counter feature acl out** command.


The following examples show how to disable IPv4 and IPv6 egress ACL counters:


```
`switch(config)# **no hardware counter feature acl out ipv4**
switch(config)#`
```


```
`switch(config)# **no hardware counter feature acl out ipv6**
switch(config)#`
```


Egress Counter Roll Over in the Global Mode

The counters roll over when the counter value for an ACL rule exceeds **2^64** (2 to the power of 64).


**Example**


In the following example, the **hardware counter feature acl ipv6 out** command is configured using units and packets.


```
`switch(config)# **hardware counter feature acl ipv6 out units packets**
switch(config)#`
```


The **clear ip access-lists counters** command clears the counters for all of the IPv4 ACLs or a specific IPv4 ACL, either globally or per CLI session.


**Example**


In the following example the ACL list named **red** is selected.


```
`switch(config)# **clear ip access-list counters red session**
switch(config)#`
```


The IPv6 egress ACL counters do not work in unshared mode.


**Example**


Use the **hardware access-lists resource sharing vlan ipv6 out** command to enable egress IPv6 ACL sharing.


```
`switch(config)# **hardware access-list resource sharing vlan ipv6 out**
switch(config)#`
```


The **clear ipv6 access-list counters** command clears the counters for all of the IPv6 ACLs or a specific IPv6 ACL, either globally or per CLI session.


**Example**


In the following example the ACL list named **green** is selected.


```
`switch(config)# **clear ipv6 access-list counters green session**
switch(config)#`
```


##### Displaying Egress ACL Counters


Use the following **show** commands to display information on Egress ACL Counters.


Use the **show ip access-lists** command to display all the IPv4 ACLs, or a specific IPv4 ACL configured in a switch. The output contains details such as ACL rules and counter values for each rule.

```
`switch(config)# **show ip access-list acl1**
IP Access List acl1
        counter per-entry
        10 deny ip 11.1.1.0/24 any dscp af11
        20 deny ip any any [match 39080716, 0:00:00 ago]

        Total rules configured: 2
        Configured on Ingress: Et2/1
        Active on     Ingress: Et2/1`
```


Use the **show ipv6 access-lists** command to display all the IPv6 ACLs or a specific IPv6 ACL configured in a switch. The output contains details such as rules in an ACL and respective counter values with each rule.

```
`switch(config)# **show ipv6 access-list acl1**
IPV6 Access List acl1
        counter per-entry
        10 permit ipv6 any any [match 3450000, 0:00:10 ago]
        20 deny ipv6 any any

        Total rules configured: 2
        Configured on Ingress: Et2/1
        Active on     Ingress: Et2/1`
```


The counter name **EgressAclDropCounter** in the output of this show command signifies the aggregate counter value for the remaining egress IPv4 ACL. In this example, the deny rules, with per-rule counters, do not allocate. No per-rule counters are allocated if you do not configure the **counter per-entry** parameter for the respective ACL.

```
`switch(config)# **show hardware counter drop**
Summary:
Total Adverse (A) Drops: 0
Total Congestion (C) Drops: 0
Total Packet Processor (P) Drops: 250
Type Chip CounterName : Count : First Occurrence : Last Occurrence
-------------------------------------------------------------------------------
P Fap0 **EgressAclDropCounter** : 250 : 2015-11-11 22:39:02 : 2015-11-11 22:51:44`
```


### ACL Configuration


You create and modify Access Control Lists (ACLs) in an ACL-configuration mode. You can edit a list only in the mode where you created it. The switch provides five configuration modes for creating and modifying access control lists:


- **ACL configuration mode** for IPv4 access control lists.

- **IPv6-ACL configuration mode** for IPv6 access control lists.

- **Std-ACL configuration mode** for Standard IPv4 access control lists.

- **Std-IPv6-ACL configuration mode** for Standard IPv6 access control lists.

- **MAC-ACL configuration mode** for MAC access control lists.


These sections describe the creation and modification of ACLs:


- Managing ACLs

- Modifying an ACL

- ACL Rule Tracking Configuration

- Displaying ACLs

- Configuring Per-Port Per-VLAN QoS

- Displaying Per-Port Per-VLAN QoS

- Configuring Mirror Access Control Lists


#### Managing ACLs


##### Creating and Opening a List


To create an ACL, enter one of the following commands, followed by the name of the list:


- **ip access-list** for IPv4 ACLs.

- **ipv6 access-list** for IPv6 ACLs.

- **ip access-list standard** for standard IPv4 ACLs.

- **ipv6 access-list standard** for standard IPv6 ACLs.

- **mac access-list** for MAC ACLs.


The switch enters the appropriate ACL Configuration Mode for the list. When adding the name of an existing ACL to the command, subsequent commands edit that list (see Modifying an ACL for additional information).


##### Examples


- This command places the switch in ACL Configuration Mode to create an ACL named **test1**.

```
`switch(config)# **ip access-list test1**
switch(config-acl-test1)#`
```

- This command places the switch in ACL Configuration Mode to create a Standard ACL named **stest1**.

```
`switch(config)# **ip access-list standard stest1**
switch(config-std-acl-stest1)#`
```

- This command places the switch in ACL Configuration Mode to create an MAC ACL named **mtest1**.

```
`switch(config)# **mac access-list mtest1**
switch(config-mac-acl-mtest1)#`
```


##### Saving List Modifications


ACL Configuration Modes are group-change modes. Changes made in a group-change mode are saved when exiting the mode. To discard changes, use the **abort** command instead of **exit**.


##### Examples


- Use the following commands to configure the first three rules into a new ACL.

```
`switch(config-acl-test1)# **permit ip 10.10.10.0/24 any**
switch(config-acl-test1)# **permit ip any host 10.20.10.1**
switch(config-acl-test1)# **deny ip host 10.10.10.1 host 10.20.10.1**`
```

- To view the edited list, use the **show** command.


```
`switch(config-acl-test1)# **show**
IP Access List test1
        10 permit ip 10.10.10.0/24 any
        20 permit ip 10.30.10.0/24 host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any`
```


Because EOS has not saved the changes, the ACL remains empty, as displayed by **show ip access-lists**.


```
`switch(config-acl-test1)# **show ip access-lists test1**
switch(config-acl-test1)#`
```


Use the **exit** command to save all current changes to the ACL and exit the ACL configuration mode.


```
`switch(config-acl-test1)# **exit**
switch(config)# **show ip access-lists test1**
IP Access List test1
        10 permit ip 10.10.10.0/24 any
        20 permit ip 10.30.10.0/24 host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any

Total rules configured: 4
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1`
```


To apply the ACL **test1** on an interface, **Ethernet1/1**, for example, and on the ingress direction, use the following command:

```
`switch(config)# **int et1/1**
switch(config-if-Et1/1)# **ip access-group test1 in**`
```


Use the **exit** command to save all changes to the Ethernet interface and exit the interface configuration mode.

```
`switch(config-if-Et1/1)# **exit**
switch(config)#
switch(config)# **show ip access-lists test1**
IP Access List test1
        10 permit ip 10.10.10.0/24 any
        20 permit ip 10.30.10.0/24 host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any

Total rules configured: 4
Configured on Ingress: Et1/1
Active on     Ingress: Et1/1`
```


##### Discarding List Changes


The **abort** command exits ACL Configuration mode without saving pending changes.


##### Examples


- The following commands enter the first three rules into a new ACL.

```
`switch(config-acl-test1)# **permit ip 10.10.10.0/24 any**
switch(config-acl-test1)# **permit ip any host 10.20.10.1**
switch(config-acl-test1)# **deny ip host 10.10.10.1 host 10.20.10.1**`
```

- To view the edited list, use the **show** command.


```
`switch(config-acl-test1)# **show**
IP Access List test1
        10 permit ip 10.10.10.0/24 any
        20 permit ip 10.30.10.0/24 host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any`
```


To discard the changes, use the **abort** command. If the ACL existed before entering the ACL Configuration Mode, the **abort** command restores the version that existed before entering the ACL Configuration Mode. Otherwise, the **show ip access-lists** command displays no output.


```
`switch(config-acl-test1)# **abort**
switch(config)#`
```


#### Modifying an ACL


An existing ACL, including those applied to interfaces, can be modified by entering the appropriate configuration mode for the ACL as described in Creating and Opening a List. By default, while modifying an ACL, all traffic is blocked on any interface using the ACL.


##### Permit All Traffic During ACL Update


To avoid packet loss and interference with features like routing and dynamic NAT, you can configure the following switches to permit **all** traffic on Ethernet and VLAN interfaces during ACL modifications:


- 7050X

- 7060X

- 7150

- 7250X

- 7280

- 7280R

- 7300X

- 7320X

- 7500 series switches


Use the **hardware access-list update default-result permit** command to configure the preceding switches.


The following commands add **`deny`** rules to the appropriate ACL:


- **deny (IPv4 ACL)** adds a deny rule to an IPv4 ACL.

- **deny (IPv6 ACL)** adds a deny rule to an IPv6 ACL.

- **deny (Standard IPv4 ACL)** adds a deny rule to an IPv4 standard ACL.

- **deny (Standard IPv6 ACL)** adds a deny rule to an IPv6 standard ACL.

- **deny (MAC ACL)** adds a deny rule to a MAC ACL.


The following commands add **`permit`** rules to the appropriate ACL:


- **permit (IPv4 ACL)** adds a permit rule to an IPv4 ACL.

- **permit (IPv6 ACL)** adds a permit rule to an IPv6 ACL.

- **permit (Standard IPv4 ACL)** adds a permit rule to an IPv4 standard ACL.

- **permit (Standard IPv6 ACL)** adds a permit rule to an IPv6 standard ACL.

- **permit (MAC ACL)** adds a permit rule to a MAC ACL.


##### Adding a Rule


To append a rule to the end of a list, enter the rule without a sequence number while in ACL configuration mode for the list. The switch computes the new rule’s sequence number by adding **10** to the last rule’s sequence number.


##### Examples


- The following command configures the switch to permit all traffic during ACL modifications on interfaces using the ACL. The rules in modified ACLs go into effect after exiting ACL configuration mode and after populating the ACL rules in hardware.

```
`switch(config)# **hardware access-list update default-result permit**`
```

- The following commands enter the first three rules into a new ACL.

```
`switch(config-acl-test1)# **permit ip 10.10.10.0/24 any**
switch(config-acl-test1)# **permit ip any host 10.20.10.1**
switch(config-acl-test1)# **deny ip host 10.10.10.1 host 10.20.10.1**`
```

- To view the edited list, use the **show** command.


```
`switch(config-acl-test1)# **show**
IP Access List test1
        10 permit ip 10.10.10.0/24 any
        20 permit ip any host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1`
```

- The following command appends a rule to the ACL. The new rule’s sequence number is **40**.

```
`switch(config-acl-test1)# **permit ip any any**
switch(config-acl-test1)# **show**
IP Access List test1
        10 permit ip 10.10.10.0/24 any
        20 permit ip any host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any`
```


##### Inserting a Rule


To insert a rule into an ACL, enter the rule with a sequence number between the existing rules’ numbers.


##### Example


The following command inserts a rule between the first two by assigning the sequence number **15**.

```
`Switch(config-acl-test1)# **15 permit ip 10.30.10.0/24 host 10.20.10.1**
Switch(config-acl-test1)# **show**
IP Access List test1
        10 permit ip 10.10.10.0/24 any
        15 permit ip 10.30.10.0/24 host 10.20.10.1
        20 permit ip any host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any`
```


##### Deleting a Rule


To remove a rule from the current ACL, perform one of these commands:


- Enter **no**, followed by the sequence number to delete a rule.

- Enter **no**, followed by the actual rule to delete it.

- Enter **default**, followed by the actual rule to delete it.


##### Examples


- These equivalent commands remove rule **20** from the list.

```
`switch(config-acl-test1)# **no 20**
switch(config-acl-test1)# **no permit ip any host 10.20.10.1**
switch(config-acl-test1)# **default permit ip any host 10.20.10.1**`
```

- This ACL results from entering one of the preceding commands.


```
`switch(config-acl-test1)# **show**
ip access list test1
        10 permit ip 10.10.10.0/24 any
        15 permit ip 10.30.10.0/24 host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any`
```


##### Resequencing Rule Numbers


Sequence numbers determine the order of the rules in an ACL. After editing a list and deleting existing rules while inserting new rules between existing rules, the sequence number distribution may not be uniform. Resequencing rule numbers changes the sequence number of rules to provide a constant difference between adjacent rules. The **resequence (ACLs)** command adjusts the sequence numbers of ACL rules.


##### Example


The **resequence (ACLs)** command renumbers rules in the test1 ACL. The sequence number of the first rule is **100**; subsequent rule numbers are incremented by **20**.

```
`switch(config-acl-test1)# **show**
IP Access List test1
        10 permit ip 10.10.10.0/24 any
        25 permit ip any host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        50 permit ip any any
        90 remark end of list
switch(config-acl-test1)# **resequence 100 20**
switch(config-acl-test1)# **show**
IP Access List test1
        100 permit ip 10.10.10.0/24 any
        120 permit ip any host 10.20.10.1
        140 deny ip host 10.10.10.1 host 10.20.10.1
        160 permit ip any any
        180 remark end of list`
```


#### ACL Rule Tracking Configuration


ACL Rules provide a **log** option that produces a syslog message about the packets matching a desired packet. ACL Logging creates a syslog entry when a packet matches an ACL rule with logging enabled.


##### Example


The following command creates an ACL Rule with logging enabled.

```
`switch(config-acl-test1)# **15 permit ip 10.30.10.0/24 host 10.20.10.1 log**
switch(config-acl-test1)#`
```


The format of the generated Syslog message depends on the ACL type and the specified protocol:


- Messages generated by a TCP or UDP packet matching an IP ACL:

**IPACCESS: list** *acl   intf*  *filter* *protocol* *src-ip*(*src_port*)  **->**   *dst-ip*(*dst_port*)

- Messages generated by ICMP packets matching an IP ACL:

**IPACCESS: list** *acl   intf* *filter* **icmp** *src-ip*(*src-port*)   **->**   *dst-ip*(*dst-port*) **type=** *n* **code=** *m*

- Messages generated by all other IP packets matching an IP ACL:

**IPACCESS: list** *acl   intf   filter* *protocol* *src-ip* **->** *dst-ip*

- Messages generated by packets matching a MAC ACL:

**MACACCESS: list** *acl   intf* *filter* *vlan* *ether* *src_mac* **->**   *dst_mac*

- Messages generated by a TCP or UDP packet matching a MAC ACL:

**MACACCESS: list** *acl  intf* *filter* *vlan* *ether* *ip-prt   src-mac* *src-ip* **:** *src-prt* **->** *dst-mac* *dst-ip* **:** *dst-prt*

- Messages generated by any other IP packet matching a MAC ACL:

**MACACCESS: list** *acl  intf* *filter**vlan* *ether* *src_mac* *src_ip* **->** *dst_mac* *dst_ip*


Variables in the Syslog messages display the following values:


- **acl** - Specifies the name of the ACL.

- **intf** - Specifies the name of the interface receiving the packet.

- **filter** - Specifies the action triggered by the ACL as **denied** or **permitted**.

- **protocol** - Specifies the IP protocol specified by the packet.

- **vlan** - Specifies the number of the VLAN receiving the packet.

- **ether** - Specifies the EtherType protocol specified by the packet.

- **src-ip** and **dst-ip** - Specifies the source and destination IP addresses.

- **src-prt** and **dst-prt** - Specifies the source and destination ports.

- **src-mac** and **dst-mac** - Specifies the source and destination MAC addresses.


ACLs provide a command that configures as counter state as counting or non-counting. The counter state applies to all rules in the ACL. The initial state for new ACLs defaults to non-counting.


The **counters per-entry (ACL configuration modes)** command places the ACL in counting mode.


The following command places the configuration mode ACL in counting mode.

```
`switch(config-acl-test1)# **counters per-entry**
switch(config-acl-test1)# **exit**
switch(config-acl-test1)# **show ip access-list test1**
IP Access List test1
        counters per-entry
        10 permit ip 10.10.10.0/24 any
        20 permit ip any host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any
        50 remark end of list
Total rules configured: 5
        Configured on Ingress: Et1
        Active on     Ingress: Et1`
```


The **clear ip access-lists counters** and **clear ipv6 access-lists counters** commands set the IP access list counters to zero for the specified IP access list.


The following command clears the ACL counter for the **test1** ACL.

```
`switch(config)# **clear ip access-lists counters test1**
switch(config)#`
```


#### Displaying ACLs


Display ACLs using the **show running-config** command. The **show ip access-lists** command also displays ACL rosters and contents as specified by command parameters.


When editing an ACL, the **show (ACL configuration modes)** command displays the current or pending list as specified by command parameters.


##### Displaying a List of ACLs


To display the roster of ACLs on the switch, use the **show [ip | ipv6 | mac] access-lists** command with the **summary** option.


##### Example


The following command lists the available IPv4 access control lists.

```
`switch(config)# **show ip access-lists summary**
IPV4 ACL default-control-plane-acl
        Total rules configured: 12
        Configured on: control-plane
        Active on    : control-plane

IPV4 ACL list2
        Total rules configured: 3

IPV4 ACL test1
        Total rules configured: 6

IPV4 ACL test_1
        Total rules configured: 1

IPV4 ACL test_3
        Total rules configured: 0
switch(config)#`
```


##### Displaying Contents of an ACL


These commands display ACL contents.


- **show access-lists**

- **show ip access-lists**

- **show ipv6 access-lists**

- **show mac access-lists**


Each command can display the contents of one ACL or of all ACLs of the type specified by the command:


- To display the contents of one ACL, enter **show** **acl_type** **access-lists** followed by the name of the ACL. The **acl_type** can be **ip, ipv6, mac** or null.

- To display the contents of all ACLs on the switch, enter the command without any options.


ACLs in counting mode display the number of inbound packets matching each rule in the list and the elapsed time since the last match.


##### Examples


- The following command displays the rules in the **default-control-plane-acl IP ACL**, configuration, and status.

```
`switch# **show ip access-lists default-control-plane-acl**
IP Access List default-control-plane-acl [readonly]
        counters per-entry
        10 permit icmp any any
        20 permit ip any any tracked [match 1725, 0:00:00 ago]
        30 permit ospf any any
        40 permit tcp any any eq ssh telnet www snmp bgp https
        50 permit udp any any eq bootps bootpc snmp [match 993, 0:00:29 ago]
        60 permit tcp any any eq mlag ttl eq 255
        70 permit udp any any eq mlag ttl eq 255
        80 permit vrrp any any
        90 permit ahp any any
        100 permit pim any any
        110 permit igmp any any [match 1316, 0:00:23 ago]
        120 permit tcp any any range 5900 5910
Total rules configured: 12
             Configured on Ingress: control-plane(default VRF)
             Active on     Ingress: control-plane(default VRF)`
```

- The following command displays the rules, configuration, and status of all the IP ACLs on the switch.

```
`switch# **show ip access-lists**
IP Access List default-control-plane-acl [readonly]
        counters per-entry
        10 permit icmp any any
        20 permit ip any any tracked [match 1371, 0:00:00 ago]
        30 permit ospf any any
        40 permit tcp any any eq ssh telnet www snmp bgp https
        50 permit udp any any eq bootps bootpc snmp
        60 permit tcp any any eq mlag ttl eq 255
        70 permit udp any any eq mlag ttl eq 255
        80 permit vrrp any any
        90 permit ahp any any
        100 permit pim any any
        110 permit igmp any any [match 1316, 0:00:23 ago]
        120 permit tcp any any range 5900 5910

        Total rules configured: 12
        Configured on Ingress: control-plane(default VRF)
        Active on     Ingress: control-plane(default VRF)

IP Access List list2
        10 permit ip 10.10.10.0/24 any
        20 permit ip 10.30.10.0/24 host 10.20.10.1
        30 permit ip any host 10.20.10.1
        40 deny ip host 10.10.10.1 host 10.20.10.1
        50 permit ip any any

        Total rules configured: 5
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1


IP Access List test1
switch(config)#`
```


##### Displaying ACL Modifications


While editing an ACL in ACL Configuration Mode, the show command provides options for displaying ACL contents.


- To display the list, as modified in ACL configuration mode, enter **show** or **show pending**.

- To display the list, as stored in ***running-config***, enter **show active**.

- To display differences between the pending list and the stored list, enter **show diff**.


##### Examples


The examples in this section display previously configured ACL commands.


The configuration stores these parameters:


```
`10 permit ip 10.10.10.0/24 any
20 permit ip any host 10.21.10.1
30 deny ip host 10.10.10.1 host 10.20.10.1
40 permit ip any any
50 remark end of list`
```


The current edit session removed this command, and the change not yet stored to the ***running-config***:


```
`20 permit ip any host 10.21.10.1`
```


The current edit session added these commands to the ACL, and the change not yet stored to the ***running-config***:


```
`20 permit ip 10.10.0.0/16 any
25 permit tcp 10.10.20.0/24 any
45 deny pim 239.24.124.0/24 10.5.8.4/30`
```


The following command displays the pending ACL as modified in the ACL Configuration Mode.

```
`switch(config-acl-test_1)# **show pending**
IP Access List test_1
        10 permit ip 10.10.10.0/24 any
        20 permit ip 10.10.0.0/16 any
        25 permit tcp 10.10.20.0/24 any
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any
        45 deny pim 239.24.124.0/24 10.5.8.4/30
        50 remark end of list`
```


The following command displays the ACL as stored in the configuration.

```
`switch(config-acl-test_1)# **show active**
IP Access List test_1
        10 permit ip 10.10.10.0/24 any
        20 permit ip any host 10.21.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
        40 permit ip any any
        50 remark end of list`
```


The following command displays the difference between the saved and modified ACLs.


- A plus sign (**+**) denotes rules added to the pending list.

- A minus sign (**-**) denotes rules removed from the saved list.

```
`switch(config-acl-test_1)# **show diff**
---
+++
@@ -1,7 +1,9 @@
 IP Access List test_1
         10 permit ip 10.10.10.0/24 any
-        20 permit ip any host 10.21.10.1
+        20 permit ip 10.10.0.0/16 any
+        25 permit tcp 10.10.20.0/24 any
         30 deny ip host 10.10.10.1 host 10.20.10.1
         40 permit ip any any
+        45 deny pim 239.24.124.0/24 10.5.8.4/30`
```


##### Displaying Egress ACL Counters


The following **show** commands display Egress ACL Counters information.


Use the **show ip access-lists** command to display all the IPv4 ACLs, or a specific IPv4 ACL configured in a switch. The output contains details such as rules in an ACL as well as the respective counter values with each rule, configuration, and status.

```
`switch(config)# **show ip access-list acl1**
IP Access List acl1
 counter per-entry
 10 deny ip 11.1.1.0/24 any dscp af11
 20 deny ip any any [match 39080716, 0:00:00 ago]

 Total rules configured: 2
 Configured on Ingress: Et2/1
 Active on     Ingress: Et2/1`
```


Use the **show ipv6 access-lists** command to display all the IPv6 ACLs or a specific IPv6 ACL configured in a switch. The output contains details such as rules in an ACL and the respective counter values with each rule along with the configuration and status.

```
`switch(config)# **show ipv6 access-list acl1**
IPV6 Access List acl1
 counter per-entry
 10 permit ipv6 any any [match 3450000, 0:00:10 ago]
 20 deny ipv6 any any

 Total rules configured: 2
 Configured on Ingress: Et1/1
 Active on     Ingress: Et1/1`
```


The counter name **EgressAclDropCounter** in the output of this show command signifies the aggregate counter value for the remaining egress IPv4 ACL. In this example, the deny rules, with per rule counters, are not allocated. The per-rule counters are not allocated when the user does not configure the counter per-entry parameter for the respective ACL.

```
`switch(config)# **show hardware counter drop**
Summary:
Total Adverse (A) Drops: 0
Total Congestion (C) Drops: 0
Total Packet Processor (P) Drops: 250
Type Chip CounterName : Count : First Occurrence : Last Occurrence
-------------------------------------------------------------------------------
P Fap0 EgressAclDropCounter : 250 : 2015-11-11 22:39:02 : 2015-11-11 22:51:44`
```


#### Configuring Per-Port Per-VLAN QoS


To configure per-port per-VLAN Quality of Service (QoS), first configure the ACL policing for QoS and then apply the policy map on a single Ethernet or port-channel interface on a per-port per-VLAN basis. The per port per VLAN QoS allows a class map to match traffic for a single VLAN or for a range of VLANs separated by commas. Per-port per-VLAN only works with QoS-based class maps.


To configure per-port per-VLAN QoS on DCS-7280(R) and DCS-7500(R), change the TCAM profile to QoS as shown in the following steps:


- Change the TCAM profile to QoS.

```
`switch# **config**
switch(config)# **hardware tcam profile qos**`
```

- Create an ACL and then match the traffic packets based on the VLAN value and the VLAN mask configured in the ACL.

```
`switch(config)# **ip access-list acl1**
switch(config-acl-acl1)# **permit vlan 100 0xfff ip any any**
switch(config-acl-acl1)# **exit**`
```

- Similarly, create a class map and then match the traffic packets based on the range of VLAN values configured in the class map.

```
`switch(config)# **class-map match-any class1**
switch(config-cmap-qos-class1)# **match vlan 20-40, 1000-1250, 2000**
switch(config-cmap-qos-class1)# **exit**`
```


#### Displaying Per-Port Per-VLAN QoS


The following **show** commands display the status, traffic hit counts, TCAM profile information, and policy maps configured on an interface.


**Examples**


- The **show policy-map** command displays the policy-map information of the configured policy-map.


```
`switch# **show policy-map policy1**
Service-policy policy1
Class-map: class1 (match-any)
Match: ip access-group name acl1
Police cir 512000 bps bc 96000 bytes
Class-map: class-default (match-any)`
```

- The **show policy-map interface** command displays the policy-map configured on an interface.


```
`switch# **show policy-map interface ethernet 1**
Service-policy input: p1
Hardware programming status: Successful
Class-map: c2001 (match-any)
Match: vlan 2001 0xfff
set dscp 4
Class-map: c2002 (match-any)
Match: vlan 2002 0xfff
set dscp 8
Class-map: c2003 (match-any)
Match: vlan 2003 0xfff
set dscp 12`
```


#### Configuring Mirror Access Control Lists


Access Control Lists (ACLs) are configured to permit or deny traffic between source and destination ports on Strata-based platforms. Mirror ACLs are used in mirroring traffic by matching VLAN ID of the configured ACLs. Mirror ACLs are applied for IPv4, IPv6, and MAC ACLs.


Note:Mirror ACLs work only in the receiving direction.


**Examples**


- The following commands configure ACL to permit VLAN traffic between any source and destination host.

```
`switch(config)# **ip access-list acl1**
switch(config-acl-acl1)# **permit vlan 1234 0x0 ip any any**`
```

- The following commands configure monitor session **sess1** with **Ethernet 1** as source port and **Ethernet 2** as the destination port for an ingress ip **acl_1**.

```
`switch(config)# **monitor session sess1 source ethernet 1 rx ip access-group acl1**
switch(config)# **monitor session sess1 destination ethernet 2**`
```


### Applying ACLs


Access Control Lists (ACLs) become active when assigned to an interface, subinterface, or control plane. This section describes the process of adding and removing ACL interface assignments.


#### Applying an ACL to an Interface


The switch must be in interface configuration mode to assign an ACL to an interface or subinterface.


- The **ip access-group** command applies the specified IP or standard IP ACL to the configuration mode interface or subinterface.

- The **ip access-group** command applies the specified IP or standard IP ACL to the control plane traffic.

- The **mac access-group** command applies the specified MAC ACL to the configuration mode interface.


IPv4, IPv6, and MAC ACLs are separately applied for inbound and outbound packets. You can assign an interface or subinterface with multiple ACLs, with a limit of one ACL per packet direction per ACL type. A subset of all available switches support Egress ACLs. IPv6 egress ACLs have limited availability, and IPv6 egress ACLs applied to routed interfaces or subinterfaces across the same chip on the DCS-7500E and the DCS-7280E series can be shared. In addition to that, the DSCP value can match on IPv6 egress ACLs. This ability results in more efficient utilization of system resources and is particularly useful for environments with few, potentially large, IPv6 egress ACLs applied across multiple routed interfaces.


#### Examples


- These commands assign **test1** ACL to **interface ethernet 3**, and verify the assignment.

```
`switch(config)# **interface ethernet 3**
switch(config-if-Et3)# **ip access-group test1 in**
switch(config-if-Et3)# **show running-config interfaces ethernet 3**
interface Ethernet3
   ip access-group test1 in
switch(config-if-Et3)#`
```

- The following commands place the switch in control plane configuration mode and applies the ACL assignment to the control plane traffic.

```
`switch(config)# **control-plane**
switch(config-cp)# **ip access-group test_cp in**`
```

- The following command enables shared ACLs.

```
`switch(config)# **hardware access-list resource sharing vlan ipv6 out**
switch(config)#`
```

- The following command disables shared ACLs.

```
`switch(config)# **no hardware access-list resource sharing vlan ipv6 out**
switch(config)#`
```

- The following commands apply an IPv4 ACL named **test_ACL** to ingress traffic on **interface ethernet 5.1**.

```
`switch(config)# **interface ethernet 5.1**
switch(config-if-Et5.1)# **ipv4 access-group test_ACL in**
switch(config-if-Et5.1)#`
```


#### Removing an ACL from an Interface


The **no ip access-group** command removes an IP ACL assignment statement from ***running-config*** for the configuration mode interface. After removing an ACL, the interface is no longer associated with an IP ACL.


The **no mac ip access-group** command removes a MAC ACL assignment statement from ***running-config*** for the configuration mode interface. After removing a MAC ACL is removed, the interface is no longer associated with an MAC ACL.


To remove an ACL from the control plane, enter the **no ip access-group** command in control plane configuration mode. Removing the control plane ACL command from ***running-config*** reinstates **default-control-plane-acl** as the control plane ACL.


#### Examples


- The following commands remove the assigned IPv4 ACL from **interface ethernet 3**.

```
`switch(config)# **interface ethernet 3**
switch(config-if-Et3)# **no ip access-group test in**
switch(config-if-Et3)#`
```

- The following commands place the switch in control plane configuration mode and remove the ACL assignment from ***running-config***, restoring **default-control-plane-acl** as the control plane ACL.

```
`switch(config)# **control-plane**
switch(config-cp)# **no ip access-group test_cp in**
switch(config-cp)#`
```


## Service ACLs


These sections describe Service ACLs:


- Service Access Control List Description

- Configuring Service ACLs and Displaying Status and Counters


### Service Access Control List Description


Service ACL enforcement is a feature added to a control plane service (the SSH server, the SNMP server, routing protocols, etc.) that allows the switch administrator to restrict the processing of packets and connections by the control plane processes that implement that service. The control plane program run by the control plane process checks already received packets and connections against a user-configurable Access Control List (ACL), a Service ACL.


The Service ACL contains permit and deny rules matching any source address, destination address, and TCP or UDP ports of received packets or connections. After receiving a packet or connection, the control plane process evaluates the packet or connection against the rules of the Service ACL configured for the control plane process. If the received packet or connection matches a deny rule, the control plane process drops or closes it without further processing.


Control Plane Process Enforced Access Control enables the system administrator to restrict which systems on the network can access the services provided by the switch. Each service has its own access control list, giving the system administrator fine-grained control over access to the switch's control plane services. The CLI for this uses the familiar pattern of access control lists assigned for a specific purpose, in this case, for each control plane service.


### Configuring Service ACLs and Displaying Status and Counters


#### SSH Server


To apply the SSH Server Service ACLs for IPv4 and IPv6 traffic, use the **ip access-group (Service ACLs)** and **ipv6 access-group (Service ACLs)** commands in **`config-mgt-ssh`** configuration mode:


```
`switch(config)# **management ssh**
switch(config-mgmt-ssh)# **ip access-group <acl_name> [vrf <vrf_name>] in**
switch(config-mgmt-ssh)# **ipv6 access-group <acl_name> [vrf <vrf_name>] in**`
```


In Release EOS-4.19.0, all VRFs are required to use the same SSH Server Service ACL. The Service ACL assigned without the **vrf** keyword is applied to all VRFs where the SSH Server is enabled.


Use the following commands to display the status and counters of the SSH Server Service ACLs:


```
`switch# **show management ssh ip access-list**
switch# **show management ssh ipv6 access-list**`
```


#### SNMP Server


Use the [**snmp-server community**](/um-eos/eos-snmp#xx1154277) command to apply the SNMP Server Service ACLs to restrict which hosts can access SNMP services on the switch:


**Example**


```
`switch(config)# **snmp-server community** **community-name** [view **viewname**] [ro | rw] **acl_name**`
```


```
`switch(config)# **snmp-server community** **community-name** [view **viewname**] [ro | rw] ipv6 **ipv6_acl_name**`
```


#### EAPI


Use the **ip access-group (Service ACLs)** and **ipv6 access-group (Service ACLs)** commands to apply Service ACLs to the EOS Application Programming Interface (EAPI) Server:


```
`switch(config)# **management api http-commands**
switch(config-mgmt-api-http-cmds)# **vrf <vrf_name>**
switch(config-mgmt-api-http-cmds-vrf-<vrf>)# **ip access-group <acl_name>**
switch(config-mgmt-api-http-cmds-vrf-<vrf>)# **ipv6 access-group <ipv6_acl_name>**`
```


Use the following commands to display the status and counters of the EAPI server Service ACLs:


```
`switch# **show management api http-commands ip access-list**
switch# **show management api http-commands ipv6 access-list**`
```


#### BGP


Use the **ip access-group (Service ACLs)** and **ipv6 access-group (Service ACLs)** commands to apply Service ACLs for controlling connections to the BGP routing protocol agent:


```
`switch(config)# **router bgp <asn>**
switch(config-router-bgp)# **ip access-group <acl_name>**
switch(config-router-bgp)# **ipv6 access-group <ipv6_acl_name>**
switch(config-router-bgp)# **vrf <vrf_name>**
switch(config-router-bgp-vrf-<vrf>)# **ip access-group <acl_name>**
switch(config-router-bgp-vrf-<vrf>)# **ipv6 access-group <ipv6_acl_name>**`
```


Use the following commands to display the status and counters of the BGP routing protocol Service ACLs:


```
`switch# **show bgp ipv4 access-list**
switch# **show bgp ipv6 access-list**`
```


#### UCMP Auto Adjust for BGP


Unequal Cost MultiPath (UCMP) for BGP forwards traffic based on weight assignments for next hops of Equal Cost MultiPath (ECMP) routes. The system programs the weights in the Forwarding Information Base (FIB).


Devices that receive BGP routes disseminate BGP link-bandwidth extended community attribute information. These devices then program the next hops in the FIB using the received link-bandwidth values. The system appends the percentage of interface speed to the received link bandwidth extended community value of the route. It adjusts the weight ratio of the traffic sent over egress ports to forward more traffic toward the peer with a higher interface speed.


##### Configuring UCMP Auto Adjust for BGP


The following command enables the weight adjustment and configures the adjust auto to **62.3** percent.


```
`switch(config-router-bgp)# **neighbor group1 link-bandwidth adjust auto percent 62.3**`
```


PERCENT is a float value between **0.0** and **100.0** and is optional.


#### OSPF


Use the **ip access-group (Service ACLs)** and **ipv6 access-group (Service ACLs)** commands to apply Service ACLs to control packets processed by the OSPF routing protocol agent:


**Example**


```
`switch(config)# **router ospf <id>**
switch(config-router-ospf)# **ip access-group <acl_name>**
switch(config-router-ospf)# **ipv6 access-group <ipv6_acl_name>**`
```


When using VRFs, each per VRF OSPF instance must be explicitly assigned its Service ACL.


Use the following commands to display the OSPF routing protocol Service ACLs' status and counters:


```
`switch# **show ospf ipv4 access-list**
switch# **show ospf ipv6 access-list**`
```


#### PIM


Use the **access-group** command to apply Service ACLs for controlling packets processed by the PIM routing protocol agent:


```
`switch(config)# **router pim**
switch(config-router-pim)# **ipv4**
switch(config-router-pim-ipv4)# **access-group <acl_name>**
switch(config-router-pim-ipv4)#**vrf <vrf_name>**
switch(config-router-pim-vrf-<vrf>)# **ipv4**
switch(config-router-pim-vrf-<vrf>-ipv4)# **access-group <acl_name>**`
```


Use the following command to display the status and counters of the PIM routing protocol Service ACLs.


```
`switch# **show ip pim access-list**`
```


#### IGMP


Use the **ip igmp access-group** command to apply Service ACLs for controlling packets processed by the IGMP management protocol agent:


```
`switch(config)# **router igmp**
switch(config-router-igmp)# **ip igmp access-group <acl_name>**
switch(config-router-igmp)# **vrf <vrf_name>**
switch(config-router-igmp-vrf-<vrf>)# **ip igmp access-group <acl_name>**`
```


Use the following command to display the status and counters of the IGMP management protocol Service ACLs.


```
`switch# **show ip igmp access-list**`
```


#### DHCP Relay


Use the **ip dhcp relay access-group** and **ipv6 dhcp relay access-group** commands to apply Service ACLs for controlling packets processed by the DHCP relay agent:


```
`switch(config)# **ip dhcp relay access-group <acl_name> [vrf <vrf_name>]**
switch(config)# **ipv6 dhcp relay access-group <acl_name> [vrf <vrf_name>]**`
```


Use the following commands to display the status and counters of the DHCP relay agent Service ACLs:


```
`switch# **show ip dhcp relay access-list**
switch# **show ipv6 dhcp relay access-list**`
```


#### LDP


Use the **ip access-group (Service ACLs)** to apply Service ACLs for controlling packets and connections processed by the LDP MPLS label distribution protocol:


```
`switch(config)# **mpls ldp**
switch(config-mpls-ldp)# **ip access-group <acl_name>**`
```


Use the following command to display the status and counters of the LDP Service ACLs.


```
`switch# **show mpls ldp access-list**`
```


#### LANZ


Use the **ip access-group (Service ACLs)** and **ipv6 access-group (Service ACLs)** commands to apply Service ACLs for controlling connections accepted by the LANZ agent:


```
`switch(config)# **queue-monitor streaming**
switch(config-qm-streaming)# **ip access-group <acl_name>**
switch(config-qm-streaming)# **ipv6 access-group <ipv6_acl_name>**`
```


Use the following command to display the status and counters of the LDP Service ACLs.


```
`switch# **show queue-monitor streaming access-lists**`
```


#### MPLS Ping and Traceroute


Use the **ip access-group (Service ACLs)** and **ipv6 access-group (Service ACLs)** commands to apply Service ACLs for controlling connections accepted by the MPLS Ping agent:


```
`switch(config)# **mpls ping**
switch(config-mpls-ping)# **ip access-group <acl_name> [vrf <vrf_name>]**
switch(config-mpls-ping)# **ipv6 access-group <ipv6_acl_name> [vrf <vrf_name>]**`
```


#### Telnet Server


Use the **ip access-group (Service ACLs)** and **ipv6 access-group (Service ACLs)** commands to apply Service ACLs to the Telnet server:


```
`switch(config)# **management telnet**
switch(config-mgmt-telnet)# **ip access-group <acl_name> [vrf <vrf_name>] in**
switch(config-mgmt-telnet)# **ipv6 access-group <ipv6_acl_name> [vrf <vrf_name>] in**`
```


In EOS 4.19.0, all VRFs are required to use the same Telnet server Service ACL. The Service ACL assigned without the **vrf** keyword is applied to all VRFs where the Telnet server is enabled.


Use the following commands to display the status and counters of the LDP Service ACLs:


```
`switch# **show management telnet ip access-list**
switch# **show management telnet ipv6 access-list**`
```


## Sub-interface ACLs


This Sub-interface ACLs feature enables ACL functionality on subinterfaces.


### **Configuring Sub-interface ACLs**


Configure the ACLs on subinterfaces using the following command.


```
`**ip|ipv6 access-group** **acl-name** in | out`
```


Use the following command to unconfigure the ACLs on subinterfaces.


```
`**no ip|ipv6 access-group** in | out`
```


### Configuring ACL Mirroring on a Subinterface Source


Configure a mirror session using subinterface sources and apply explicit ACLs to each source in the session. EOS only supports ingress mirroring from the Rx direction.


Use the following commands to configure a session, *ACLMirror1*, on *Ethernet5/1.1*, *Ethernet5/1.2*, *Ethernet6/1* as the source, *acl1* as the ACL group, and *Ethernet 14/1* as the destination:


```
`switch(config)# **monitor session ACLMirror1 source Ethernet 5/1.1 rx**
switch(config)# **monitor session ACLMirror1 source Ethernet 5/1.2 rx ip access-group acl1**
switch(config)# **monitor session ACLMirror1 source Ethernet 6/1 rx**
switch(config)# **monitor session ACLMirror1 destination Ethernet 14/1**`
```


#### Displaying the ACL Mirroring Information


Use the [**show monitor session**](/um-eos/eos-data-transfer#xx1136306) command to display the session information:


```
`switch(config)# **show monitor session**
Session ACLMirror1
------------------------

Programmed in HW: Yes

Source Ports:

  Rx Only:     Et5/1.2(IP ACL: acl1), Et5/1.1
               Et6/1

Destination Ports:

    Et14/1 :  active`
```


### **Sub-interface ACLs Limitations**


The sub-interface ACLs feature contains the following limitations:


- Egress IPv4 ACLs on subinterfaces are not supported when sharing mode is disabled for Egress IPv4 RACLs.

- Egress IPv6 ACL deny logging is not supported on subinterfaces.

- Blocking traffic while modifying ACLs is not supported on Egress IPv4 ACLs on subinterfaces.


### **Sub-interface ACLs Show Commands**


The **show ip access-lists** and **show ipv6 access-lists** commands display the summary of a configured ACL including the subinterface on which the ACL is configured and active.


**show ip|ipv6 access-lists** **acl-name** summary


**Examples**


```
`switch(config)# **show ip access-lists acl1 summary**
IPV4 ACL acl1
 Total rules configured: 1
 Configured on Ingress: Et5.1
 Active on Ingress: Et5.1`
```


```
`switch(config)# **show ipv6 access-lists acl1 summary**
IPV6 ACL acl1
 Total rules configured: 1
 Configured on Egress: Et5.1
 Active on Egress: Et5.1`
```


## RACL Sharing on SVIs


### IPv4 Ingress Sharing


IPv4 ingress sharing optimizes the utilization of hardware resources by sharing them between different VLAN interfaces when they have the same ACL attached.


Larger deployments benefit from this function, where IPv4 ingress sharing is applied on multiple SVIs with member interfaces on the same forwarding ASIC. For example, a trunk port carrying multiple VLANs and an ingress sharing is applied on all VLANs; it occupies lesser hardware resources irrespective of the number of VLANs. By default, IPv4 ingress sharing is disabled on the switches.


To enable IPv4 Ingress Sharing, use the **no hardware access-list resource sharing vlan in** command.
Note: Enabling or disabling the IPv4 ingress sharing requires the restart of software agents on the switches which is a disruptive process and will impact the traffic forwarding.
The **no** form of the command disables the IPv4 ingress sharing on the switch. To display the IPv4 ingress sharing information use **show platform trident** command on the switch.


### IPv4 Egress Sharing


IPv4 Egress Sharing optimizes the utilization of hardware resources by sharing TCAM entries for a group of SVIs on which IPv4 ACLs are shared. The TCAM entries are shared for all the SVIs per chip, saving a lot of hardware resources and enabling ACLs to scale to larger configurations.


Larger deployments benefit from IPv4 Egress Sharing, which is applied on multiple SVIs with member interfaces on the same forwarding ASIC. For example, a trunk port carrying multiple VLANs, and when applying Egress Sharing on all VLANs, it occupies lesser hardware resources irrespective of the number of VLANs.


By default, the system enables IPv4 Egress Sharing on the switches. However, enabling both IPv4 Egress Sharing and uRPF cannot at the same time is not possible. Disabling IPv4 RACL sharing will allow uRPF configuration and ensure the simultaneous configuration of the RACL in non-shared mode.


To enable unicast Reverse Path Forwarding (uRPF) on the switch, the IPv4 Egress Sharing must be disabled using the **no hardware access-list resource sharing vlan ipv4 out** command.


If IPv4 Egress Sharing was previously disabled from the default configuration, use the hardware access-list resource sharing vlan ipv4 out command to enable it.
Note: Enabling or disabling IPv4 Egress Sharing requires restarting software agents on the switches, which is a disruptive process and will impact the traffic forwarding.

Use the following **show** commands to verify the IPv4 Egress Sharing information on the switch.


- show ip access-lists

- [show vlan](/um-eos/eos-virtual-lans-vlans#xx1153070)

- show platform arad acl tcam

- [show ip route](/um-eos/eos-ipv4#xx1145358)

- [show platform arad ip route](/um-eos/eos-ipv4#xx1173125)


### Configuring IPv4 Egress Sharing


The **hardware access-list resource sharing vlan ipv4 out** command enables IPv4 Egress Sharing on the switch.
Note: IPv4 Egress Sharing is enabled by default.


The **no** form of the command disables the switch's IPv4 Egress Sharing, allowing you to configure the uRPF.


### Displaying IPv4 Egress Sharing Information


**Examples**


- The **show ip access-lists** command displays the list of all the configured IPv4 ACLs.

```
`switch# **show ip access-lists summary**
IPV4 ACL default-control-plane-acl [readonly]
 Total rules configured: 17
 Configured on Ingress: control-plane(default VRF)
 Active on Ingress: control-plane(default VRF)

IPV4 ACL ipAclLimitTest
 Total rules configured: 0
 Configured on Egress: Vl2148,2700
 Active on Egress: Vl2148,2700`
```

- The **show vlan** command displays the list of all the member interfaces under each SVI.

```
`switch# **show vlan**
VLAN  Name           Status    Ports
----- -------------- --------- -----------------
1     default        active
2148  VLAN2148       active    Cpu, Et1, Et26
2700  VLAN2700       active    Cpu, Et18`
```

- The **show platform arad acl tcam** command displays the number of TCAM entries (hardware resources) occupied by the ACL on each forwarding ASIC and the percentage of TCAM utilization per forwarding ASIC.

```
`switch# **show platform arad acl tcam detail**
ip access-list ipAclLimitTest (Shared RACL, 0 rules, 1 entries, direction out,
state success, Acl Label 2)
Fap: Arad0, Shared: true, Interfaces: Vl2148, Vl2700
Bank Offset Entries
0         0       1
Fap: Arad1, Shared: true, Interfaces: Vl2148
Bank Offset Entries
0         0       1

switch# **show platform arad acl tcam summary**
The total number of TCAM lines per bank is 1024.
========================================================
Arad0:
========================================================
 Bank   Used                  Used %             Used By
    0      1                       0   IP Egress PACLs/RACLs
Total Number of TCAM lines used is: 1
========================================================
Arad1:
========================================================
 Bank   Used                   Used %            Used By
    0      1                        0   IP Egress PACLs/RACLs
Total Number of TCAM lines used is: 1`
```

- The **show ip route** command displays the unicast ip routes installed in the system.

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

- The **show platform arad ip route** command displays the platform unicast forwarding routes.

```
`switch# **show platform arad ip route**
Tunnel Type: M(mpls), G(gre)
 -------------------------------------------------------------------------------
|                                Routing Table                                       |               |
|------------------------------------------------------------------------------
|VRF|   Destination    |      |                    |     | Acl   |                 |
ECMP| FEC | Tunnel
| ID|   Subnet         | Cmd  |       Destination  | VID | Label |  MAC / CPU Code
|Index|Index|T Value

--------------------------------------------------------------------------------
|0  |0.0.0.0/8          |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1031 | -
|0  |10.1.0.0/16        |TRAP | CoppSystemL3DstMiss|2659 | - | ArpTrap | - |1030 | -
|0  |10.2.0.0/16        |TRAP | CoppSystemL3DstMiss|2148 | - | ArpTrap | - |1026 | -
|0  |10.3.0.0/16        |TRAP | CoppSystemL3DstMiss|2700 | - | ArpTrap | - |1034 | -
|0  |127.0.0.0/8        |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1031 | -
|0  |172.17.0.0/16      |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1025 | -
|0  |172.18.0.0/16      |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1025 | -
|0  |172.19.0.0/16      |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1025 | -
|0  |172.20.0.0/16      |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1025 | -
|0  |172.22.0.0/16      |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1025 | -
|0  |172.24.0.0/18      |TRAP | CoppSystemL3DstMiss|0    | - | ArpTrap | - |1032 | -
|0  |0.0.0.0/0          |TRAP | CoppSystemL3LpmOver|0    | - | SlowReceive | -
|1024 | -
|0  |10.1.0.0/32*       |TRAP | CoppSystemIpBcast  |0    | - | BcastReceive | -
|1027 | -
|0  |10.1.0.1/32*       |TRAP | CoppSystemIpUcast  |0    | - | Receive | - |32766| -
|0  |10.1.255.1/32*     |ROUTE| Po1                |2659 |4094 | 00:1f:5d:6b:ce:45
| - |1035 | -
|0  |10.1.255.255/32*   |TRAP | CoppSystemIpBcast  |0    | - | BcastReceive | -
|1027 | -
|0  |10.2.0.0/32*       |TRAP | CoppSystemIpBcast  |0    | - | BcastReceive | -
|1027 | -
|0  |10.2.0.1/32*       |TRAP | CoppSystemIpUcast  |0    | - | Receive | - |32766| -
|0  |10.2.255.1/32*     |ROUTE| Et1                |2148 |2 | 00:1f:5d:6d:54:dc |
- |1036 | -
|0  |10.2.255.255/32*   |TRAP | CoppSystemIpBcast  |0    | - | BcastReceive | -
|1027 | -
|0  |10.3.0.0/32*       |TRAP | CoppSystemIpBcast  |0    | - | BcastReceive | -
|1027 | -
|0  |10.3.0.1/32*       |TRAP | CoppSystemIpUcast  |0    | - | Receive | - |32766| -
|0  |10.3.255.1/32*     |ROUTE| Et18               |2700 |2 | 00:1f:5d:6b:00:01 |
- |1038 | -`
```


## Route Maps


A route map is an ordered set of rules that controls the redistribution of IP routes into a protocol domain based on criteria such as route metrics, access control lists, next-hop addresses, and route tags. Route maps can also alter route parameters as they are redistributed.


### Route Map Description


Route maps are composed of route map statements, each consisting of a list of match and set commands.


#### Route Map Statements


Route map statements are categorized by the resolution of routes that the statement filters.


- Permit statements facilitate the redistribution of matched routes.

- Deny statements prevent the redistribution of matched routes.


Route map statement elements include name, sequence number, filter type, match commands, set commands, and continue commands.


- The **name** identifies the route map to which the statement belongs.

- The **sequence number** designates the statement’s placement within the route map.

- A **filter type** specifies the route resolution. Valid types are **permit** and **deny**.

- The **match commands** specify criteria that select the routes the statement evaluates for redistribution.

- The **set commands** modify route parameters for redistributed routes.

- The **continue commands** prolong the route map evaluation of routes that match a statement.


Statements filter routes for redistribution. Routes that statements pass are redistributed (permit statements) or rejected (deny statements). The next statement in the route map then filters routes that statements fail.


- When a statement does not contain a **match** command, the statement passes all routes.

- When a statement contains a single **match** command that lists a single object, the statement passes routes whose parameters match the object.

- When a statement contains a single **match** command that lists multiple objects, the statement passes routes whose parameters match at least one object.

- When a statement contains multiple **match** commands, the statement passes routes whose parameters match all match commands.


The **Set** commands modify parameters for redistributed routes and are valid in permit statements.


#### Example


The following route map statement is named **MAP_1** with sequence number **10**. The statement matches all routes from BGP Autonomous System 10 and redistributes them with a local preference set to **100**. Routes that do not match the statement are evaluated against the next statement in the route map.

```
`switch# **route-map MAP_1 permit 10**
   match as 10
   set local-preference 100`
```


#### Route Maps with Multiple Statements


A route map consists of statements with the same name and different sequence numbers. Statements filter routes by ascending order based on their sequence numbers. When a statement passes a route, the redistribution action is performed as the filter type specifies, ignoring all subsequent statements. When the statement fails the route, the statement with the smallest sequence number larger than the current one filters the route.


All route maps contain an implied final statement containing a single deny statement without a match command. This statement denies the redistribution of any routes that no other statement passes.


#### Example


The following route map is named **MAP_1** and has two permit statements. Routes that do not match either statement are denied redistribution into the target protocol domain.

```
`switch# **route-map MAP_1 permit 10**
   match as 10
   set local-preference 100
!
switch# **route-map MAP_1 permit 20**
   match metric-type type-1
   match as 100`
```


Route Map Configuration describes route map configuration procedures.


#### Route Maps with Multiple Statements and Continue Commands


Route map statements that contain a continue (route map) command support additional route map evaluation of routes whose parameters meet the statement’s match commands. Routes that match a statement containing a **continue** command are evaluated against the statement specified by the **continue** command.


When a route matches multiple route-map statements, the filter action (deny or permit) is determined by the last statement that the route matches. The **set** commands in all statements matching the route are applied to the route after the route map evaluation is complete. Multiple set commands are applied in the same order by which the route was evaluated against the statements containing them.


#### Example


The following route map is named **MAP_2** with a **permit** and a **deny** statement. The permit statement contains a continue command. Routes that match statement 10 are evaluated against statement 20.

```
`switch# **route-map MAP_2 permit 10**
   match as 10
   continue 20
   set local-preference 100
!
switch# **route-map MAP_2 deny 20**
   match metric-type type-1
   match as 100`
```


The route is redistributed if it passes statement 10 and is rejected by statement 20. The route is denied redistribution in all other instances. The **continue** command guarantees the evaluation of all routes against both statements.


### Route Map Configuration


Route maps are created and modified in route-map configuration mode. These sections describe the configuration mode and its commands.


- Route Map Creation and Editing

- Modifying Route Map Components


#### Route Map Creation and Editing


##### Creating a Route Map Statement


To create a route map, use the **route-map** command, including the map name and filter type (**deny** or **permit**). If the command does not specify a number, the system assigns a default sequence number to the statement.


##### Example


The following command places the switch in the ***route map*** configuration mode and creates a route map statement named **map1** with a sequence number of **50**.

```
`switch(config)# **route-map map1 permit 50**
switch(config-route-map-map1)#`
```


##### Editing a Route Map Statement


To edit an existing route map statement, use the **route-map**, including the map’s name and the statement’s number. The switch enters the route map configuration mode for the statement. Subsequent **match (route-map)** and **set (route-map)** commands add the corresponding commands to the statement.


The **show** command displays the contents of the existing route map.


##### Example


The following command places the switch in the route map configuration mode to edit an existing route map statement. The **show** command displays the contents of all statements in the route map.

```
`switch(config)# **route-map MAP2**
switch(config-route-map-MAP2)#show
  Match clauses:
    match as 10
    match tag 333
  Set clauses:
    set local-preference 100
switch(config-route-map-MAP2)#`
```


##### Saving Route Map Modifications


Route map configuration mode is a group-change mode. You can save changes by exiting the mode, either with an explicit **exit** command or by switching directly to another configuration mode. This includes switching to the configuration mode for a different route map.


##### Example


The first command creates the **map1** statement with a sequence number of 10. The second command is not yet saved to the route map, as displayed by the **show** command.


```
`switch(config)# **route-map map1 permit**
switch(config-route-map-map1)# **match as 100**
switch(config-route-map-map1)# **show**

switch(config-route-map-map1)#`
```


The **exit** command saves the **match** command.


```
`switch(config-route-map-map1)# **exit**
switch(config)# **show route-map map1**
route-map map1 permit 10
  Match clauses:
    match as 100
  Set clauses:
switch(config)#`
```


##### Discarding Route Map Modifications


The **abort** command discards all pending changes and exits route-map configuration mode.


##### Example


The **abort** command discards the pending **match** command and restores the original route map.

```
`switch(config)# **route-map map1 permit**
switch(config-route-map-map1)# **match as 100**
switch(config-route-map-map1)# **abort**
switch(config)# **show route-map map1**
switch(config)#`
```


#### Modifying Route Map Components


The following commands add rules to the configuration mode route map:


- **match (route-map)** adds a match rule to a route map.

- **set (route-map)** adds a set rule to a route map.


##### Inserting a Statement


To insert a new statement into an existing route map, create a new statement with a sequence number that differs from any existing statement in the map.


##### Example


The following commands add statement **50** to the **Map1** route map and a match statement of **150**. They save the configuration using **exit** then display the new route map using **show route-map Map1**.

```
`switch(config)# **route-map Map1 permit 50**
switch(config-route-map-Map1)# **match as 150**
switch(config-route-map-Map1)# **exit**
switch(config)# **show route-map Map1**
route-map Map1 deny 10
  Match clauses:
    match as 10
    match tag 333
  Set clauses:
    set local-preference 100
route-map Map1 permit 50
  Match clauses:
    match as 150
  Set clauses:
switch(config)#`
```


##### Deleting Route Map Components


To remove a component from a route map, perform one of the following:


- To remove a command from a statement, enter **no**, followed by the command you want to remove.

- To remove a statement, enter **no**, followed by the route map with the filter type and the sequence number of the statement you want to remove.

- To remove a route map, enter **no** followed by the route map without a sequence number.


### Using Route Maps


Protocol redistribution commands include a route map parameter determining the routes to be redistributed into the specified protocol domain.


#### Example


The following commands use the **Map1** route map to select OSPFv2 routes for redistribution into BGP AS1.

```
`switch(config)# **router bgp 1**
switch(config-router-bgp)# **redistribute ospf route-map Map1**
switch(config-router-bgp)# **exit**
switch(config)#`
```


## Prefix Lists


A prefix list is an ordered set of rules that defines route redistribution access for a specified IP address space. It consists of a filter action (**`deny`** or **`permit`**), an address space identifier (IPv4 **`subnet
          address`** or IPv6 **`prefix`**), and a **`sequence`** number.


Prefix lists are referenced by route map match commands when filtering routes for redistribution.


- Prefix List Configuration describes the prefix list configuration process.

- Using Prefix Lists describes the use of prefix lists.

- Static Routes Redistribution into IGPs describes the redistribution of routes whose configured next-hops satisfy the route-map policy.


### Prefix List Configuration


A prefix list is an ordered set of rules that defines route redistribution access for a specified IP address space. A prefix list rule consists of a filter action (deny or permit), a network address (IPv4 subnet or IPv6 prefix), and a sequence number. A rule may also include an alternate mask size.


The switch supports IPv4 and IPv6 prefix lists. The switch is placed in a Prefix-list configuration mode to create and edit IPv4 or IPv6 prefix lists.


#### IPv4 Prefix Lists


IPv4 prefix lists are created or modified by adding an IPv4 prefix list rule in the Prefix-list configuration mode. Each rule includes the name of a prefix list and the sequence number, network address, and filter action. A list consists of all rules that have the same prefix-list name.


The **ip prefix-list** command creates a prefix list or adds a rule to an existing list. Route map match commands use prefix lists to filter routes for redistribution into OSPF, RIP, or BGP domains.


##### Creating an IPv4 Prefix List


To create an IPv4 prefix list, enter the **ip prefix-list** command, followed by the list's name. The switch enters the ***IPv4 prefix-list*** configuration mode for the list. If the name of an existing ACL follows the command, subsequent commands edit that list.


##### Examples


- The following command places the switch in ***IPv4 prefix list*** configuration mode to create an IPv4 prefix list named **route-one**.

```
`switch(config)# **ip prefix-list route-one**
switch(config-ip-pfx)#`
```

- This series of commands creates four different rules for the prefix-list named **route-one**.

```
`switch(config)# **ip prefix-list route-one**
switch(config-ip-pfx)# **seq 10 deny 10.1.1.0/24**
switch(config-ip-pfx)# **seq 20 deny 10.1.0.0/16**
switch(config-ip-pfx)# **seq 30 permit 12.15.4.9/32**
switch(config-ip-pfx)# **seq 40 deny 1.1.1.0/24**`
```


To view the list, save the rules by exiting the ***Prefix-list*** command mode using the **exit** command, then re-enter the configuration mode and use the **show active** command.


```
`switch(config-ip-pfx)# **exit**
switch(config)# **ip prefix-list route-one**
switch(config-ip-pfx)# **show active**
ip prefix-list route-one
   seq 10 deny 10.1.1.0/24
   seq 20 deny 10.1.0.0/16
   seq 30 permit 12.15.4.9/32
   seq 40 deny 1.1.1.0/24
switch(config-ip-pfx)# **ip prefix-list route-one**`
```


IPv4 prefix lists are referenced in the **match (route-map)** command.


#### IPv6 Prefix Lists


##### Creating an IPv6 Prefix List


The switch provides an ***IPv6 prefix-list*** configuration mode for creating and modifying IPv6 prefix lists. A list can be edited only in the mode where it was created.


To create an IP ACL, enter the **ipv6 prefix-list** command and the list's name. The switch enters the list's ***IPv6 prefix-list*** configuration mode. If the name of an existing ACL follows the command, subsequent commands edit that list.


##### Example


This command places the switch in the ***IPv6 prefix list*** configuration mode to create an IPv6 prefix list named **map1**.

```
`switch(config)# **ipv6 prefix-list map1**
switch(config-ipv6-pfx)#`
```


##### Adding a Rule


To append a rule to the end of a list, enter the rule without a sequence number while in ***Prefix-List*** configuration mode for the list. The system derives the new rule’s sequence number by adding **10** to the last rule’s sequence number.


##### Example


These commands enter the first two rules into a new prefix list.

```
`switch(config-ipv6-pfx)# **permit 3:4e96:8ca1:33cf::/64**
switch(config-ipv6-pfx)# **permit 3:11b1:8fe4:1aac::/64**`
```


To view the list, save the rules by exiting the ***prefix-list*** command mode using the **exit** command, then re-enter the configuration mode and use the **show active** command.


```
`switch(config-ipv6-pfx)# **exit**
switch(config)# **ipv6 prefix-list map1**
switch(config-ipv6-pfx)# **show active**
ipv6 prefix-list map1
   seq 10 permit 3:4e96:8ca1:33cf::/64
   seq 20 permit 3:11b1:8fe4:1aac::/64
switch(config-ipv6-pfx)#`
```


The following command appends a rule to the end of the prefix list. The new rule’s sequence number is **30**.


```
`switch(config-ipv6-pfx)# **permit 3:1bca:1141:ab34::/64**
switch(config-ipv6-pfx)# **exit**
switch(config)# **ipv6 prefix-list map1**
switch(config-ipv6-pfx)# **show active**
ipv6 prefix-list map1
   seq 10 permit 3:4e96:8ca1:33cf::/64
   seq 20 permit 3:11b1:8fe4:1aac::/64
   seq 30 permit 3:1bca:1141:ab34::/64
switch(config-ipv6-pfx)#`
```


##### Inserting a Rule


To insert a rule into a prefix list, use the **seq (IPv6 Prefix Lists)** command to enter a rule with a sequence number between the numbers of two existing rules.


##### Example


This command inserts a rule between the first two by assigning sequence number **15**.

```
`switch(config-ipv6-pfx)# **seq 15 deny 3:4400::/64**
switch(config-ipv6-pfx)# **exit**
switch(config)# **show ipv6 prefix-list map1**
ipv6 prefix-list map1
seq 10 permit 3:4e96:8ca1:33cf::/64
seq 15 deny 3:4400::/64
seq 20 permit 3:11b1:8fe4:1aac::/64
seq 30 permit 3:1bca:3ff2:634a::/64
switch(config)#`
```


##### Deleting a Rule


To remove a rule from the configuration mode prefix list, enter **no seq** (see **seq (IPv6 Prefix Lists)**), followed by the rule's sequence number.


##### Example


These commands remove rule **20** from the prefix list and display the resultant prefix list.

```
`switch(config-ipv6-pfx)# **no seq 20**
switch(config-ipv6-pfx)# **exit**
switch(config)# **show ipv6 prefix-list map1**
ipv6 prefix-list map1
seq 10 permit 3:4e96:8ca1:33cf::/64
seq 15 deny 3:4400::/64
seq 30 permit 3:1bca:3ff2:634a::/64
switch(config)#`
```


### Using Prefix Lists


Route map match commands include an option that matches a specified prefix list.


**Example**


The **MAP_1** route map uses a match command that references the **PL_1** prefix list.

```
`switch(config)# **route-map MAP_1 permit**
switch(config-route-map-MAP_1)# **match ip address prefix-list PL_1**
switch(config-route-map-MAP_1)# **set community 500**
switch(config-route-map-MAP_1)# **exit**`
```


### Static Routes Redistribution into IGPs


Use **match ip next-hop** to match against next-hops in a route-map. This can be used to redistribute matching static routes into an IGP (IS-IS, OSPF, etc.).


The following example applies the **match ip next-hop** clause for static routes redistributed into IGPs for multi-agent mode. The following configures a static route.


```
`switch(config)# **ip route 10.20.30.0/24 1.2.3.4**`
```


The following commands configure a prefix-list:


```
`switch (config)# **ip prefix-list prefixListName**
switch(config-ip-pfx)# **permit 1.2.3.4/32**`
```


**1.2.3.4** is a **configured** next-hop for static route **10.20.30.0/24**.


The following commands configure a route map:


```
`switch(config)# **route-map routeMapName**
switch(config-route-map-routeMapName)# **match ip next-hop prefix-list prefixListName**`
```


For example, based on the route-map mentioned in the preceding command, to redistribute matching static routes into an IGP, use the following command for IS-IS:


```
`switch(config-router-isis)# **redistribute static route-map routeMapName**`
```


View redistributed routes using the following **show** commands.


The **show ip route** command displays the IP route.


```
`switch# **show ip route**

VRF: default
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

 ...
 I L2     10.20.30.0/24 [115/10] via 1.2.3.4, Ethernet1`
```


Use the **show isis database detail** command to view routes redistributed into IS-IS.


```
`switch# **show isis database detail**

IS-IS Instance: B VRF: default
  IS-IS Level 1 Link State Database
    LSPID                 Seq Num   Cksum  Life  IS Flags
    ...
  IS-IS Level 2 Link State Database
    LSPID                 Seq Num   Cksum  Life  IS Flags
    0000.0000.0001.00-00  6         10364  840   L2 <>
      ...
      Reachability         : 10.20.30.0/24 Metric: 0 Type: 1 Up
      ...`
```


While the preceding example applies to IS-IS, a similar approach may be taken for other IGPs, such as OSPF.


## Port ACLs with User-Defined Fields


Describes the support for specifying User-Defined Fields (UDF) in Port ACLs, including IPv4, IPv6, and MAC ACLs. The purpose of the User-Defined Fields feature is to permit or deny packets based on custom offset pattern matching.


User-Defined Fields, or UDFs, are part of an access-list filter and comprise an offset, length, pattern match and mask. This describes a single portion of any incoming packet that matches the provided value.


UDFs may also be defined via aliases. Aliases can save a UDF configuration for reuse in multiple access lists or access list rules. An alias may substitute for a fully defined UDF, including the offset, pattern, and mask. The pattern or mask may be overridden when the alias is used in an access list rule.


The behavior, CLI syntax, and configuration of UDFs are identical to Traffic Steering UDF and Mirroring ACL UDF.


This section describes port ACLs with user-defined fields, including configuration instructions. Topics covered by this section include:


- Configuring Port ACLs with User-Defined Fields

- Port ACLs with User-Defined Fields Limitations


### Configuring Port ACLs with User-Defined Fields


User-Defined Fields (UDFs) are specified as part of an access list. However, the type of access list dictates the base position of the UDF and the options available. In addition, you must configure a TCAM profile to include UDFs as part of the Port ACL feature’s key.


#### TCAM Profile


User-Defined Fields are defined as additional fields in the Port ACL feature’s key. By default, UDFs are not included in the keys for the Port ACL features. Adding a UDF to the key requires removing different key fields to fit within the TCAM width restrictions.


Note: Each UDF is either 16 bits wide or 32 bits wide.


The following are example configurations of the TCAM profile.


##### IPv4 Port ACL


The following configurations create a new profile based on the default profile. This new profile replaces the Layer 4 port key fields with one 16-bit UDF and one 32-bit UDF.


```
`switch(config)# **hardware tcam**
switch(config-hw-tcam)# **profile ipv4Udf copy default**
switch(config-hw-tcam-profile-ipv4Udf)# **feature acl port ip**
switch(config-hw-tcam-profile-ipv4Udf-feature-acl-port-ip)# **no key field l4-ops**
switch(config-hw-tcam-profile-ipv4Udf-feature-acl-port-ip)# **no key field l4-src-port**
switch(config-hw-tcam-profile-ipv4Udf-feature-acl-port-ip)# **no key field l4-dst-port**
switch(config-hw-tcam-profile-ipv4Udf-feature-acl-port-ip)# **key field udf-16b-1**
switch(config-hw-tcam-profile-ipv4Udf-feature-acl-port-ip)# **key field udf-32b-1**
switch(config-hw-tcam-profile-ipv4Udf-feature-acl-port-ip)# **exit**
switch(config-hw-tcam-profile-ipv4Udf)# **exit**
switch(config-hw-tcam)# **system profile ipv4Udf**`
```


16-bit IPv4 Header Match

**Example**


The following configurations match IPv4 packets based on the Identification (ID) field.


Packets ingressing into **interface ethernet 7** with an ID equal to **1000** (`0x03E80000`) are forwarded, while packets with an ID different from **1000** are dropped.


```
`(config)# **ip access-list udfAcl**
(config-acl-udfAcl)# **permit ip any any payload header start offset 1 pattern 0x03E80000 mask 0x0000FFFF**
(config-acl-udfAcl)# **deny ip any any**
(config-acl-udfAcl)# **exit**
(config)# **interface ethernet 7**
(config-if-Et7)#`
```


##### IPv6 Port ACL


The following configurations create a new profile based on the default profile. This new profile replaces the destination IPv6 address key field with two 32-bit UDFs.


```
`switch(config)# **hardware tcam**
switch(config-hw-tcam)# **profile ipv6Udf copy default**
switch(config-hw-tcam-profile-ipv6Udf)# **feature acl port ipv6**
switch(config-hw-tcam-profile-ipv6Udf-feature-acl-port-ipv6)# **no key field dst-ipv6**
switch(config-hw-tcam-profile-ipv6Udf-feature-acl-port-ipv6)# **key field udf-32b-1**
switch(config-hw-tcam-profile-ipv6Udf-feature-acl-port-ipv6)# **key field udf-32b-2**
switch(config-hw-tcam-profile-ipv6Udf-feature-acl-port-ipv6)# **exit**
switch(config-hw-tcam-profile-ipv6Udf)# **exit**
switch(config-hw-tcam)# **system profile ipv6Udf**`
```


32-bit IPv6 Payload Match

**Example**


The following configurations match IPv6 UDP packets based on the first 32 bits of the packet payload.


UDP packets ingressing into **interface ethernet 7** that starts with **0x1234567X** (where **X** can be any valid hexadecimal) in the payload are forwarded while dropping any other packets. The offset is set to **2** (2 x 4-byte words) to skip the UDP header.


```
`(config)# **ipv6 access-list udfAcl**
(config-ipv6-acl-udfAcl)# **permit udp any any payload offset 2 pattern 0x12345670 mask 0x0000000f**
(config-ipv6-acl-udfAcl)# **deny ipv6 any any**
(config-ipv6-acl-udfAcl)# **exit**
(config)# **interface ethernet 7**
(config-if-Et7)# **ipv6 access-group udfAcl in**`
```


### Port ACLs with User-Defined Fields Limitations


User-defined fields consume a limited set of copy resources. For each unique offset, if a pattern is specified masked to be > 16 bits wide, then a 32-bit resource is used. If no 32-bit resource is available, then two 16-bit resources are used if available. Copy resources depend on the number of UDF key fields added to the feature key. Each UDF key field maps to one copy resource. Using the above TCAM profile configurations:


- IPv4: 1 × 16-bit pattern + 1 × 32-bit pattern.

- IPv6: 2 × 32-bit pattern.

- MAC: 1 × 16-bit pattern + 1 × 32-bit pattern.


Other limitations include:


- The maximum offset value is **31**, which is 31 4-byte words, or 124 bytes.

- UDFs only work on ingress Port ACLs.


## ACL, Route Map, and Prefix List Commands


This section describes CLI commands that this chapter references.


### ACL Creation and Access Commands


- hardware access-list resource sharing vlan in

- hardware access-list resource sharing vlan ipv4 out

- ip access-list

- ip access-list standard

- ipv6 access-list

- ipv6 access-list standard

- mac access-list

- system profile


### ACL Implementation Commands


- ip access-group

- ipv6 access-group

- mac access-group


### Service ACL Implementation Commands


- ip access-group (Service ACLs)

- ipv6 access-group (Service ACLs)


### ACL Edit Commands


- counters per-entry (ACL configuration modes)

- hardware access-list update default-result permit

- no sequence number (ACLs)

- resequence (ACLs)

- show (ACL configuration modes)


### ACL Rule Commands


- deny (IPv4 ACL)

- deny (IPv6 ACL)

- deny (MAC ACL)

- deny (Standard IPv4 ACL)

- deny (Standard IPv6 ACL)

- permit (IPv4 ACL)

- permit (IPv6 ACL)

- permit (MAC ACL)

- permit (Standard IPv4 ACL)

- permit (Standard IPv6 ACL)

- remark


### ACL List Counter Commands


- clear ip access-lists counters

- clear ipv6 access-lists counters

- hardware counter feature acl out


### ACL Display Commands


- show access-lists

- show ip access-lists

- show ipv6 access-lists

- show mac access-lists


### Prefix List Creation and Access Commands


- ip prefix-list

- ipv6 prefix-list


### Prefix List Edit Commands


- deny (IPv6 Prefix List)

- permit (IPv6 Prefix List)

- seq (IPv6 Prefix Lists)


### Prefix List Display Commands


- show hardware tcam profile

- show ip prefix-list

- show ipv6 prefix-list

- show platform arad acl tcam

- show platform arad acl tcam summary

- show platform arad mapping

- show platform fap acl

- show platform fap acl tcam

- show platform fap acl tcam hw

- show platform fap acl tcam summary

- show platform trident tcam


### Route Map Creation and Access Command


- route-map


### Route Map Edit Commands


- continue (route map)

- description (route map)

- match (route-map)

- set (route-map)

- set as-path prepend

- set as-path match

- set community (route-map)

- set extcommunity (route-map)


### Route Map Display Commands


- show route-map


### clear ip access-lists counters


The **clear ip access-lists counters** command sets ACL counters to zero for the specified IPv4 Access Control List (ACL). The **session** parameter limits ACL counter clearing to the current CLI session.


**Command Mode**


Privileged EXEC


**Command Syntax**


clear ip access-lists counters acl_name scope


**Parameters**


- **acl_name** - Specify the name of ACL list. Options include the following:


- **no parameter** - Specifies all ACLs.

- **access_list** - Specifies the name of ACL.

- **scope** - Specify the session affected by command. Options include the following:


- **no parameter** - Clears all counters on all CLI sessions.

- **session** - Clears counters only on the current CLI session.


**Example**


This command resets all IPv4 ACL counters.

```
`switch(config)# **clear ip access-lists counters**
switch(config)#`
```


### clear ipv6 access-lists counters


The **clear ipv6 access-lists counters** command sets ACL counters to zero for the specified IPv6 Access Control List (ACL). The **session** parameter limits ACL counter clearing to the current CLI session.


**Command Mode**


Privileged EXEC


**Command Syntax**


clear ipv6 access-lists counters [acl_name][scope]


**Parameters**


- **acl_name** - Specify the name of ACL. Options include the following:


- **no parameter** - Clears all IPv6 ACLs.

- **access_list** - Clears the access list of the IPv6 ACL.

- **scope** - Specify the session affected by command. Options include the following:


- **no parameter** - The command affects counters on all CLI sessions.

- **session** - Affects only current CLI session.


**Example**


This command resets all IPv6 ACL counters.

```
`switch(config)# **clear ipv6 access-lists counters**
switch(config)#`
```


### continue (route map)


The **continue** command creates a route map statement entry that enables additional route map evaluation of routes with parameters meeting the statement matching criteria.


A statement typically contains a match (route-map) and a set (route-map) command. The evaluation of routes with settings the same as **match** command parameters normally ends and the statement's **set** commands apply to the route. Routes that match a statement containing a **continue** command evaluate against the statement specified by the **continue** command.


When a route matches multiple route map commands, the last statement that the route matches determines the filter action (**deny** or**permit**) . The **set** commands in all statements matching the route apply to the route after completing the route map evaluation. Multiple set commands apply in the same order by the route evaluation against the statement containing them.


The **no continue** and **default continue** commands remove the corresponding **continue** command from the configuration mode **route map** statement by deleting the corresponding command from ***running-config***.


**Command Mode**


Route-Map Configuration


**Command Syntax**


**continue next_seq**


**no continue next_seq**


**default continue next_seq**


**Parameters**


next_seq - Specifies next statement for evaluating matching routes. Options include the following:


- **no parameter** - The next statement in the route map, as determined by sequence number.

- **seq_number** - Specifies the number of the next statement. Values range from **1** to **16777215**.


**Restrictions**


A **continue** command cannot specify a sequence number smaller than the sequence number of the route map statement.


**Related Command**


route-map command enters the Route-Map Configuration Mode.


**Example**


This command creates route map **map1**, statement **40** with a match command, a set command, and a continue command. Routes that match the statement subsequently evaluate against statement **100**. The **set local-preference** command applies to matching routes regardless of subsequent matching operations.

```
`switch(config)# **route-map map1 deny 40**
switch(config-route-map-map1)# **match as 15**
switch(config-route-map-map1)# **continue 100**
switch(config-route-map-map1)# **set local-preference 50**
switch(config-route-map-map1)#`
```


### counters per-entry


The **counters per-entry** command places the ACL in counting mode. In counting mode, the feature generally displays the number of instances in which each rule in the list matches an inbound packet and the elapsed time since the last match. However, for certain select platforms, in addition to the packet counter, ACL counters can also be enabled for byte counts when applied to data plane ACLs. Review the complete list of platforms that support byte count for data plan ACLslisted below:


Note: Only dataplane ACLs support byte counting on the switch.


The following platforms support ACL byte counting:


- CCS-710/720/722/755/758 series

- DCS-7010TX

- DCS-7050SX3/CX3/TX3/CX4/DX4/PX4

- DCS-7060 Series

- DCS-7300X3/7304X3/7308X3/7316/7320X/7324/7328/7358X4/7368/7388


On the FM6000 platform, this command has no effect when used in an ACL for a PBR class map.


The **no counters per-entry** and **default counters per-entry** commands place the ACL in non-counting mode.


**Command Mode**


ACL Configuration


IPv6-ACL Configuration


Std-ACL Configuration


Std-IPv6-ACL Configuration


MAC-ACL Configuration


**Command Syntax**


counters per-entry


no counters per-entry


default counters per-entry


**Examples**


- This command places the **test1** ACL in counting mode.

```
`switch(config)# **ip access-list test1**
switch(config-acl-test1)# **counters per-entry**
switch(config-acl-test1)#`
```

- This command displays the ACL, with counter information, for an ACL in counting mode.

```
`switch# **show ip access-lists**
IP Access List default-control-plane-acl [readonly]
  counters per-entry
  10 permit icmp any any
  20 permit ip any any tracked [match 12041 packets, 0:00:00 ago]
  30 permit ospf any any
  40 permit tcp any any eq ssh telnet www snmp bgp https [match 11 packets, 1:41:07 ago]
  50 permit udp any any eq bootps bootpc snmp rip [match 78 packets, 0:00:27 ago]
  60 permit tcp any any eq mlag ttl eq 255
  70 permit udp any any eq mlag ttl eq 255
  80 permit vrrp any any
  90 permit ahp any any
  100 permit pim any any
  110 permit igmp any any [match 14 packets, 0:23:27 ago]
  120 permit tcp any any range 5900 5910
  130 permit tcp any any range 50000 50100
  140 permit udp any any range 51000 51100
Total rules configured: 14
       Configured on Ingress: control-plane(default VRF)
       Active on     Ingress: control-plane(default VRF)`
```

- On platforms that support byte counting, Counter information displays as shown below:

```
`switch# **show ip access-lists**
IP Access List default-control-plane-acl [readonly]
        counters per-entry
        10 permit icmp any any [match 30 packets, 0:02:08 ago]
        20 permit ip any any tracked [match 97777 packets, 0:00:00 ago]
        30 permit udp any any eq bfd ttl eq 255
        40 permit udp any any eq bfd-echo ttl eq 254
        50 permit udp any any eq multihop-bfd micro-bfd sbfd
        60 permit udp any eq sbfd any eq sbfd-initiator
        70 permit ospf any any
        80 permit tcp any any eq ssh telnet www snmp bgp https msdp ldp netconf-ssh gnmi [match 72 packets, 0:00:00 ago]
        90 permit udp any any eq bootps bootpc snmp rip ntp ldp ptp-event ptp-general
        100 permit tcp any any eq mlag ttl eq 255
        110 permit udp any any eq mlag ttl eq 255
        120 permit vrrp any any
        130 permit ahp any any
        140 permit pim any any
Total rules configured: 14
             Configured on Ingress: control-plane(default VRF)
             Active on     Ingress: control-plane(default VRF)

IP Access List ipCountersTest:*The **ipCountersTest ACL** is applied to the data plane. Hence, it displays the byte count information as shown below:*
        counters per-entry
        10 permit tcp host 10.1.1.1 range 2000 4000 host 10.2.1.1 [match 486 bytes in 3 packets, 0:00:26 ago]
        20 permit tcp host 10.1.1.1 range 14000 16000 host 10.2.1.1 [match 486 bytes in 3 packets, 0:00:18 ago]
        30 permit udp host 10.1.1.1 range 62000 64000 host 10.2.1.1 [match 450 bytes in 3 packets, 0:00:00 ago]
        40 permit tcp host 10.1.1.1 range 50000 52000 host 10.2.1.1 [match 486 bytes in 3 packets, 0:00:02 ago]
        50 permit tcp host 10.1.1.1 range 38000 40000 host 10.2.1.1 [match 486 bytes in 3 packets, 0:00:10 ago]
        60 permit tcp host 10.1.1.1 range 26000 28000 host 10.2.1.1 [match 486 bytes in 3 packets, 0:00:18 ago]
Total rules configured: 6`
```


**ipCountersTest** ACL applies to the data plane and displays the byte count information.


### deny (IPv4 ACL)


The **deny**command adds a deny rule to the configuration mode IPv4 Access Control List (ACL). Interfaces with the ACL drop packets filtered by a **deny** rule. Sequence numbers determine rule placement in the ACL. Sequence numbers for commands without numbers derive from adding **10** to the number of the ACL's last rule.


The **no deny** and **default deny** commands remove the specified rule from the configuration mode ACL. The no sequence number (ACLs) command also removes the specified rule from the ACL.


**Command Mode**


ACL Configuration


**Command Syntax**


[seq_num] deny protocol source_addr source_port dest_addrR dest_port flags message fragments tracked dscp_filter ttl_filter log


no deny protocol source_addr source_port dest_addrR dest_port flags message fragments tracked dscp_filter ttl_filter log]


default deny protocol source_addr source_port dest_addrR dest_port flags message fragments tracked dscp_filter ttl_filter log]


Note: Commands use a subset of the listed fields. Available parameters depend on specified protocol.


**Parameters**


- **seq_num** - The sequence number assigned to the rule. Options include the following:


- **no parameter** The number derive from adding 10 to the number of the ACL last rule.

- **14294967295** -The number assigned to the entry.

- **protocol** Specify the protocol field filter. Values include the following:


- **ahp** - Authentication Header Protocol (51

- **icmp** - Internet Control Message Protocol (1)

- **igmp** - Internet Group Management Protocol (2)

- **ip** - Internet Protocol v4 (4)

- **ospf** - Open Shortest Path First (89)

- **pim** - Protocol Independent Multicast (103)

- **tcp** - Transmission Control Protocol (6)

- **udp** - User datagram protocol (17)

- **vrrp** - Virtual Router Redundancy Protocol (112)

- **protocol_num** - An integer corresponding to an IP protocol. Values range from **0** to **255**.

- **source_addr** and **dest_addr** - Specify the source and destination address filters. Values include the following:


- **network_addr** - Specify the subnet address as a CIDR or address-mask.

- **any** - Filter packets from all addresses.

- **host** **ip_addr** - Specify an IP address in dotted decimal notation.

Subnet addresses support discontiguous masks.

- **source_port** and **dest_port** - Specify the source and destination port filters. Values include the following:


- **any** - Specify all ports.

- **eq** **port-1** **port-2** ... **port-n** - Specify a list of ports. Maximum list size is 10 ports.

- **neq** **port-1** **port-2** ... **port-n** - Specify the set of all ports not listed. Maximum list size is 10 ports.

- **gt** **port** - Specify the set of ports with larger numbers than the listed port.

- **lt** **port** - Specify the set of ports with smaller numbers than the listed port.

- **range** **port_1** **port_2** - Specify a range of ports.

- **fragments** Filters packets with FO bit set that indicates a non-initial fragment packet.

- **flags** Flag bit filters (TCP packets).

- **message** Message type filters (ICMP packets).

- **tracked** Rule filters packets in existing ICMP, UDP, or TCP connections.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.

- **dscp_filter** - Filters a packet by the DSCP value. Values include the following:


- **no parameter** -Specify that the rule does not use DSCP to filter packets.

- **dscp** **dscp_value** - Specify to match packets match if the DSCP field in packet equals the **dscp_value**.

- **TTL_FILTER** - Filters a packet by the TTL (time-to-live) value. Values include the following:


- **ttl eq** **ttl_value** - Match packets if **ttl** in packet is equal to **ttl_value**.

- **ttl gt** **ttl_value** - Match packets if **ttl** in packet is greater than **ttl_value**.

- **ttl lt** **ttl_value** - Match packets if **ttl** in packet is less than **ttl_value**.

- **ttl neq** **ttl_value** - Match packets if **ttl** in packet is not equal to **ttl_value**.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.

- **log** - Triggers an informational log message to the console about the matching packet.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.


**Examples**


- This command appends a **deny** statement at the end of the ACL. The **deny** statement drops OSPF packets from **10.10.1.1/24** to any host.

```
`switch(config)# **ip access-list text1**
switch(config-acl-text1)# **deny ospf 10.1.1.0/24 any**
switch(config-acl-text1)#`
```

- This command inserts a **deny** statement with the sequence number 65. The **deny** statement drops all PIM packets.

```
`switch(config-acl-text1)# **65 deny pim any any**
switch(config-acl-text1)#`
```


### deny (IPv6 ACL)


The **deny**command adds a deny rule to the an IPv6 Access Control List (ACL). Interfaces with the ACL drop packets filtered by a **deny** rule. Sequence numbers determine rule placement in the ACL. Sequence numbers for commands without numbers derive from adding **10** to the number of the ACL's last rule.


The **no deny** and **default deny** commands remove the specified rule from the configuration mode ACL. The no <sequence number> (ACLs) command also removes the specified rule from the ACL.


**Command Mode**


IPv6-ACL Configuration


**Command Syntax**


**seq_num deny protocol src_addr source_pt dest_addr dest_pt flag msg hop tracked dscp_filter log**


**no deny **protocol src_addr source_pt dest_addr dest_pt flag msg hop tracked dscp_filter log****


**default deny****protocol src_addr source_pt dest_addr dest_pt flag msg hop tracked dscp_filter log**


Note: Commands use a subset of the listed fields. Available parameters depend on specified protocol. Use CLI syntax assistance to view parameters for specific protocols when creating a deny rule.


**Parameters**


- **seq_num** - The sequence number assigned to the rule. Optionsinclude the following:


- **no parameter** - The number derived from adding **10** to the number of the ACL last rule.

- **1 - 4294967295** - A number assigned to an entry.

- **prot** - Specify the protocol field filter. Values include the following:


- **icmpv6** - Internet Control Message Protocol for version 6 (58)

- **ipv6** - Internet Protocol IPv6 (41)

- **ospf** - Open Shortest Path First (89)

- **tcp** - Transmission Control Protocol (6)

- **udp** - User Datagram Protocol (17)

- **protocol_num** - An integer corresponding to an IP protocol. Values range from **0** to **255**.

- **SRC_ADDR** and **DEST_ADDR** - Specify source and destination address filters. Options include the following:


- **ipv6_prefix** - Specify an IPv6 address with prefix length (CIDR notation).

- **any** - Filter packets from all addresses.

- **host** **ipv6_addr** - Specify an IPv6 host address.

- **SRC_PT** and **DEST_PT** - Specify the source and destination port filters. Options include the following:


- **any** - Specify all ports.

- **eq** **port-1** **port-2** ... **port-n** - Specify a list of ports. Maximum list size is 10 ports.

- **neq** **port-1** **port-2** ... **port-n** - Specify the set of all ports not listed. Maximum list size is 10 ports.

- **gt** **port** - Specify the set of ports with larger numbers than the listed port.

- **lt** **port** - Specify the set of ports with smaller numbers than the listed port.

- **range** **port_1** **port_2** - Specify a range of ports.

- HOP - Filters by packet hop-limit value. Options include the following:


- **no parameter** - The rule does not use hop limit to filter packets.

- **hop-limit eq** **hop_value** - Match packetsif **hop-limit** value in packet equals **hop_value**.

- **hop-limit gt** **hop_value** - Match packets if **hop-limit** in packet is greater than **hop_value**.

- **hop-limit lt** **hop_value** - Match packets if **hop-limit** in packet is less than **hop_value**.

- **hop-limit neq** **hop_value** - Match packets if **hop-limit** in packet is not equal to **hop_value**.

- **FLAG** - Specify flag bit filters (TCP packets).

- **MSG** - Specify message type filters (ICMPv6 packets).

- **tracked** - Specify rule filters packets in existing ICMP, UDP, or TCP connections.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.

- **DSCP_FILTER**- Filters packet by theDSCP value. Values include the following:


- **no parameter** - The rule does not use DSCP to filter packets.

- **dscp** **dscp_value** - Match packets if DSCP field in packet equalsthe **dscp_value**.

- **log** - Triggers an informational log message to the console about the matching packet.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.


**Example**


This command appends a **deny** statement at the end of the ACL. The **deny** statement drops IPv6 packets from **3710:249a:c643:ef11::/64** to any host.

```
`switch(config)# **ipv6 access-list text1**
switch(config-acl-text1)# **deny ipv6 3710:249a:c643:ef11::/64 any**
switch(config-acl-text1)#`
```


### deny (IPv6 Prefix List)


The **deny** command adds a deny rule in the IPv6 Prefix List Configuration Mode . Route map match commands use prefix lists to filter routes for redistribution into OSPF, RIP, or BGP domains. Routes are denied access when they match the prefix in a **deny** statement.


The **no deny** and **default deny** commands remove the specified rule from theIPv6 prefix list. The **no deny** command also removes the specified rule from the prefix list.


**Command Mode**


IPv6-pfx Configuration


**Command Syntax**


sequence deny ipv6_prefix mask


**Parameters**


- **sequence** - A sequence number assigned to the rule. Options include the following:


- **no parameter** - A number derived by adding **10** to the number of the list last rule.

- **seq** **seq_num** - A number specified by **seq_num**. Value ranges from **0 to 65535**.

- **ipv6_prefix** - Specify the IPv6 prefix to filter routes (CIDR notation).

- **mask** - Specify the range of the prefix to match.


- **no parameter** - Requires an exact match with the subnet mask.

- **eq** **mask_e** - Specify a prefix length equal to **mask_e**.

- **ge** **mask_g** Specify a range from **mask_g** to **128**.

- **le** **mask_l** - Specify a range from **subnet** mask length to **mask_l**.

- **ge** **mask_l** **le** **mask_g** - Specify a range from **mask_g** to **mask_l**.

- **mask_e**, **mask_land**, and **mask_g** -from **1 to 128**.


**Example**


This command appends a **deny** statement at the end of the **text1** prefix list. The **deny** statement denies redistribution of routes with the specified prefix.

```
`switch(config)# **ipv6 prefix-list route-five**
switch(config-ipv6-pfx)# **deny 3100::/64**
switch(config-ipv6-pfx)#`
```


### deny (MAC ACL)


The **deny** command adds a deny rule to the MAC Access Control List (ACL) Configuration Mode.


Interfaces with an applied ACL drop packets filtered by a **deny** rule. Sequence numbers determine rule placement in the ACL. Sequence numbers for commands without numbers derive from adding **10** to the number of the ACL last rule.


The **no deny** and **default deny** commands remove the specified rule from the MAC Access Control List (ACL) Configuration Mode. The no <sequence number> (ACLs) command also removes the specified rule from the ACL.


**Command Mode**


MAC-ACL Configuration Mode


**Command Syntax**


seq_num deny source_addr dest_addr [protocol][log]


no deny source_addr dest_addr [protocol][log]


default deny source_addr dest_addr [protocol][log]


**Parameters**


- **seq_num** Sequence number assigned to the rule. Options include the following:


- **no parameter** - A number derived by adding **10** to the number of the ACL's last rule.

- **1 - 4294967295** - A number assigned to entry.

- **source_addr** and **dest_addr** - Configure source and destination address filters. Options includethe following:


- **mac_address mac_mask** - Specify the MAC address and mask.

- **any** - Filters all Packets from all addresses.

- **mac_address** - Specifies a MAC address in 3x4 dotted hexadecimal notation (hhhh.hhhh.hhhh).

- **mac_mask** - Specifies a MAC address mask in 3x4 dotted hexadecimal notation (hhhh.hhhh.hhhh).

- **0** - Requires an exact match to filter.

- **1** - Filters on any value.

- **protocol** - Configure a protocol field filter. Values include the following:


- **aarp** - Appletalk Address Resolution Protocol (0x80f3).

- **appletalk** - Appletalk (0x809b).

- **arp** - Address Resolution Protocol (0x806).

- **ip** - Internet Protocol Version 4 (0x800).

- **ipx** - Internet Packet Exchange (0x8137).

- **lldp** - LLDP (0x88cc).

- **novell** - Novell (0x8138).

- **rarp** - Reverse Address Resolution Protocol (0x8035).

- **protocol_num** An integer corresponding to a MAC protocol. Values range from **0 to 65535**.

- **log** Triggers an informational log message to the console about the matching packet.


**Examples**


- This command appends a permit statement at the end of the ACL. The deny statement drops all **aarp** packets from **10.1000.0000** through **10.1000.FFFF** to any host.

```
`switch(config)# **mac access-list text1**
switch(config-mac-acl-text1)# **deny 10.1000.0000 0.0.FFFF any aarp**`
```

- This command inserts a permit statement with the sequence number **25**. The deny statement drops all packets through the interface.

```
`switch(config-mac-acl-text1)# **25 deny any any**`
```


### deny (Standard IPv4 ACL)


The **deny** command adds a deny rule to the Standard IPv4 Access Control List (ACL) Configuration Mode. Standard ACL rules filter on the source field.


Interfaces with an applied ACL drop packets filtered by a **deny** rule. Sequence numbers determine rule placement in the ACL. Sequence numbers for commands without numbers derive from adding **10** to the number of the ACL last rule.


The **no deny** and **default deny** commands remove the specified rule from the Standard IPv4 Access Control List (ACL) Configuration Mode. The no sequence number (ACLs) command also removes the specified rule from the ACL.


**Command Mode**


Std-ACL Configuration


**Command Syntax**


[seq_num] deny source_addr log


no deny source_addr log


default deny source_addr log


**Parameters**


- **seq_num** - Specify the sequence number assigned to the rule. Options include the following:


- **no parameter** - A number derived by adding **10** to the number of the ACL last rule.

- **1 - 4294967295** - A number assigned to entry.

- **source_addr**- Specify a source address filter. Options include the following:


- **network_addr** - Specify a subnet address as a CIDR or address-mask.

- **any** Filter packets from all addresses.

- **host** **ip_addr** - Specify an IP address in dotted decimal notation.

Subnet addresses support noncontinuous masks.

- **log** - Triggers an informational log message to the console about the matching packet.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.


**Example**


This command appends a **deny** statement at the end of the ACL. The **deny** statement drops packets from **10.10.1.1/24**.

```
`switch(config)# **ip access-list standard text1**
switch(config-std-acl-text1)# **deny 10.1.1.1/24**
switch(config-std-acl-text1)#`
```


### deny (Standard IPv6 ACL)


The **deny**command adds a deny rule to the Standard IPv6 Access Control List (ACL) Configuration Mode. Standard ACL rules filter on the source field.


Interfaces with an applied ACL drop packets filtered by a **deny** rule. Sequence numbers determine rule placement in the ACL. Sequence numbers for commands without numbers derive from adding **10** to the number of the ACL's last rule.


The **no deny** and **default deny** commands remove the specified rule from the Standard IPv6 Access Control List (ACL) Configuration Mode. The no <sequence number> (ACLs) command also removes the specified rule from the ACL.


**Command Mode**


Std-IPv6-ACL Configuration


**Command Syntax**


seq_num deny source_addr


no deny source_addr


default deny source_addr


**Parameters**


- **seq_num** Sequence number assigned to the rule. Options include:


- **no parameter** - A Number derived by adding **10** to the number of the ACL's last rule.

- **1 - 4294967295** - The number assigned to entry.

- **source_addr**- The Source address filter configured for the ACL. Options include:


- **ipv6_prefix** - IPv6 address with prefix length (CIDR notation).

- **any** - Filter all packets from all addresses.

- **host** **ipv6_addr** - Specify the IPv6 host address.


**Example**


This command appends a **deny** statement at the end of the ACL. The **deny** statement drops packets from **2103::/64**.

```
`switch(config)# **ipv6 access-list standard text1**
switch(config-std-acl-ipv6-text1)# **deny 2103::/64**
switch(config-std-acl-ipv6-text1)#`
```


### description (route map)


The **description** command adds a text string to the configuration mode route map. The string has no functional impact on the route map.


The **no description** and **default description** commands remove the text string from the configuration mode route map by deleting the corresponding **description** command from ***running-config***.


**Command Mode**


Route-Map Configuration


**Command Syntax**


description label_text


no description


default description


**Parameter**


**label_text** Character string assigned to the route map configuration.


**Related Command**


route-map


**Example**


These commands add description text to the **XYZ-1** route map.

```
`switch(config)# **route-map XYZ-1**
switch(config-route-map-XYZ-1)# **description This is the first map.**
switch(config-route-map-XYZ-1)# **exit**
switch(config)# **show route-map XYZ-1**
route-map XYZ-1 permit 10
  Description:
    description This is the first map.
  Match clauses:
  Set clauses:
switch(config)#`
```


### hardware access-list resource sharing vlan in


The **hardware access-list resource sharing vlan in** command enables the IPv4 Ingress Sharing of hardware resources on the switch when the same ACL applies to different VLANs.


The **no hardware access-list resource sharing vlan in** command disables the IPv4 Ingress Sharing of hardware resources on the switch.


**Command Mode**


Global Configuration


**Command Syntax**


hardware access-list resource sharing vlan [ipv4 | ipv6] in


no hardware access-list resource sharing vlan in


**Guidelines**


- Ccompatible only with the DCS-7010 and DCS-7050x series switches.

- Enabling IPv4 Ingress Sharing requires the restart of software agents on the platform. This is a disruptive process and impacts traffic forwarding.


Use the **show platform trident** command to verify the Ingress IPv4 Sharing information.


### hardware access-list resource sharing vlan ipv4 out


The **hardware access-list resource sharing vlan ipv4 out** command enables IPv4 Egress RACL TCAM sharing on the switch.


The **no hardware access-list resource sharing vlan ipv4 out** command disables the IPv4 Egress RACL TCAM sharing on the switch. By default, the switch enables IPv4 Egress RACL sharing.


**Command Mode**


Global Configuration


**Command Syntax**


hardware access-list resource sharing vlan ipv4 out


no hardware access-list resource sharing vlan ipv4 out


**Guidelines**


- Compatible only with the DCS-7280E and DCS-7500E series switches.

- Disabling IPv4 RACL sharing requires the restart of software agents on the platform. This is a disruptive process and impacts traffic forwarding.

- Enabling IPv4 RACL sharing, if previously disabled from the default configuration, requires the restart of software agents on the platform. This is a disruptive process and impacts traffic forwarding. Enabling IPv4 RACL sharing if uRPF is configured disables uRPF.

- Use the **show running-config all | include sharing** command to verify whether or not sharing for egress IPv4 RACLs is enabled.


**Example**


This command verifies if IPv4 RACL sharing is enabled or disabled.

```
`switch# **show running-config all | include sharing**

hardware access-list resource sharing vlan ipv4 out
                        ---->It returns the following output if IPv4 RACL sharing is enabled.`
```


### hardware access-list update default-result permit


The **hardware access-list update default-result permit** command configures the switch to permit all traffic on Ethernet and VLAN interfaces with ACLs applied to them while modifying the ACLs. Permits traffic when modifying the ACL using one of the **ip access-list** commands, and ends when exiting the ACL Configuration Mode and rules populated in hardware. EOS disables this by default.


The **no hardware access-list update default-result permit** and **default hardware access-list update default-result permit** commands restore the switch to the default state and blocks traffic during ACL modifications by removing the corresponding **hardware access-list update default-result permit** command from the ***running-config***.


**Command Mode**


Global Configuration


**Command Syntax**


hardware access-list update default-result permit


no hardware access-list update default-result permit


default hardware access-list update default-result permit


**Restrictions**


This command is available on the Arista 7050X, 7060X, 7150, 7250X, 7280, 7280R, 7300X, 7320X, and 7500 series switches.


When enabled, static NAT, and ACL-based mirroring are affected during ACL updates.


**Example**


This command configures a 7150 series switch to permit all traffic on Ethernet and VLAN interfaces with applied ACLs while modifying the ACLs.

```
`switch(config)# **hardware access-list update default-result permit**
switch(config)#`
```


### hardware counter feature acl out


The **hardware counter feature acl out** command enables egress ACL hardware counters for IPv4 or IPv6 and count the number of packets matching rules associated with egress ACLs applied to various interfaces on a switch.


The **no hardware counter feature acl out** and **default hardware counter feature acl out** commands disable or return the egress ACL hardware counters to the default state.


**Command Mode**


Global Configuration


**Command Syntax**


hardware counter feature acl out [options [ipv4 | ipv6]


no hardware counter feature acl out [options [ipv4 | ipv6]


default hardware counter feature acl out [options [ipv4 | ipv6]


**Parameters**


- **options** - ACL hardware counter options include the following:


- **ipv4** - Specify an IPv4 address.

- **ipv6** - Specify an IPv4 address.


**Examples**


- This command enables IPv4 egress ACL hardware counters.

```
`switch(config)# **hardware counter feature acl out ipv4**
switch(config)#`
```

- This command disables IPv4 egress ACL hardware counters.

```
`switch(config)# **no hardware counter feature acl out ipv4**
switch(config)#`
```


### ip access-group (Service ACLs)


The **ip access-group** (Service ACLs) command configures a Service ACL to apply to a control-plane service. Specify the service by the command mode used to apply the Service ACL.


The **no ip access-group** and **default ip access-group** commands remove the corresponding **ip access-group** (Service ACLs) command from ***running-config***.


**Command Mode**


Mgmt-SSH Configuration


Mgmt-API Configuration


Router-BGP Configuration


Router-OSPF Configuration


Router-IGMP Configuration


MPLS-LDP Configuration


Queue-Monitor-Streaming Configuration


MPLS-Ping Configuration


Mgmt-Telnet Configuration


**Command Syntax**


ip access-group  acl_name [vrfvrf_name][in]


no ip access-group acl_name [vrfvrf_name][in]


default ip access-group acl_name [vrfvrf_name][in]


**Parameters**


Parameters vary by process.


- **acl_name** - Specify the name of the Service ACL assigned to control-plane service.

- **vrf** **vrf_name** - Specifies the VRF to apply the Service ACL.

- **in** - Specifies inbound connections or packets only. Requires a keyword for SSH and Telnet services.


**Example**


These commands apply the Service ACL **bgpacl** to the BGP routing protocol in VRF **purple**.

```
`(config)# **router bgp 5**
(config-router-bgp)# **vrf purple**
(config-router-bgp-vrf-purple)# **ip access-group bgpacl**`
```


For additional configuration examples, see Configuring Service ACLs and Displaying Status and Counters.


### ip access-group


The **ip access-group** command applies an IPv4 or standard IPv4 Access Control List (ACL) to an interface or subinterface in the Interface Configuration Mode.


The **no ip access-group** and **default ip access-group** commands remove the corresponding **ip access-group** command from ***running-config***.


**Command Mode**


Interface-Ethernet Configuration


Interface-Port-Channel Configuration


Interface-VLAN Configuration


**Command Syntax**


ip access-group list_name[direction [in | out]]


no ip access-group list_name[direction [in | out]]


default ip access-group list_name [direction [in | out]]


**Parameters**


- **list_name** - Specify the name of ACL assigned to interface.

- direction Transmission direction of packets, relative to interface. Valid options include the following:


- **in** - Inbound packets.

- **out** - Outbound packets.


**Considerations**


Filtering of outbound packets by ACLs not supported on Petra platform switches.


Filtering of outbound packets by ACLs on FM6000 switches supported on physical interfaces only (Ethernet and port channels).


ACLs on sub-interfaces are supported on DCS-7280E, DCS-7500E, DCS-7280R, and DCS-7500R.


**Example**


These commands apply the IPv4 ACL named **test2** to **interface ethernet 3**.

```
`switch(config)# **interface ethernet 3**
switch(config-if-Et3)# **ip access-group test2 in**
switch(config-if-Et3)#`
```


### ip access-list


The **ip access-list** command places the switch in ACL Configuration Mode, a group change mode that modifies an IPv4 access control list. The command specifies the name of the IPv4 ACL that subsequent commands modify and creates an ACL if it references a nonexistent list. All changes in a group change mode edit session are pending until the end of the session.


The **exit** command saves pending ACL changes to ***running-config***, then returns the switch to Global Configuration Mode. ACL changes are also saved by entering a different configuration mode.


The **abort** command discards pending ACL changes, returning the switch to Global Configuration Mode.


The **no ip access-list** and **default ip access-list** commands delete the specified IPv4 ACL.


**Command Mode**


Global Configuration


**Command Syntax**


ip access-list list_name


no ip access-list list_name


default ip access-list list_name


**Parameter**


**list_name** - Specify the name of the ACL. Must begin with an alphabetic character. Cannot contain spaces or quotation marks.


**Commands Available in ACL configuration mode:**


- deny (IPv4 ACL)

- no sequence number

- permit (IPv4 ACL)

- remark

- resequence (ACLs)

- show (ACL configuration modes)


**Related Commands:**


- ip access-list standard Enters ***std-acl*** configuration mode for editing standard IP ACLs.

- show ip access-lists Displays IP and standard ACLs.


**Examples**


- This command places the switch in ACL configuration mode to modify the **filter1** IPv4 ACL.

```
`switch(config)# **ip access-list filter1**
switch(config-acl-filter1)#`
```

- This command saves changes to **filter1** ACL, then returns the switch to Global Configuration Modee.

```
`switch(config-acl-filter1)# **exit**
switch(config)#`
```

- This command discards changes to **filter1**, then returns the switch to Global Configuration Mode.

```
`switch(config-acl-filter1)# **abort**
switch(config)#`
```


### ip access-list standard


The **ip access-list standard** command places the switch in STD-ACL Configuration Mode, a group change mode that modifies a standard IPv4 access control list. The command specifies the name of the standard IPv4 ACL that subsequent commands modify, and creates an ACL if it references a nonexistent list. All group change mode edit session changes are pending until the session ends.


The **exit** command saves pending ACL changes to ***running-config***, then returns the switch to Global Configuration Mode. Pending changes are also saved by entering a different configuration mode.


The **abort** command discards pending ACL changes, returning the switch to global configuration mode.


The **no ip access-list standard** and **default ip access-list standard** commands delete the specified ACL.


**Command Mode**


Global Configuration


**Command Syntax**


ip access-list standard list_name


no ip access-list standard list_name


default ip access-list standard list_name


**Parameter**


**list_name** - Specify the name of standard ACL. Must begin with an alphabetic character. Cannot contain spaces or quotation marks.


**Commands Available in std-ACL configuration mode:**


- deny (Standard IPv4 ACL)

- no sequence number

- permit (Standard IPv4 ACL)

- remark

- resequence (ACLs)

- show (ACL configuration modes)


**Related Commands**


- ip access-list - Enters ACL configuration mode for editing IPv4 ACLs.

- show ip access-lists - Displays IPv4 and standard IPv4 ACLs.


**Examples**


- This command places the switch in std-ACL configuration mode to modify the **filter2** IPv4 ACL.

```
`switch(config)# **ip access-list standard filter2**
switch(config-std-acl-filter2)#`
```

- This command saves changes to **filter2** ACL, then returns the switch to the Global Configuration Mode.

```
`switch(config-std-acl-filter2)# **exit**
switch(config)#`
```

- This command discards changes to **filter2**, then returns the switch to the Global Configuration Mode.

```
`switch(config-std-acl-filter2)# **abort**
switch(config)#`
```


### ip prefix-list


The **ip prefix-list** command creates a prefix list or adds an entry to an existing list. Route map match commands use prefix lists to filter routes for redistribution into OSPF, RIP, or BGP domains.


A prefix list comprises all prefix list entries with the same label. The sequence numbers of the rules in a prefix list specify the order for applying rules to a route evaluated by the match command.


The **no ip prefix-list** and **default ip prefix-list**commands delete the specified prefix list entry by removing the corresponding **ip prefix-list** statement from ***running-config***. If the **no** or **default ip prefix-list** command does not list a sequence number, the command deletes all entries of the prefix list.


**Command Mode**


Global Configuration


**Command Syntax**


ip prefix-list list_name [deny | permit] [seq index]  network_addr [mask] resequence seq_number remark comment


no ip prefix-list list_name seq [index]


default ip prefix-list list_name seq [index]


**Parameters**


- **list_name** - Specify a name for the prefix list.

- **seq** **seq_num**- Specify the sequence number for the prefix list entry Value ranges from **0** to **65535**.

- **permit | deny** - Specifies route access when a route matches IP prefix list. Options include:


- **permit** - Allows access when matching the specified subnet.

- **deny** - Denies access when matching the specified subnet.

- **network_addr** - Specify the subnet to filter routes. Use either a CIDR or address-mask format.

- **MASK** - Specifies the range of the prefix to be matched.


- **no parameter** Exact match with the subnet mask is required.

- **eq** **mask_e** Prefix length is equal to **mask_e**.

- **ge** **mask_g** Range is from **1** to **32**.

- **le** **mask_l** Range is from **subnet** mask length to **mask_l**.

- **ge** **mask_l** **le** **mask_g** Range is from **mask_g** to **mask_l**.

- **mask_e**, **mask_l**, and **mask_g** range from **1** to **32**. When **le** and **ge** are specified, **subnet** **mask** **mask_g**>**mask_l**.

- **remark comment** - Add a comment to the prefix list configuration.


**Example**


- This command places the switch in IPv4 prefix list configuration mode to create an IPv4 prefix list named **route-one**.

```
`switch(config)# **ip prefix-list route-one**
switch(config-ip-pfx)#`
```

- These commands create four different rules for the prefix-list named **route-one**.

```
`switch(config)# **ip prefix-list route-one**
switch(config-ip-pfx)# **seq 10 deny 10.1.1.0/24**
switch(config-ip-pfx)# **seq 20 deny 10.1.0.0/16**
switch(config-ip-pfx)# **seq 30 permit 12.15.4.9/32**
switch(config-ip-pfx)# **seq 40 deny 1.1.1.0/24**`
```


### ipv6 access-group


The **ipv6 access-group**command applies an IPv6 or standard IPv6 Access Control List (ACL) to the configuration mode interface.


The **no ipv6 access-group** and **default ipv6 access-group** commands remove the corresponding **ipv6 access-group** command from ***running-config***.


**Command Mode**


Interface-Ethernet Configuration


Interface-Port-Channel Configuration


Interface-VLAN Configuration


**Command Syntax**


**ipv6 access-group list_name [in | out]**


**no ipv6 access-group list_name [in | out]**


**default ipv6 access-group list_name [in | out]**


**Parameters**


- **list_name** - Specify the name of the ACL assigned to interface.

- **[in | out]** - Specify the transmission direction of packets, relative to interface. Valid options include the following:


- **in** Inbound packets.

- **out** Outbound packets.


**Examples**


These commands assign the IPv6 ACL named **test2** to the **interface ethernet 3**.

```
`switch(config)# **interface ethernet 3**
switch(config-if-Et3)# **ipv6 access-group test2 in**
switch(config-if-Et3)#`
```


### ipv6 access-group (Service ACLs)


The **ipv6 access-group** (Service ACLs) command configures an IPv6 or standard IPv6 Service ACL to be applied by a control-plane service. Specify the service with the command mode to apply the Service ACL.


The **no ipv6 access-group** (Service ACLs) and **default ipv6 access-group** (Service ACLs) commands remove the corresponding **ipv6 access-group**(Service ACLs) command from ***running-config***.


**Command Mode**


Mgmt-SSH Configuration


Mgmt-API Configuration


Router-BGP Configuration


Router-OSPF Configuration


MPLS-LDP Configuration


Queue-Monitor-Streaming Configuration


MPLS-Ping Configuration


Mgmt-Telnet Configuration


**Command Syntax**


ipv6 access-group ipv6_acl_name [vrf vrf_name][in]


no ipv6 access-group [ipv6_acl_name][vrfvrf_name][in]


default ipv6 access-group ipv6_acl_name [vrf vrf_name][in]


**Parameters**


Parameters vary by process.


- **ipv6_acl_name** - Specify the name of the IPv6 Service ACL assigned to control-plane service.

- **vrf** **vrf_name** - Specifies the VRF to apply the Service ACL.

- **in** - Specifies inbound connections or packets only and requires a keyword for SSH and Telnet services.


**Example**


These commands apply the IPv6 Service ACL **bgpacl** to the BGP routing protocol in VRF **purple**.

```
`(config)# **router bgp 5**
(config-router-bgp)# **vrf purple**
(config-router-bgp-vrf-purple)# **ipv6 access-group bgpacl**`
```


For additional configuration examples, see Configuring Service ACLs and Displaying Status and Counters.


### ipv6 access-list


The **ipv6 access-list** command places the switch in ***IPv6-ACL*** Configuration Mode, a group change mode that modifies an IPv6 access control list. The command specifies the name of the IPv6 ACL that subsequent commands modify and creates an ACL if it references a nonexistent list. All changes in a group change mode edit session pend until the end of the session.


The **exit** command saves pending ACL changes to ***running-config***, then returns the switch to global configuration mode. ACL changes are also saved by entering a different configuration mode.


The **abort** command discards pending ACL changes, returning the switch to Global Configuration Mode.


The **no ipv6 access-list** and **default ipv6 access-list** commands delete the specified IPv6 ACL.


**Command Mode**


Global Configuration


**Command Syntax**


ipv6 access-list list_name


no ipv6 access-list **list_name**


default ipv6 access-list list_name


**Parameters**


**list_name** - Specify a name for the ACL. Must begin with an alphabetic character and cannot contain spaces or quotation marks.


**Commands Available in IPv6-ACL configuration mode:**


- deny (IPv6 ACL)

- no <sequence number> (ACLs)

- permit (IPv6 ACL)

- remark

- resequence (ACLs)

- show (ACL configuration modes)


**Related Commands**


- ipv6 access-list standard Enters ***std-ipv6-acl*** configuration mode for editing standard IPv6 ACLs.

- show ipv6 access-lists Displays IPv6 and standard IPv6 ACLs.


**Examples**


- This command places the switch in IPv6-ACL configuration mode to modify the **filter1** IPv6 ACL.

```
`switch(config)# **ipv6 access-list filter1**
switch(config-ipv6-acl-filter1)#`
```

- This command saves changes to **filter1** ACL, then returns the switch to global configuration mode.

```
`switch(config-ipv6-acl-filter1)# **exit**
switch(config)#`
```

- This command discards changes to **filter1**, then returns the switch to global configuration mode.

```
`switch(config-ipv6-acl-filter1)# **abort**
switch(config)#`
```


### ipv6 access-list standard


The **ipv6 access-list standard** command places the switch in std-IPv6-ACL-configuration mode, a group change mode that modifies a standard IPv6 access control list. The command specifies the name of the standard IPv6 ACL that subsequent commands modify and creates an ACL if it references a nonexistent list. All group change mode edit session changes are pending until the session ends.


The **exit** command saves pending ACL changes to ***running-config***, then returns the switch to Global Configuration Mode. Pending changes are also saved by entering a different configuration mode.


The **abort** command discards pending ACL changes, returning the switch to global configuration mode.


The **no ipv6 access-list standard** and **default ipv6 access-list standard** commands delete the specified ACL.


**Command Mode**


Global Configuration


**Command Syntax**


ipv6 access-list standard list_name


no ipv6 access-list standard list_name


default ipv6 access-list standard list_name


**Parameters**


**list_name** - Specify a name for the ACL. Must begin with an alphabetic character and cannot contain spaces or quotation marks.


**Commands Available in std-IPv6-ACL configuration mode:**


- deny (Standard IPv6 ACL)

- no <sequence number> (ACLs)

- permit (Standard IPv6 ACL)

- remark

- resequence (ACLs)

- show (ACL configuration modes)


**Related Commands**


- ipv6 access-list Enters IPv6-ACL configuration mode for editing IPv6 ACLs.

- show ipv6 access-lists Displays IPv6 and standard IPv6 ACLs.


**Examples**


- This command places the switch in Std-IPv6 ACL configuration mode to modify the **filter2** ACL.

```
`switch(config)# **ipv6 access-list standard filter2**
switch(config-std-ipv6-acl-filter2)#`
```

- This command saves changes to **filter2** ACL, then returns the switch to global configuration mode.

```
`switch(config-std-ipv6-acl-filter2)# **exit**
switch(config)#`
```

- This command discards changes to **filter2**, then returns the switch to global configuration mode.

```
`switch(config-std-ipv6-acl-filter2)# **abort**
switch(config)#`
```


### ipv6 prefix-list


The **ip prefix-list** command places the switch in ***IPv6 prefix-list*** configuration mode, which is a group change mode that modifies an IPv6 prefix list. The command specifies the name of the IPv6 prefix list that subsequent commands modify and creates a prefix list if it references a nonexistent list. All changes in a group change mode edit session are pending until the end of the session.


The **exit** command saves pending prefix list changes to ***running-config***, then returns the switch to global configuration mode. ACL changes are also saved by entering a different configuration mode.


The **abort** command discards pending changes, returning the switch to global configuration mode.


The **no ipv6 prefix-list** and **default ipv6 prefix-list** commands delete the specified IPv6 prefix list.


**Command Mode**


Global Configuration


**Command Syntax**


ipv6 prefix-list list_name


no ipv6 prefix-list list_name


default ipv6 prefix-list list_name


**Parameter**


**list_name** Name of prefix list. Must begin with an alphabetic character. Cannot contain spaces or quotation marks.


**Commands Available in IPv6-pfx configuration mode:**


- deny (IPv6 Prefix List)

- permit (IPv6 Prefix List)

- seq (IPv6 Prefix Lists)


**Examples**


- This command places the switch in ***IPv6 prefix-list*** configuration mode to modify the **route-five** prefix list.

```
`switch(config)# **ipv6 prefix-list route-five**
switch(config-ipv6-pfx)#`
```

- This command saves changes to the prefix list, then returns the switch to global configuration mode.

```
`switch(config-ipv6-pfx)# **exit**
switch(config)#`
```

- This command saves changes to the prefix list, then places the switch in ***interface-ethernet*** mode.

```
`**switch(config-ipv6-pfx)# interface ethernet 3
switch(config-if-Et3)#**`
```

- This command discards changes to the prefix list, then returns the switch to global configuration mode.

```
`switch(config-ipv6-pfx)# **abort**
switch(config)#`
```


### mac access-group


The **mac access-group** command applies a MAC Access Control List (MAC ACL) when in the Interface Configuration Mode.


The **no mac access-group** and **default mac access-group** commands remove the specified **mac access-group** command from ***running-config***.


**Command Mode**


Interface-Ethernet Configuration


Interface-Port-Channel Configuration


**Command Syntax**


mac access-group list_name [direction [in | out]]


no mac access-group list_name[direction [in | out]]


default mac access-group list_name [direction [in | out]]


**Parameters**


- **list_name** - Specify the name of MAC ACL.

- **direction** - Specify the transmission direction of packets, relative to interface. Valid options include:


- **in** Inbound packets.

- **out** Outbound packets.


**Restrictions**


Only Helix, Trident, and Trident II platform switches support filtering of outbound packets by MAC ACLs.


**Example**


These commands assign the MAC ACL named **mtest2** to **interface ethernet 3** to filter inbound packets.

```
`switch(config)# **interface ethernet 3**
switch(config-if-Et3)# **mac access-group mtest2 in**
switch(config-if-Et3)#`
```


### mac access-list


The **mac access-list** command places the switch in ***MAC-ACL*** Configuration Mode, a group change mode that modifies a MAC access control list. The command specifies the name of the MAC ACL that subsequent commands modify and creates an ACL if it references a nonexistent list. All changes in a group change mode edit session are pending until the end of the session.


The **exit** command saves pending ACL changes to ***running-config***, then returns the switch to Global Configuration Mode. ACL changes are also saved by entering a different configuration mode.


The **abort** command discards pending ACL changes, returning the switch to Global Configuration Mode.


The **no mac access-list** and **default mac access-list**commands delete the specified list.


**Command Mode**


Global Configuration


**Command Syntax**


mac access-list list_name


no mac access-list list_name


default mac access-list list_name


**Parameter**


**list_name** - Specify the name of the MAC ACL. Names must begin with an alphabetic character and cannot contain a space or quotation mark.


**Commands Available in MAC-ACL Configuration Mode:**


- deny (MAC ACL)

- no <sequence number> (ACLs)

- permit (MAC ACL)

- remark

- resequence (ACLs)

- show (ACL configuration modes)


**Examples**


- This command places the switch in ***MAC-ACL*** configuration mode to modify the **mfilter1** MAC ACL.

```
`switch(config)# **mac access-list mfilter1**
switch(config-mac-acl-mfilter1)#`
```

- This command saves changes to **mfilter1** ACL, then returns the switch to global configuration mode.

```
`switch(config-mac-acl-mfilter1)# **exit**
switch(config)#`
```

- This command saves changes to **mfilter1** ACL, then places the switch in ***interface-ethernet*** configuration mode.

```
`switch(config-mac-acl-mfilter1)# **interface ethernet 3**
switch(config-if-Et3)#`
```

- This command discards changes to **mfilter1**, then returns the switch to global configuration mode.

```
`switch(config-mac-acl-mfilter1)# **abort**
switch(config)#`
```


### match (route-map)


The **match** command creates a route map statement entry that specifies one route filtering command. When a statement contains multiple match commands, the permit or deny filter applies to a route only if the properties equal the corresponding parameters in each **match** command. When a route properties do not equal the command parameters, the route is evaluated against the next statement in the route map, as determined by sequence number. If all statements fail to permit or deny the route, the route is denied.


The **no match** and **default match** commands remove the **match**command from the configuration mode route map statement by deleting the corresponding command from ***running-config***.


Note: The route map configuration supports only standard ACL.


**Command Mode**


Route-Map Configuration


**Command Syntax**


match condition


no match condition


default match condition


**Parameters**


- **condition** - Specifies criteria for evaluating a route. Options include the following:


- **aggregate-role** - Specify the role in BGP contributor-aggregate relation. Options include the following:


- **contributor** - Specify BGP aggregate contributor.

- **aggregate-attributes** - Specify the Route map to apply against the aggregate route.

- **as** **1** to **4294967295** - Specify the BGP Autonomous System number.

- **as-path** **path_name** - Specify the BGP Autonomous System path access list.

- as-path length { <= | = | => } **length**


- <= - Length of AS path must be less than or equal to specified value.

- = - Length of AS path must be equal to specified value.

- => Length of AS path must be equal to or greater than specified value.

- **length** - Value for AS path length comparison (0-4000).

- **community** **name** BGP community. Options include the following:


- **listname** - Specify the BGP community.

- **listname** - Specify the **exact-match** BGP community. The list must match the present set.

- **extcommunity** **listname** - Specify the BGP extended community. Options include the following:


- **listname** - Specify the BGP community.

- **listname** - Specify the **exact-match** BGP community. The list must match the present set.

- **interface** **intf_name** - Specifies an interface. Options include the following::


- **ethernet** **e_num** - Specify the Ethernet interface.

- **loopback** **l_num** - Specify the Loopback interface.

- **port-channel** **p_num** - Specify the Port channel interface.

- **vlan** **v_num** - Specify the VLAN interface.


**invert-result** - Specify the Invert sub route map result.

- **ip address** **LIST** - Specify the IPv4 address filtered by an ACL or prefix list. Options include the following:


- **access-list** **acl_name** - Specify the IPv4 address filtered by access control list (ACL).

- **prefix-list** **plv4_name**- Specify the IPv4 address filtered by IP prefix list.

- **ip next-hop prefix-list** **plv4_name** - Specify the IPv4 next-hop filtered by IP prefix list.

- **ip resolved-next-hop prefix-list** **plv4_name** - Specify the IPv4 resolved next-hop filtered by IP prefix list.

- **ipv6 address prefix-list** **plv6_name** - Specify the IPv6 address filtered by IPv6 prefix list.

- **ipv6 next-hop prefix-list** **plv6_name** - Specify the IPv6 next-hop filtered by IPv6 prefix list.

- **ipv6 resolved-next-hop prefix-list** **plv6_name** - Specify the IPv6 resolved nexthop filtered by IPv6 prefix list.

- **local-preference** **1** to **4294967295** - Specify the BGP local preference metric.

- **metric** **1** to **4294967295** - Specify the route metric.

- **metric-type** **OSPF_TYPE** - Specify the OSPF metric type. Options include the following:


- **type-1** OSPF type 1 metric.

- **type-2** OSPF type 2 metric.

- **source-protocol** **protocol_type** - Specify the Routing protocol of route source. Options include the following:


- **bgp**

- **connected**

- **ospf**

- **rip**

- **static**

- **tag** **1** to **4294967295** Route tag.


**Related Command**


route-map


**Examples**


- This command creates a ***route map*** match rule that filters routes from BGP **as 15**.

```
`switch(config)# **route-map map1**
switch(config-route-map-map1)# **match as 15**
switch(config-route-map-map1)#`
```

- This command adds a **route-map** match rule that the AS path be less than or equal to 300.

```
`switch(config-route-map-map1)# **match as-path length <= 300**
switch(config-route-map-map1)#`
```


### no sequence number


The **no sequence number** command removes the rule with the specified sequence number from the ACL. The **default <sequence number>** command also removes the specified rule.


**Command Mode**


ACL Configuration


IPv6-ACL Configuration


Std-ACL Configuration


Std-IPv6-ACL Configuration


MAC-ACL Configuration


**Command Syntax**


no line_num


default line_num


**Parameter**


**line_num** - Specify the sequence number of rule to delete. Values range from **1 - 4294967295**.


**Example**


This command removes statement **30** from the list.

```
`switch(config-acl-test1)# **show IP Access Lists test1**
  10 permit ip 10.10.10.0/24 any
  20 permit ip any host 10.20.10.1
  30 deny ip host 10.10.10.1 host 10.20.10.1
  40 permit ip any any
  50 remark end of list
Total rules configured: 5
  Configured on Ingress: Et1/1
  Active on     Ingress: Et1/1

switch(config-acl-test1)# **no 30**
switch(config-acl-test1)# **show IP Access Lists**
  20 permit ip any host 10.20.10.1
  40 permit ip any any
  50 remark end of list
Total rules configured: 4
  Configured on Ingress: Et1/1
  Active on     Ingress: Et1/1`
```


### permit (IPv4 ACL)


The **permit** command adds a permit rule to the configuration mode IPv4 Access Control List (ACL). Interfaces with the applied ACL accept packets filtered by a permit rule the ACL is applied. Sequence numbers determine rule placement in the ACL. Sequence numbers for commands without numbers derive from adding 10 to the number of the ACL last rule.


The **no permit** and **default permit** commands remove the specified rule from the configuration mode ACL. The no <sequence number> (ACLs) command also removes a specified rule from the ACL.


**Command Mode**


ACL Configuration


**Command Syntax**


seq_num permit protocol src_addr source_pt dest_addr dest_pt flags msg fragments tracked dscp_filter ttl_filter log


no permit protocol src_addr source_pt dest_addr dest_pt flags msg fragments tracked dscp_filter ttl_filter log


default permit protocol src_addr source_pt dest_addr dest_pt flags msg fragments tracked dscp_filter ttl_filter log


Commands use a subset of the listed fields and available parameters depend on specified protocol.


**Parameters**


- **seq_num**- Specify the sequence number assigned to the rule. Options include the following:


- **no parameter** - A number derived from adding **10** to the number of the ACL's last rule.

- **1 - 4294967295** - Specify the number assigned to entry.

- **protocol** - Specify the protocol field filter. Options include the following:


- **ahp**- Authentication Header Protocol (51)

- **gre** - Generic Routing Encapsulation

- **gtp** - GPRS Tunneling Protocol

- **icmp** - Internet Control Message Protocol (1)

- **igmp** -Internet Group Management Protocol (2)

- **ip** -Any Internet Protocol v4 (4)

- **ospf** -Open Shortest Path First (89)

- **pim** -Protocol Independent Multicast (103)

- **tcp** -Transmission Control Protocol (6)

- **udp** -User datagram protocol (17)

- **vlan** - Enter VLAN number and mask. VLAN value range from 1 to 4094, and mask value range from 0x000-0xFFF .

- **vrrp** - Virtual Router Redundancy Protocol (112).

- **protocol_num** -An integer corresponding to an IP protocol. Values range from **0 to 255**.

- **src_addr** and **dest_addr** - Specify the source and destination address filters. Options include the following:


- **network_addr** - Specify the subnet address (CIDR or address-mask).

- **any** - Filter packets from all addresses.

- **host** **ip_addr** - Specify the IP address in dotted decimal notation.

Source and destination subnet addresses support discontiguous masks.

- **source_port** and **dest_port** Source and destination port filters. varnames include:


- **any** - Specify all ports.

- **eq** **port-1** **port-2** ... **port-n** - Specify a list of ports. Maximum list size is 10 ports.

- **neq** **port-1** **port-2** ... **port-n** - Specify the set of all ports not listed. Maximum list size is 10 ports.

- **gt** **port** - Specify the set of ports with larger numbers than the listed port.

- **lt** **port** - Specify the set of ports with smaller numbers than the listed port.

- **range** **port_1** **port_2** - Specify the set of ports within a range.

- **fragments** -Filters packets with FO bit set (indicates a non-initial fragment packet).

- **flags** -Specify the flags bit filters (TCP packets). Use CLI syntax assistance (?) to display varnames.

- **msg** - Specify the message type filters (ICMP packets). Use CLI syntax assistance (?) to display varnames.

- **tracked** - Specify the rule filters packets in existing ICMP, UDP, or TCP connections.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.

- **dscp_filter** -Specify the rule filters packet by its DSCP value. Values include:


- **no parameter** - The rule does not use DSCP to filter packets.

- **dscp** **dscp_value** - Packets match if DSCP field in packet is equal to **dscp_value**.

- **ttl_filter** - Rule filters packet by its TTL (time-to-live) value. Values include:


- **ttl eq** **ttl_value** - Match packets if **ttl** in packet is equal to **ttl_value**.

- **ttl gt** **ttl_value** - Match packets if **ttl** in packet is greater than **ttl_value**.

- **ttl lt** **ttl_value** - Match packets if **ttl** in packet is less than **ttl_value**.

- **ttl neq** **ttl_value** - Match packets if **ttl** in packet is not equal to **ttl_value**.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.

- **log**-Specify to trigger an informational log message to the console about the matching packet.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.


**Examples**


- This command appends a **permit** statement at the end of the ACL. The **permit** statement passes all OSPF packets from **10.10.1.1/24** to any host.

```
`switch(config)# **ip access-list text1**
switch(config-acl-text1)# **permit ospf 10.1.1.0/24 any**
switch(config-acl-text1)#`
```

- This command inserts a **permit** statement with the sequence number **25**. The **permit** statement passes all PIM packets through the interface.

```
`switch(config-acl-text1)# **25 permit pim any any**
switch(config-acl-text1)#`
```

- These commands configure ACL to permit VLAN traffic between any source and destination host.

```
`switch(config)# **ip access-list acl1**
switch(config-acl-acl1)# **permit vlan 1234 0x0 ip any any**`
```


### permit (IPv6 ACL)


The **permit** command adds a permit rule to the configuration mode IPv6 Access Control List (ACL). Interfaces with the applied ACL accept packets filtered by a permit rule the ACL is applied. Sequence numbers determine rule placement in the ACL. Sequence numbers for commands without numbers derive from adding 10 to the number of the ACL last rule.


The **no permit** and **default permit** commands remove the specified rule from the configuration mode ACL. The no <sequence number> (ACLs) command also removes a specified rule from the ACL.


**Command Mode**


IPv6-ACL Configuration


**Command Syntax**


seq_num permit protocol src_addr source_pt dest_addr dest_pt flags msg hop tracked dscp_filter log


no permit protocol src_addr source_pt dest_addr dest_pt flag msg hop tracked dscp_filter log


default deny protocol src_addr source_pt dest_addr dest_pt flag msg hop tracked dscp_filter log


Note: Commands use a subset of the listed fields and available parameters depend on specified protocol.


**Parameters**


- **seq_num** - The sequence number assigned to the rule. Options include the following:


- **no parameter.Number is derived by adding 10 to the number of the ACL’s last rule.**

- **1 - 4294967295** Number assigned to entry.

- **protocol** Specify the protocol field filter. Options include the following:


- **icmpv6** - Internet Control Message Protocol for IPv6 (58).

- **ipv6** - Internet Protocol IPv6 (41).

- **ospf** - Open Shortest Path First (89).

- **tcp** - Transmission Control Protocol (6).

- **udp** - User Datagram Protocol (17).

- **vlan** - Enter VLAN number. Value ranges from 1 to 4094.

- **protocol_num** - Integer corresponding to an IP protocol. Values range from 0 to 255.

- **src_addr** and **dest_addr** - Specify the source and destination address filters. Options include the following:


- **ipv6_prefix** - Specify the IPv6 address with prefix length (CIDR notation).

- **any** - Specify the Packets from all addresses are filtered.

- **host** **ipv6_addr** - Specify the IPv6 host address.

- **source_pt** and **DEST_PT** - Specify the source and destination port filters. Options include the following:


- **any** All ports.

- **eq** **port-1** **port-2** ... **port-n** - Specify the list of ports. Maximum list size is 10 ports.

- **neq** **port-1** **port-2** ... **port-n** Specify the set of all ports not listed. Maximum list size is 10 ports.

- **gt** **port** - Specify theset of ports with larger numbers than the listed port.

- **lt** **port** - Specify the set of ports with smaller numbers than the listed port.

- **range** **port_1** **port_2** - Specify the set of ports whose numbers are in the range.

- **hop** - Filter using the packet’s hop-limit value. Options include the following:


- **no parameter** - The rule does not use hop limit to filter packets.

- **hop-limit eq** **hop_value** - Match packets if **hop-limit** value in packet equals **hop_value**.

- **hop-limit gt** **hop_value** - Match packets if **hop-limit** in packet is greater than **hop_value**.

- **hop-limit lt** **hop_value** - Match packets if **hop-limit** in packet is less than **hop_value**.

- **hop-limit neq** **hop_value** - Match packets if **hop-limit** in packet is not equal to **hop_value**.

- **flag** - Flag bit filters (TCP packets).

- **msg** - Message type filters (ICMPv6 packets).

- **tracked** The rule filters packets in existing ICMP, UDP, or TCP connections.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.

- **dscp_filter** The rule filters packet by its DSCP value. Options include the following:


- **no parameter** - The rule does not use DSCP to filter packets.

- **dscp** **dscp_value** - Match packets if DSCP field in packet is equal to **dscp_value**.


- **flow_label** - The rule permits packets with IPv6 flow labels matching an exact value or a pattern based on a mask. varnames include:


- **no parameter** - The rule does not use IPv6 flow labels to filter packets.

- **flow-label eq** **ipv6_flow_label** - The IPv6 flow label must exactly match **ipv6_flow_label**. Flow labels can range from 0 to 1048575.

- **flow-label** **ipv6_flow_label** **flow_label_mask** The IPv6 flow label must match a pattern defined by **ipv6_flow_label** and **flow_label_mask**. The mask is an inverse mask. Where the mask has a 0 bit, the flow label must match the **ipv6_flow_label** value, and where the mask has a 1 bit, the corresponding bit in the flow label is ignored. For example, if **ipv6_flow_label** is 10 (0b01010 in binary) and **flow_label_mask** is 0x14 (0b10100 in binary), the rule matches flow labels described by 0b.1.10 where “.” is a wildcard and can be either 0 or 1. The flow labels that match include 10 (0b01010), 14 (0b0110), 26 (0b11010), and 30 (0b1110). Flow labels can range from 0 to 1048575 and flow label masks can range from 0x00000 to 0xfffff.

- **log** - Send an informational log message to the console when a packet matches.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.


**Examples**


- This command appends a **permit** statement at the end of the ACL. The **permit** statement passes all IPv6 packets with the source address 3710:249a:c643:ef11::/64 and with any destination address.

```
`switch(config)# **ipv6 access-list acl1**
switch(config-acl-acl1)# **permit ipv6 3710:249a:c643:ef11::/64 any**
switch(config-acl-acl1)# **exit**
switch(config)#`
```

- These commands configure ACL to permit VLAN traffic between any source and destination host.

```
`switch(config)# **ip access-list acl2**
switch(config-acl-acl2)# **permit ipv6 vlan 1234 0x0 ip any any**
switch(config-acl-acl2)# **exit**
switch(config)#`
```

- These commands add a rule to permit all IPv6 packets with flow label 23.

```
`switch(config)# **ipv6 access-list acl3**
switch(config-acl-acl3)# **permit ipv6 any any flow-label eq 23**
switch(config-acl-acl3)# **exit**
switch(config)#`
```

- These commands create a rule to permit all IPv6 packets matched by the flow label 23 and the mask 0x5678.

```
`switch(config)# **ipv6 access-list acl4**
switch(config-acl-acl4)# **permit ipv6 any any flow-label 23 0x5678**
switch(config-acl-acl4)# **exit**
switch(config)#`
```


### permit (IPv6 Prefix List)


The **permit**command adds a rule to the configuration mode IPv6 prefix list. Route map match commands use prefix lists to filter routes for redistribution into OSPF, RIP, or BGP domains. Routes are redistributed into the specified domain when they match the prefix that a **permit** statement specifies.


The **no permit** and **default permit** commands remove the specified rule from the prefix list. The **no** seq (IPv6 Prefix Lists) command also removes the specified rule from the prefix list.


**Command Mode**


IPv6-pfx Configuration


**Command Syntax**


seq_num permit ipv6_prefix mask


**Parameters**


- **seq_num** - Specify the sequence number assigned to the rule. Options include the following:


- **no parameter** - Number derived from adding 10 to the number of the list's last rule.

- **seq** **seq_num** - Specify the number from the **seq_num**. Value ranges from **0 to 65535**.

- **ipv6_prefix** - Specify the IPv6 prefix that filters the routes in CIDR notation.

- **mask** - Specify the range of the prefix to match.


- **no parameter** - Requires an exact match with the subnet mask.

- **eq** **mask_e** - Specify the prefix length equal to **mask_e**.

- **ge** **mask_g** - Specify the range from the **mask_g** to **128**.

- **le** **mask_l** - Specify the range from the **subnet** mask length to **mask_l**.

- **ge** **mask_l** **le** **mask_g** Range is from **mask_g** to **mask_l**.

- **mask_e**, **mask_l** and **mask_g** range from **1 to 128**.

- When **le** and **ge** are specified, the prefix list size **mask_g** **mask_l**.


**Example**


This command appends a **permit** statement at the end of the text1 prefix list. The **permit** statement allows redistribution of routes with the specified prefix.

```
`switch(config)# **ipv6 prefix-list route-five**
switch(config-ipv6-pfx)# **permit 3100::/64**
switch(config-ipv6-pfx)#`
```


### permit (MAC ACL)


The **permit** command adds a permit rule to the configuration mode MAC access control list packets through the interface to which the list is applied. Rule filters include protocol, source, and destination.


The **no permit** and **default permit** commands remove the specified rule from the configuration mode ACL. The no <sequence number> (ACLs) command also removes the specified rule from the ACL.


**Command Mode**


MAC-ACL Configuration


**Command Syntax**


seq_num permit source_addr dest_addr protocol log


no permit  source_addr dest_addr protocol log


default permit  source_addr dest_addr protocol log


**Parameters**


- **seq_num** - Specify the sequence number assigned to the rule. Options include the following:


- **no parameter** - Specify the number derived by adding **10** to the number of the ACL's last rule.

- **1 - 4294967295** - Specify the number assigned to entry.

- **source_addr** and **dest_addr**- Specify the source and destination address filters. Options include the following:


- **mac_address** **mac_mask** - Specify the MAC address and mask.

- **any** - Filter packets from all addresses.

- **mac_address** - Specifies a MAC address in 3x4 dotted hexadecimal notation (hhhh.hhhh.hhhh).

- **mac_mask** - Specifies a MAC address mask in 3x4 dotted hexadecimal notation (hhhh.hhhh.hhhh).

- **0** - Require an exact match to filter.

- **1** - Filter on any value.

- **protocol** - Specify the protocol field filter. Options include the following:


- **aarp** Appletalk Address Resolution Protocol (0x80f3).

- **appletalk** Appletalk (0x809b).

- **arp** Address Resolution Protocol (0x806).

- **ip** Internet Protocol Version 4 (0x800).

- **ipx** Internet Packet Exchange (0x8137).

- **lldp** LLDP (0x88cc).

- **novell** Novell (0x8138).

- **rarp** Reverse Address Resolution Protocol (0x8035).

- **protocol_num** Integer corresponding to a MAC protocol. Values range from **0 to 65535**.

- **log** - Specify to trigger an informational log message to the console about the matching packet.


**Examples**


- This command appends a **permit** statement at the end of the ACL. The **permit** statement passes all ***aarp*** packets from **10.1000.0000** through **10.1000.FFFF** to any host.

```
`switch(config)# **mac access-list text1**
switch(config-mac-acl-text1)# **permit 10.1000.0000 0.0.FFFF any aarp**
switch(config-mac-acl-text1)#`
```

- This command inserts a **permit** statement with the sequence number **25**. The **permit** statement passes all packets through the interface.

```
`switch(config-mac-acl-text1)# **25 permit any any**
switch(config-mac-acl-text1)#`
```


### permit (Standard IPv4 ACL)


The **permit** command adds a permit rule to a standard IPv4 Access Control List (ACL). Standard ACL rules filter on the source field.


Interfaces with the applied ACL accept packets filtered by a permit rule. Sequence numbers determine rule placement in the ACL. Sequence numbers for commands without numbers derive from adding ***10*** to the number of the ACL's last rule..


The **no permit** and **default permit** commands remove the specified rule from the ACL. The no <sequence number> (ACLs) command also removes the specified rule from the ACL.


**Command Mode**


Std-ACL Configuration


**Command Syntax**


[seq_num] permit [ source_addr network_addr [any | host] [log]


no permit [ source_addr network_addr [any | host] [log]


default permit [ source_addr network_addr [any | host][log]


**Parameters**


- **seq_num** - Specify the sequence number assigned to the rule. Options include the following:


- **no parameter** - A number derived from adding **10** to the number of the ACL's last rule.

- **1 - 4294967295** Number assigned to entry.

- **source_addr** - Specify the source address filter. Options include the following:


- **network_addr** - Specify the subnet address in CIDR or as an address-mask.

- **any** - Filter packets from all addresses.

- **host** **ip_addr** - Specify the IP address in dotted decimal notation.

Subnet addresses support discontiguous masks.

- **log** - Specify to trigger an informational log message to the console about the matching packet.


- Valid in ACLs applied to the control plane.

- Validity in ACLs applied to data plane varies by switch platform.


**Example**


This command appends a **permit** statement at the end of the ACL. The **permit** statement passes all packets with a source address of **10.10.1.1/24**.

```
`switch(config)# **ip access-list standard text1**
switch(config-std-acl-text1)# **permit 10.1.1.1/24**
switch(config-std-acl-text1)#`
```


### permit (Standard IPv6 ACL)


The **permit** command adds a permit rule to the standard IPv6 access control list. Standard ACL rules filter on the source field.


Interfaces with the applied ACL accept packets filtered by a permit rule. Sequence numbers determine rule placement in the ACL. Sequence numbers for commands without numbers derive from adding 10 to the number of the ACL's last rule.


The **no permit** and **default permit** commands remove the specified rule from the configuration mode ACL. The no <sequence number> (ACLs) command also removes the specified rule from the ACL.


**Command Mode**


Std-IPv6-ACL Configuration


**Command Syntax**


[seq_num] permit source_addr


no permit source_addr


default permit source_addr


**Parameters**


- **seq_num** - Specify the sequence number assigned to the rule. Options include the following:


- **no parameter** - The number derived by adding **10** to the number of the ACL's last rule.

- **1 - 4294967295** - The number assigned to entry.

- **source_addr** - Specify the source address filter. Options include the following:


- **ipv6_prefix** - Specify the IPv6 address with prefix length (CIDR notation).

- **any** - Filter packets from all addresses.

- **host** **ipv6_addr** - Specify the IPv6 host address.


**Example**


This command appends a **permit** statement at the end of the ACL. The **permit** statement drops packets with a source address of **2103::/64**.

```
`switch(config)# **ipv6 access-list standard text1**
switch(config-std-acl-ipv6-text1)# **permit 2103::/64**
switch(config-std-acl-ipv6-text1)#`
```


### remark


The **remark** command adds a non-executable comment statement into the pending ACL. Remarks entered without a sequence number are appended to the end of the list. Remarks with a sequence number insert into the list as specified by the sequence number.


The **default remark** command removes the comment statement from the ACL.


The **no remark** command removes the comment statement from the ACL. The command can specify the remark by content or by sequence number.


**Command Mode**


ACL Configuration


IPv6-ACL Configuration


Std-ACL Configuration


Std-IPv6-ACL Configuration


MAC-ACL Configuration


**Command Syntax**


remark text


line_num remark [text]


no remark text


default remark text


**Parameters**


- **text** The comment text.

- **line_num** Sequence number assigned to the remark statement. Value ranges from **1 - 4294967295**.


**Example**


This command appends a comment to the list.

```
`switch(config-acl-test1)# **remark end of list**
switch(config-acl-test1)# **show**
IP Access List test1
  10 permit ip 10.10.10.0/24 any
  20 permit ip any host 10.20.10.1
  30 deny ip host 10.10.10.1 host 10.20.10.1
  40 permit ip any any
  50 remark end of list`
```


### resequence (ACLs)


The **resequence** command assigns sequence numbers to rules in the configuration mode ACL. Command parameters specify the number of the first rule and the numeric interval between consecutive rules.


Maximum rule sequence number is **4294967295**.


**Command Mode**


ACL Configuration


IPv6-ACL Configuration


Std-ACL Configuration


Std-IPv6-ACL Configuration


MAC-ACL Configuration


**Command Syntax**


resequence [start_num [inc_num]]


**Parameters**


- **start_num** Sequence number assigned to the first rule. Default is **10**.

- **inc_num** Numeric interval between consecutive rules. Default is **10**.


**Example**


The **resequence** command re-numbers the list, starting the first command at number **100** and incrementing subsequent lines by **20**.

```
`switch(config-acl-test1)# **show**
IP Access List test1
  10 permit ip 10.10.10.0/24 any
  20 permit ip any host 10.20.10.1
  30 deny ip host 10.10.10.1 host 10.20.10.1
  40 permit ip any any
  50 remark end of list
switch(config-acl-test1)# **resequence 100 20**
switch(config-acl-test1)# **show**
IP Access List test1
  100 permit ip 10.10.10.0/24 any
  120 permit ip any host 10.20.10.1
  140 deny ip host 10.10.10.1 host 10.20.10.1
  160 permit ip any any
  180 remark end of list`
```


### route-map


The **route-map** command places the switch in Route-Map Configuration Mode, a group change mode that modifies a route map statement. The command specifies the name and number of the route map statement that subsequent commands modify and creates a route map statement if it references a nonexistent statement. All changes in a group change mode edit session pend until the end of the session.


Route maps define commands for redistributing routes between routing protocols. Use names, filter type (**permit** or **deny**), and sequence number to identify a route map statement. Statements with the same name are components of a single route map, and the sequence number determines the order in which the statements compare to a route.


The **exit** command saves pending route map statement changes to ***running-config***, then returns the switch to global configuration mode. Also, save ACL changes by entering a different configuration mode.


The **abort** command discards pending changes, returning the switch to global configuration mode.


The **no route-map** and **default route-map** commands delete the specified route map statement from ***running-config***.


Note: The route map configuration supports only standard ACL.


**Command Mode**


Global Configuration


**Command Syntax**


route-map  map_name [filter_type] [sequence_number]


no route-map  map_name [filter_type] [sequence_number]


default route-map map_name [filter_type][sequence_number]


**Parameters**


- **map_name** - Assign a label to the route map. Protocols reference this label to access the route map.

- **filter_type** - Specify the disposition of routes matching commands specified by route map statement.


- **permit** - Redistribute routes when they match route map statement.

- **deny** - Do not redistribute routes when they match route map statement.

- **no parameter** Assigns **permit** as the **filter_type**.


When a route does not match the route map criteria, EOS evaluates the next statement within the route map to determine the redistribution action for the route.


- **sequence_number** - Specify the route map position relative to other statements with the same name.


- **no parameter** - Assign the sequence number of 10 (default) to the route map.

- **1-16777215** - Specifies sequence number assigned to route map.


**Commands Available in Route-Map Configuration Mode:**


- continue (route map)

- match (route-map)

- set (route-map)


**Examples**


- This command creates the route map named **map1** and places the switch in route map configuration mode. This configures the route map as a permit map.

```
`switch(config)# **route-map map1 permit 20**
switch(config-route-map-map1)#`
```

- This command saves changes to **map1** route map, then returns the switch to Global Configuration Mode.

```
`switch(config-route-map-map1)# **exit**
switch(config)#`
```

- This command saves changes to **map1** route map, then places the switch in Interface-Ethernet Configuration Mode.

```
`switch(config-route-map-map1)# **interface ethernet 3**
switch(config-if-Et3)#`
```

- This command discards changes to **map1** route map, then returns the switch to Global Configuration Mode.

```
`switch(config-route-map-map1)# **abort**
switch(config)#`
```


### no seq (IPv6 Prefix Lists)


The **no seq** command removes the rule with the specified sequence number from the ACL. The **default seq** command also removes the specified rule.


The **seq** keyword provides a command option used at the beginning of deny (IPv6 Prefix List) and permit (IPv6 Prefix List) commands that places a new rule between two existing rules.


**Command Mode**


IPv6-pfx Configuration


**Command Syntax**


no seq line_num


default seq line_num


**Parameter**


**line_num** - Specify the sequence number of rule to delete. Valid rule numbers range from **0** to **65535**.


**Example**


These commands remove rule **20** from the **map1** prefix list, then displays the resultant list.

```
`switch(config)# **ipv6 prefix-list map1**
switch(config-ipv6-pfx)# **no seq 20**
switch(config-ipv6-pfx)# **exit**
switch(config)# **show ipv6 prefix-list map1**
ipv6 prefix-list map1
seq 10 permit 3:4e96:8ca1:33cf::/64
seq 15 deny 3:4400::/64
seq 30 permit 3:1bca:3ff2:634a::/64
seq 40 permit 3:1bca:1141:ab34::/64
switch(config)#`
```


### set (route-map)


The **set** command specifies modifications to routes selected for redistribution by the Route-Map Configuration Mode.


The **no set** and **default set** commands remove the specified **set** command from the Route-Map Configuration Mode statement by deleting the corresponding **set** command from ***running-config***.


**Command Mode**


Route-Map Configuration


**Command Syntax**


set condition [as-path prepend [num | auto]]


no set condition [as-path prepend [num | auto]]


default set condition[as-path prepend [num | auto]]


**Parameters**


- **condition** - Specifies the route modification parameter and value. Options include the following:


- **as-path prepend** - Specifies the BGP AS number prepended to as-path. For details, see the set as-path prepend command.


- **1 - 4294967295** - Specifies the BGP AS number to prepend.

- **auto** - Specifies to use the peer AS number for inbound and local AS for outbound to prepend.

- **distance** **1 - 255** - Specifies the protocol independent administrative distance.

- **ip next-hop** **ipv4_address** - Specifies the next-hop IPv4 address.


- peer-address - Specifies using BGP peering address as next hop IPv4 address.

- **ipv6 next-hop** **ipv6_address** - Specifies the next-hop IPv6 address.


- peer-address - Specifies using the BGP peering address as next hop IPv6 address.

- **local-preference** **1 - 4294967295** - Specifies the BGP local preference metric.

- **metric** **1 - 4294967295** - Specifies the route metric.

- **metric +** **1 - 4294967295** - Specifies adding specified value to current route metric.

- **metric -** **1 - 4294967295** - Specifies subtracting specified value to current route metric.

- **metric-type** **OSPF_TYPE** OSPF metric type. Options include the following:


- **type-1** - OSPF type 1 metric.

- **type-2** - OSPF type 2 metric.

- **origin** **O_TYPE** BGP origin attribute. Options include the following:


- **egp** - Exterior BGP route.

- **igp** - Interior BGP route.

- **incomplete** - BGP route of unknown origin.

- **tag** **1 - 4294967295** - Route tag.

- **weight** **1 - 65535** - BGP weight parameter.


**Related Commands**


- route-map enters the Route-Map Configuration Mode.

- set (route-map) specifies community modifications for the redistributed routes.

- set community (route-map) specifies extended community modifications for the redistributed routes.


**Example**


This command creates a route map entry that sets the local preference metric to **100** on redistributed routes.

```
`switch(config)# **route-map map1**
switch(config-route-map-map1)# **set local-preference 100**
switch(config-route-map-map1)#`
```


### set as-path match


The **set as-path match** command configures the **as_path** attribute for prefixes either received from a BGP neighbor or advertised to a BGP neighbor in the Route-Map Configuration Mode.


The **no set as-path match** command removes the AS path specified for the BGP prefix.


**Command Mode**


Route-Map Configuration


**Command Syntax**


set as-path match [all replacement [none| auto]] as_path


set as-path match[all replacement [none| auto]] as_path


**Parameters**


- **none** - Replaces the **as_path** of the matching routes with a null or an empty **as_path**.

- **auto** - Applying the specific route map as an inbound policy to a corresponding BGP neighbor statement, then replace the **as_path** of the prefixes received from this neighbor with the neighbor AS number. If applying this route map as an outbound policy to a corresponding neighbor statement, then replace the **as_path** of the prefixes advertised to this neighbor with the locally configured AS number.

- **as_path** - Replaces the AS-Path of the matching routes with an arbitrary **as_path**.


**Examples**


- This command replaces the AS-Path with the **none** option.

```
`switch# **show ip bgp neighbors 80.80.1.2 advertised-routes**
BGP routing table information for VRF default
Router identifier 202.202.1.1, local AS number 200
Route status codes: s - suppressed, * - valid, > - active, # - not installed, E
- ECMP head, e - ECMP
S - Stale, c - Contributing to ECMP, b - backup, L - labeled-unicast, q - Queued
for advertisement
Origin codes: i - IGP, e - EGP, ? - incomplete
AS Path Attributes: Or-ID - Originator ID, C-LST - Cluster List, LL Nexthop -
Link Local Nexthop

Network Next Hop Metric LocPref Weight Path
* > 101.101.1.0/24 80.80.1.1 - - - 200 i
* > 102.102.1.0/24 80.80.1.1 - - - 200 i
* > 103.103.1.0/24 80.80.1.1 - - - 200 302 i
* > 202.202.1.0/24 80.80.1.1 - - - 200 i

switch# **configure terminal**
switch(config)# **route-map foo permit 10**
switch(config-route-map-foo)# **set as-path match all replacement none**
switch(config-route-map-foo)# **exit**
switch(config)# **router bgp 200**
switch(config-router-bgp)# **neighbor 80.80.1.2 route-map foo out**
switch(config-router-bgp)# **end**

switch# **show ip bgp neighbors 80.80.1.2 advertised-routes**
BGP routing table information for VRF default
Router identifier 202.202.1.1, local AS number 200
Route status codes: s - suppressed, * - valid, > - active, # - not installed, E
- ECMP head, e - ECMP
S - Stale, c - Contributing to ECMP, b - backup, L - labeled-unicast, q - Queued
for advertisement
Origin codes: i - IGP, e - EGP, ? - incomplete
AS Path Attributes: Or-ID - Originator ID, C-LST - Cluster List, LL Nexthop -
Link Local Nexthop

Network Next Hop Metric LocPref Weight Path
* > 101.101.1.0/24 80.80.1.1 - - - 200 i
* > 102.102.1.0/24 80.80.1.1 - - - 200 i
* > 103.103.1.0/24 80.80.1.1 - - - 200 i
* > 202.202.1.0/24 80.80.1.1 - - - 200 i`
```

- Replace the AS-Path of matching prefixes with an empty or a null AS-Path. Remove AS **302** from prefix **103.103.1.0/24** as shown in the above output.


- This command replaces the AS-Path with the **auto** option.

```
`switch(config)# **route-map foo permit 10**
switch(config-route-map-foo)# **set as-path match all replacement auto**
switch(config-route-map-foo)# **end**

switch# **show ip bgp neighbors 80.80.1.2 advertised-routes**
BGP routing table information for VRF default
Router identifier 202.202.1.1, local AS number 200
Route status codes: s - suppressed, * - valid, > - active, # - not installed, E
- ECMP head, e - ECMP
S - Stale, c - Contributing to ECMP, b - backup, L - labeled-unicast, q - Queued
for advertisement
Origin codes: i - IGP, e - EGP, ? - incomplete
AS Path Attributes: Or-ID - Originator ID, C-LST - Cluster List, LL Nexthop -
Link Local Nexthop

Network Next Hop Metric LocPref Weight Path
* > 101.101.1.0/24 80.80.1.1 - - - 200 200 i
* > 102.102.1.0/24 80.80.1.1 - - - 200 200 i
* > 103.103.1.0/24 80.80.1.1 - - - 200 200 i
* > 202.202.1.0/24 80.80.1.1 - - - 200 200 i`
```


Replaces the AS-Path of matching prefixes with the locally configured AS **200**.

- This command replaces the AS-Path with another AS-Path.

```
`switch(config)# **route-map foo permit 10**
switch(config-route-map-foo)# **set as-path match all replacement 500 600**
switch(config-route-map-foo)# **end**

switch# **show ip bgp neighbors 80.80.1.2 advertised-routes**
BGP routing table information for VRF default
Router identifier 202.202.1.1, local AS number 200
Route status codes: s - suppressed, * - valid, > - active, # - not installed, E
- ECMP head, e - ECMP
S - Stale, c - Contributing to ECMP, b - backup, L - labeled-unicast, q - Queued
for advertisement
Origin codes: i - IGP, e - EGP, ? - incomplete
AS Path Attributes: Or-ID - Originator ID, C-LST - Cluster List, LL Nexthop -
Link Local Nexthop

Network Next Hop Metric LocPref Weight Path
* > 101.101.1.0/24 80.80.1.1 - - - 200 500 600 i
* > 102.102.1.0/24 80.80.1.1 - - - 200 500 600 i
* > 103.103.1.0/24 80.80.1.1 - - - 200 500 600 i
* > 202.202.1.0/24 80.80.1.1 - - - 200 500 600 i`
```


Replaces the AS-Path of matching prefixes with **500 600** as configured.

- Replaces the AS-Path with a combination of **auto** and an AS-Path.

```
`switch(config)# **route-map foo permit 10**
switch(config-route-map-foo)# **set as-path match all replacement auto 500 600**
switch(config-route-map-foo)# **end**

switch# **show ip bgp neighbors 80.80.1.2 advertised-routes**
BGP routing table information for VRF default
Router identifier 202.202.1.1, local AS number 200
Route status codes: s - suppressed, * - valid, > - active, # - not installed, E
- ECMP head, e - ECMP
 S - Stale, c - Contributing to ECMP, b - backup, L - labeled-unicast, q - Queued
for advertisement
Origin codes: i - IGP, e - EGP, ? - incomplete
AS Path Attributes: Or-ID - Originator ID, C-LST - Cluster List, LL Nexthop -
Link Local Nexthop

 Network Next Hop Metric LocPref Weight Path
 * > 101.101.1.0/24 80.80.1.1 - - - 200 200 500 600 i
 * > 102.102.1.0/24 80.80.1.1 - - - 200 200 500 600 i
 * > 103.103.1.0/24 80.80.1.1 - - - 200 200 500 600 i
 * > 202.202.1.0/24 80.80.1.1 - - - 200 200 500 600 i`
```


Replaces the AS-Path of matching prefixes with the locally configured AS **200** and **500 600**.


### set as-path prepend


The **set as-path prepend** command adds a **set** statement to a route map to prepend one or more Autonomous System (AS) numbers to the **as_path** attribute of a BGP route.


The **no set as-path prepend** and **default set as-path prepend** commands remove the specified set statements from the route map and update all corresponding routes.


**Command Mode**


Route-Map Configuration


**Command Syntax**


set as-path prepend auto | as_number [auto | as_number | last-as count]


no set as-path prepend auto | as_number [auto  | as_number | last-as count]


default set as-path prepend auto | as_number [auto  | as_number | last-as count]


**Parameters**


- **auto** - Prepends the peer AS number for peer inbound route maps and the local AS number for peer outbound route maps.

- **as_number** - Prepends the specified AS number. Enter in plain notation (values range from **1-4294967295**) or in asdot notation as described in RFC 5396. In asdot notation, enter AS numbers from **1-65535** in plain notation, and enter AS numbers from **65536 to 4294967295** as two values separated by a dot. The first value is high-order and represents a multiple of **65536**, and the second value is low-order and represents a decimal integer. For example, AS number **65552** can be entered as either **65552** or 1.16 (i.e., 1*65536+16). However entered, EOS stores the AS numbers internally in plain decimal notation and appear that way in **show** outputs.

- **last-as** **count** - Prepends the last AS number in the AS path *count* times. Values range from **1 to 15**. Mutually exclusive with the use of the **auto** cmdname or the entry of one or more specified AS numbers, and not supported in multi-agent mode.


**Examples**


- These commands create a route-map entry that prepends AS number **64496** and prepends either the peer or local AS number twice.

```
`switch(config)# **route-map map1**
switch(config-route-map-map1)# **set as-path prepend 64496 auto auto**
switch(config-route-map-map1)# **exit**

switch(config)# **show route-map map1**
route-map map1 permit 10
  Description:
  Match clauses:
  SubRouteMap:
  Set clauses:
    set as-path prepend 64496 auto auto
switch(config)#`
```

- The commands create a route-map entry that prepends AS numbers **64496**, **64498**, and **65552**.

```
`switch(config)# **route-map map2**
switch(config-route-map-map2)# **set as-path prepend 64496 64498 1.16**
switch(config-route-map-map2)# **exit**

switch(config)# **show route-map map2**
route-map map2 permit 10
  Description:
  Match clauses:
  SubRouteMap:
  Set clauses:
    set as-path prepend 64496 64498 65552
switch(config)#`
```

- These commands create a route map entry that prepends the last AS number **12** times.

```
`switch(config)# **route-map map3**
switch(config-route-map-map3)# **set as-path prepend last-as 12**
switch(config-route-map-map3)# **exit**

switch(config)# **show route-map map3**
route-map map3 permit 10
  Description:
  Match clauses:
  SubRouteMap:
  Set clauses:
    set as-path prepend last-as 12
switch(config)#`
```


### set community (route-map)


The **set community** command specifies community attribute modifications to routes selected for redistribution. The **set community none** command removes community attributes from the route.


The **no set community** and **default set community** commands remove the specified community from the Route-Map Configuration Modestatement by deleting the corresponding statement from the ***running config***.


**Command Mode**


Route-Map Configuration


**Command Syntax**


set community [gshut | aa:nn | community-list | internet | local-as | no-advertise | no-export | none | number]


no set community [gshut | aa:nn | additive | community-list | delete | internet | local-as | no-advertise | no-export | none | number]


default set community [gshut | aa:nn | additive | community-list | delete | internet | local-as | no-advertise | no-export | none | number]


**Parameters**


- **gshut** - Configures a graceful shutdown in BGP.

- **aa:nn** - Configures the community AS and network number, separated by colon. Value ranges from **0:0 to 65535:65535**.

- **community-list** - A label for community list.

- **internet** - Advertises route to the Internet community.

- **local-as** - Advertises route only to local peers.

- **no-advertise** - Does not advertise route to any peer.

- **no-export** - Advertises route only within BGP AS boundary.

- **none** - Does not provide any community attributes.

- **number** - Configures the community number. Value ranges from **1** to **4294967040**.

- **additive** - Adds specified attributes to the current community.

- **delete** - Removes specified attributes from the current community.


**Related Commands**


- [ip community-list](/um-eos/eos-border-gateway-protocol-bgp#xx1116784)

- route-map

- set (route-map)

- set community (route-map)


**Guideline**


EOS does not support disabling the process of graceful shutdown community.


**Example**


This command advertises routes only to local peers.

```
`switch(config-route-map-map1)# **show active**
route-map map1 permit 10
   match community instances <= 50
   set community 0:456 0:2345
switch(config-route-map-map1)# **set community local-as**
switch(config-route-map-map1)# **ip community-list 345 permit 23**
switch(config)# **route-map map1**
switch(config-route-map-map1)# **show active**
route-map map1 permit 10
   match community instances <= 50
   set community 0:456 0:2345 local-as
switch(config-route-map-map1)#`
```


### set extcommunity (route-map)


The **set extcommunity** command specifies extended community attribute modifications to routes selected for redistribution. The **set extcommunity none** command removes extended community attributes from the route.


The **no set extcommunity** and **default set extcommunity** commands remove the specified **set extcommunity** command from the Route-Map Configuration Mode statement by deleting the corresponding statement from ***running-config***.


**Command Mode**


Route-Map Configuration Mode


**Command Syntax**


set extcommunity cond_x [cond_2][cond_n][mod_type]


set extcommunity none


no set extcommunitycond_x [cond_2][cond_n][mod_type]


default set extcommunity cond_x [cond_2][cond_n][mod_type]


default set extcommunity none


**Parameters**


- **cond_x** - Specifies extended community route map modification. Command may contain multiple attributes. Options include the following:


- **rt** **asn:nn** - Specifies the route target attribute (AS:network number).

- **rt** **ip-address:nn** - Specifies the route target attribute (IP address: network number).

- **soo** **ASN:nn** - Specifies the site of origin attribute (AS:network number).

- **soo** **IP-address:nn** - Specifies the site of origin attribute (IP address: network number).

- **mod_type**- Specifies the route map modification method. Options include the following:


- **no parameter** - Specifies the command to replace an existing route map with specified parameters.

- **additive** - Specifies the command to add specified parameters to existing route map.

- **delete** - Specifies the command to remove specified parameters from existing route map.


**Related Commands**


- route-map enters route map configuration mode.

- set (route-map) specifies attribute modifications for the redistributed routes.


**Example**


This command creates a route map entry in **map1** that sets the route target extended community attribute.

```
`switch(config)# **route-map map1**
switch(config-route-map-map1)# **set extcommunity rt 10.13.2.4:100**
switch(config-route-map-map1)#`
```


### show (ACL configuration modes)


The **show** command displays the contents of an Access Control List (ACL).


- **show** or **show pending** displays the list as modified in ACL configuration mode.

- **show active** displays the list as stored in running-config.

- **show comment** displays the comment stored with the list.

- **show diff** displays the modified and stored lists, with flags denoting the modified rules.


Exiting the ACL configuration mode stores all pending ACL changes to ***running-config***.


**Command Mode**


ACL Configuration


IPv6-ACL Configuration


Std-ACL Configuration


Std-IPv6-ACL Configuration


MAC-ACL Configuration


**Command Syntax**


show


show active


show comment


show diff


show pending


**Examples**


The examples in this section assume these ACL commands are entered as specified.


- These commands are stored in **none**:


```
`10 permit ip 10.10.10.0/24 any
20 permit ip any host 10.21.10.1
30 deny ip host 10.10.10.1 host 10.20.10.1
40 permit ip any any
50 remark end of list`
```

- The current edit session removed this command. This change is not yet stored to **none**:


```
`20 permit ip any host 10.21.10.1`
```

- The current edit session added these commands ACL. They are not yet stored to **none**:


```
`20 permit ip 10.10.0.0/16 any
25 permit tcp 10.10.20.0/24 any
45 deny pim 239.24.124.0/24 10.5.8.4/30`
```

- This command displays the ACL, as stored in the configuration.

```
`switch(config-acl-test_1)# **show active**
IP Access List test_1
  10 permit ip 10.10.10.0/24 any
  20 permit ip any host 10.21.10.1
  30 deny ip host 10.10.10.1 host 10.20.10.1
  40 permit ip any any
  50 remark end of list`
```

- This command displays the pending ACL, as modified in ACL configuration mode.

```
`switch(config-acl-test_1)# **show pending**
IP Access List test_1
  10 permit ip 10.10.10.0/24 any
  20 permit ip 10.10.0.0/16 any
  25 permit tcp 10.10.20.0/24 any
  30 deny ip host 10.10.10.1 host 10.20.10.1
  40 permit ip any any
  45 deny pim 239.24.124.0/24 10.5.8.4/30
  50 remark end of list`
```

- This command displays the difference between the saved and modified ACLs.


- Rules added to the pending list are denoted with a plus sign (+).

- Rules removed from the saved list are denoted with a minus sign (-)

```
`switch(config-acl-test_1)# **show diff**
---
+++
@@ -1,7 +1,9 @@
 IP Access List test_1
  10 permit ip 10.10.10.0/24 any
  20 permit ip any host 10.21.10.1
  20 permit ip 10.10.0.0/16 any
  25 permit tcp 10.10.20.0/24 any
  30 deny ip host 10.10.10.1 host 10.20.10.1
  40 permit ip any any
  45 deny pim 239.24.124.0/24 10.5.8.4/30`
```


### show hardware tcam profile


The **show hardware tcam profile** command displays the hardware specific information for the current operational TCAM profile in the running configuration.


This command is applicable to DCS-7280(E/R) and DCS-7500(E/R) series switches only.


**Command Mode**


EXEC


**Command Syntax**


show hardware tcam profile [[profileName [[feature featureName] detail]]|[detail]


**Parameters**


- **profileName** Selects the named profile.

- **feature**featureNameSelects the specific feature by name.

- **detail** Displays the content of the TCAM profile.


**Guidelines**


If the profile cannot be programmed, the Status column will print ‘ERROR‘. Any features that use TCAM functionality will not work properly. Do not expect any features to work if the profile is in the ‘ERROR’ state. If there are warnings or errors, a summary message will display warnings or errors found in programming the profile in addition to the system log messages.


**Examples**


- The **show hardware tcam profile** lists the TCAM profile status on each line card. In case of successful programming it is as shown below.

```
`switch(config)# **show hardware tcam profil**e
                     Configuration            Status
FixedSystem          testprofile              testprofile`
```

- If the profile cannot be programmed, the Status column will print ‘ERROR‘.

```
`(config)# **show hardware tcam profile**
             Configuration    Status
Linecard3    newprofile1    **ERROR**
Linecard4    newprofile1    **ERROR** Linecard5 newprofile1 ERROR
Linecard6    newprofile1    **ERROR**
Linecard7    newprofile1    **WARNING**

Detailed Programming Status
Linecard3, Linecard4, Linecard5
[Error] feature flow is not supported on this hardware platform
Linecard7
[Warning] the key size of feature flow exceeds the configured key size limit`
```

- **The show hardware tcam profile <profile> detail** command displays further info about the TCAM profile features.
Note: The profile contains all the features that are untouched after copying from the base profile.


```
`switch(config-hw-tcam)# **show hardware tcam profile myprofile detail**
Profile myprofile [ FixedSystem ]
 Feature:             acl port ip egress
 Key size:            320
 Key Fields:          dscp, dst-ip, ip-frag, ip-protocol, l4-dst-port,
                      l4-src-port, src-ip

 Feature:             acl port ip ingress
 Key size:            320
 Key Fields:          dscp, dst-ip, ip-frag, ip-protocol, l4-dst-port, l4-ops,
                      l4-src-port, src-ip, tcp-control, ttl

 Feature:             acl port ipv6 egress
 Key size:            320
 Key Fields:          dst-ipv6, ip-protocol, ipv6-next-header,
                      ipv6-traffic-class, l4-dst-port, l4-src-port, src-ipv6,
                      tcp-control, ttl

 Feature:             acl port ipv6 ingress
 Key size:            320
 Key Fields:          dst-ipv6, ip-protocol, ipv6-next-header,
                      ipv6-traffic-class, l4-dst-port, l4-ops, l4-src-port,
                      src-ipv6, tcp-control, ttl

 Feature:             acl port ipv6 source-only egress
 Key size:            320
 Key Fields:          ip-protocol, src-ipv6

 Feature:             acl port mac egress
 Key size:            320
 Key Fields:          dst-mac, ether-type, src-mac
...`
```

- You can use the **show hardware tcam profile** command without the **detail** keyword to see all of the features configured in a profile without seeing how the features are defined.

```
`(config-hw-tcam-profile-newfeature)# **show hardware tcam profile default**

Features enabled in TCAM profile default: [ Linecard3, Linecard4, Linecard6, Linecard
7, Linecard8, Linecard9, Linecard10 ]

mpls
acl vlan ipv6
acl subintf ipv6
acl vlan ipv6 egress
acl port ipv6
pbr ipv6
acl vlan ip
acl subintf ip
acl port ip
tunnel vxlan
acl port mac
pbr ip
pbr mpls
qos ipv6
qos ip
mirror ip
counter lfib
mpls pop ingress`
```


### show access-lists


The **show access-lists** command displays the contents of all IPv4, IPv6, and MAC Access Control Lists (ACLs) on the switch in addition to the configuration and status. Use the **summary** option to display only the configuration and status, which contains details such as the name of the ACL, total rules configured, configured and active status containing interface information, and supplicant information as in the case of dynamic ACLs from dot1x sessions.


**Command Mode**


Privileged EXEC


**Command Syntax**


show access-lists[interface interface_acl] | [acl_name acl_name] acl_name | [scope summary]


**Parameters**


- **interface** - Filter by interfaces such as Ethernet, VLANs, and Port Channels. Selection options include the following:


- **no parameter** - Display all ACLs.

- **interface_acl** - Display ACLs attached to the interface if present.

- **acl_name** - Display the list name. Selection options include the following:


- **no parameter** - Display all ACLs.

- **acl_name** - Display a specific ACL.

- **scope** - Display detailed or summarized information. Selection options include the following:


- **no parameter** - Display all rules in the specified lists including the configuration and status.

- **summary** - Display only the configuration and status of the ACL.


**Examples**


- This command displays all rules in all the ACLs including IPv4, IPv6, and MAC and the configuration and status.

```
`switch# **show access-lists**
Phone ACL bypass: disabled
IP Access List default-control-plane-acl [readonly]
        counters per-entry
        10 permit icmp any any
        20 permit ip any any tracked [match 149061 bytes in 1721 packets, 0:00:00 ago]
        30 permit udp any any eq bfd ttl eq 255
        40 permit udp any any eq bfd-echo ttl eq 254
        50 permit udp any any eq multihop-bfd micro-bfd sbfd
        60 permit udp any eq sbfd any eq sbfd-initiator
        70 permit ospf any any
        80 permit tcp any any eq ssh telnet www snmp bgp https msdp ldp netconf-ssh gnmi [match 180 bytes in 3 packets, 0:03:08 ago]
        90 permit udp any any eq bootps bootpc snmp rip ntp ldp ptp-event ptp-general [match 984 bytes in 3 packets, 1 day, 9:02:21 ago]
        100 permit tcp any any eq mlag ttl eq 255
        110 permit udp any any eq mlag ttl eq 255
        120 permit vrrp any any
        130 permit ahp any any
        140 permit pim any any
        150 permit igmp any any
        160 permit tcp any any range 5900 5910
        170 permit tcp any any range 50000 50100
        180 permit udp any any range 51000 51100
        190 permit tcp any any eq 3333
        200 permit tcp any any eq nat ttl eq 255
        210 permit tcp any eq bgp any
        220 permit rsvp any any
        230 permit tcp any any eq 9340
        240 permit tcp any any eq 9559
        250 permit udp any any eq 8503
        260 permit udp any any eq lsp-ping
        270 permit udp any eq lsp-ping any

        Total rules configured: 27
        Configured on Ingress: control-plane(default VRF)
        Active on     Ingress: control-plane(default VRF)

IP Access List v4Acl
        10 permit ip any any

        Total rules configured: 1
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1

Standard IP Access List stAcl
        10 permit any

        Total rules configured: 1

IP Access List noRulesAcl

        Total rules configured: 0
        Configured on Ingress: Et2/1
        Active on     Ingress: Et2/1

IPV6 Access List default-control-plane-acl [readonly]
        counters per-entry
        10 permit icmpv6 any any [match 335448 bytes in 4424 packets, 0:01:13 ago]
        20 permit ipv6 any any tracked
        30 permit udp any any eq bfd hop-limit eq 255
        40 permit udp any any eq bfd-echo hop-limit eq 254
        50 permit udp any any eq multihop-bfd micro-bfd sbfd
        60 permit udp any eq sbfd any eq sbfd-initiator
        70 permit ospf any any
        80 permit 51 any any
        90 permit 50 any any
        100 permit tcp any any eq ssh telnet www snmp bgp https netconf-ssh gnmi
        110 permit udp any any eq bootps bootpc snmp ntp ptp-event ptp-general
        120 permit tcp any any eq mlag hop-limit eq 255
        130 permit udp any any eq mlag hop-limit eq 255
        140 permit tcp any any range 5900 5910
        150 permit tcp any any range 50000 50100
        160 permit udp any any range 51000 51100
        170 permit udp any any eq dhcpv6-client dhcpv6-server
        180 permit tcp any eq bgp any
        190 permit tcp any any eq nat hop-limit eq 255
        200 permit udp any any eq nat hop-limit eq 255
        210 permit rsvp any any
        220 permit pim any any
        230 permit tcp any any eq 9340
        240 permit tcp any any eq 9559
        250 permit udp any any eq 8503
        260 permit udp any any eq lsp-ping
        270 permit udp any eq lsp-ping any

        Total rules configured: 27
        Configured on Ingress: control-plane(default VRF)
        Active on     Ingress: control-plane(default VRF)

IPV6 Access List v6Acl
        10 permit ipv6 3891:3c58:6300::/64 any
        20 permit ipv6 any host 2fe1:b468:24a::
        30 deny ipv6 host 3411:91c1:: host 4210:cc23:d2de::

        Total rules configured: 3
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1

MAC Access List mlist
        10 deny any any

        Total rules configured: 1
        Configured on Ingress: Et11/1
        Configured on Egress: Et11/1
        Active on     Ingress: Et11/1
        Active on     Egress: Et11/1`
```

- This command displays only the configuration and status of each ACL on the switch.

```
`switch# **show access-lists summary**
Phone ACL bypass: disabled
IPV4 ACL default-control-plane-acl [readonly]
        Total rules configured: 27
        Configured on Ingress: control-plane(default VRF)
        Active on     Ingress: control-plane(default VRF)

IPV4 ACL v4Acl
        Total rules configured: 1
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1

Standard IPV4 ACL stAcl
        Total rules configured: 1

IPV4 ACL noRulesAcl
        Total rules configured: 0
        Configured on Ingress: Et2/1
        Active on     Ingress: Et2/1

IPV6 ACL default-control-plane-acl [readonly]
        Total rules configured: 27
        Configured on Ingress: control-plane(default VRF)
        Active on     Ingress: control-plane(default VRF)

IPV6 ACL v6Acl
        Total rules configured: 3
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1

MAC ACL mlist
        Total rules configured: 1
        Configured on Ingress: Et11/1
        Configured on Egress: Et11/1
        Active on     Ingress: Et11/1
        Active on     Egress: Et11/1`
```

- This command displays all rules in list2 ACL and the configuration and status.


```
`switch# **show access-list list2**
IP Access List list2
        10 permit ip 10.10.10.0/24 any
        20 permit ip any host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1

        Total rules configured: 3
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1

IPV6 Access List list2
        10 permit ipv6 3891:3c58:6300::/64 any
        20 permit ipv6 any host 2fe1:b468:24a::
        30 deny ipv6 host 3411:91c1:: host 4210:cc23:d2de::

        Total rules configured: 3
        Configured on Ingress: Et2/1
        Active on     Ingress: Et2/1
switch#`
```


The above output displayed two ACLs as the switch had an IPv4 ACL and an IPv6 ACL with the same name.

- This command displays all rules in list2 ACL on Ethernet 1/1 with the configuration and status.

```
`switch# **show access-list list2 interface Ethernet 1/1**
IP Access List list2
        10 permit ip 10.10.10.0/24 any
        20 permit ip any host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1

        Total rules configured: 3
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1
switch#`
```


### show ip access-lists


The **show ip access-lists** command displays the contents of IPv4 and standard IPv4 Access Control List (ACLs) on the switch with the configuration and status. Use the **summary** option to display only the configuration and status with details such the name of the ACL, total rules configured, configured and active status containing interface information, and supplicant information as in the case of dynamic ACLs from dot1x sessions.


**Command Mode**


Privileged EXEC


**Command Syntax**


show ip access-lists [interface interface_ipv4]|[acl_name acl_name] | [scope summary]


**Parameters**


- **interface** Filter on interfaces such as Ethernet, VLANs, and Port Channels. Selection options include the following:


- **no parameter** - Displays all IPv4 ACLs.

- **interface_ipv4** - Display the ACLs on a specified interface.


- acl_name - Specify the name of a list to display. Selection options include the following:


- **no parameter** - Displays all IPv4 ACLs.

- **acl_name** - Specify an IPv4 ACL to display.


- **scope** - Displays detailed or summarized information. Selection options include the following:


- **no parameter** - Display all rules in the specified lists with the configuration and status.

- **summary** - Display only the configuration and status.


**Examples**


- This command displays all rules in list2 IPv4 ACL, configuration, and status.

```
`switch# **show ip access-lists list2**
IP Access List list2
        10 permit ip 10.10.10.0/24 any
        20 permit ip any host 10.20.10.1
        30 deny ip host 10.10.10.1 host 10.20.10.1
Total rules configured: 3
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1
switch#`
```


The above output can also be displayed with the help of the **show ip access-lists interface Ethernet 1/1** command since the ACL list2 applies to the Ethernet 1/1 interface.

- This command displays the name and number of rules in each list on the switch.

```
`switch# **show ip access-lists summary**
IPV4 ACL default-control-plane-acl
        Total rules configured: 12
        Configured on: control-plane
        Active on    : control-plane

IPV4 ACL list2
        Total rules configured: 3
IPV4 ACL test1
        Total rules configured: 6
Standard IPV4 ACL test_1
        Total rules configured: 1
IPV4 ACL test_3
        Total rules configured: 0
switch#`
```

- This command displays the summary and lists all the configured IPv4 ACLs.

```
`switch # **show ip access-lists summary**
IPV4 ACL default-control-plane-acl [readonly]
 Total rules configured: 17
 Configured on Ingress: control-plane(default VRF)
 Active on Ingress: control-plane(default VRF)

IPV4 ACL ipAclLimitTest
 Total rules configured: 0
 Configured on Egress: Vl2148,2700
 Active on Egress: Vl2148,2700`
```


### show ip prefix-list


The **show ip prefix-list** command displays all rules for the specified IPv4 prefix list. The command displays all IPv4 prefix list rules if a prefix list name is not specified.


**Command Mode**


EXEC


**Command Syntax**


**show ip prefix-list [display_items list_name]**


**Parameters**


**display_items** - Specifies the name of prefix lists to display rules. Options include:


- **no parameter** - Display all IPv4 prefix list rules.

- **list_name** Specifies the IPv4 prefix list to display rules.


**Example**


This command displays all rules in the route-one IPv4 prefix list.

```
`switch(config-ip-pfx)# **show ip prefix-list**
ip prefix-list route-one
    seq 10 deny 10.1.1.0/24
    seq 20 deny 10.1.0.0/16
    seq 30 permit 12.15.4.9/32
    seq 40 deny 1.1.1.0/24
switch(config-ip-pfx)#`
```


### show ipv6 access-lists


The **show ipv6 access-lists** command displays the contents of all IPv6 Access Control Lists (ACLs) on the switch with the configuration and status. Use the **summary** option to display only the configuration and status with contains details such as the name of the ACL, total rules configured, configured and active on status with interface information, and supplicant information in case of dynamic ACLs from dot1x sessions.


**Command Mode**


Privileged EXEC


**Command Syntax**


show ipv6 access-lists [ interface interface_ipv6] [supplicant supplicant][acl_name acl_name][scope summary]


**Parameters**


- **interface** Filter on interfaces such as Ethernet, VLANs, and Port Channels. Selection options include the following:


- **no parameter** - Displays all IPv6 ACLs.

- **interface_ipv6** - Display the ACLs on a specified interface.


- acl_name - Specify the name of a list to display. Selection options include the following:


- **no parameter** - Displays all IPv6 ACLs.

- **acl_name** - Specify an IPv6 ACL to display.


- scope - Displays detailed or summarized information. Selection options include the following:


- **no parameter** - Display all rules in the specified lists with the configuration and status.

- **summary** Display only the configuration and status.


**Examples**


- This command displays all rules in test1 IPv6 ACL.

```
`switch# **show ipv6 access-lists list2**
IP Access List list2
        10 permit ipv6 3891:3c58:6300::/64 any
        20 permit ipv6 any host 2fe1:b468:024a::
        30 deny ipv6 host 3411:91c1:: host 4210:cc23:d2de:::
Total rules configured: 3
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1
switch#`
```


The above output can also be displayed using the **show ipv6 access-lists interface Ethernet 1/1** command since the ACL list2 applies to the Ethernet 1/1 interface.

- This command displays the name and number of rules in each list on the switch.

```
`switch# **show ipv6 access-lists summary**
IPV6 ACL list2
        Total rules configured: 3
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1

IPV6 ACL test1
        Total rules configured: 6

IPV6 ACL test_1
        Total rules configured: 1

Standard IPV6 ACL test_3
        Total rules configured: 0
switch#`
```


### show ipv6 prefix-list


The **show ipv6 prefix-list** command displays all rules for the specified IPv6 prefix list. The command displays all IPv6 prefix lists if a prefix list name is not specified.


**Command Mode**


EXEC


**Command Syntax**


show ipv6 prefix-list [display_items list_name]


**Parameters**


**display_items** Specifies the name of prefix lists for which rules are displayed. Options include:


- **no parameter** All IPv6 prefix lists are displayed.

- **list_name** Specifies the IPv6 prefix list for which rules are displayed.


**Examples**


- This command displays all rules in the map1 IPv6 prefix list:

```
`switch> **show ipv6 prefix-list map1**
ipv6 prefix-list map1
seq 10 permit 3:4e96:8ca1:33cf::/64
seq 15 deny 3:4400::/64
seq 20 permit 3:11b1:8fe4:1aac::/64
seq 30 permit 3:1bca:3ff2:634a::/64
seq 40 permit 3:1bca:1141:ab34::/64`
```

- This command displays all prefix lists:

```
`switch> **show ipv6 prefix-list**
ipv6 prefix-list map1
seq 10 permit 3:4e96:8ca1:33cf::/64
seq 15 deny 3:4400::/64
seq 20 permit 3:11b1:8fe4:1aac::/64
seq 30 permit 3:1bca:3ff2:634a::/64
seq 40 permit 3:1bca:1141:ab34::/64
ipv6 prefix-list FREDD
ipv6 prefix-list route-five
ipv6 prefix-list map2
seq 10 deny 10:1:1:1::/64 ge 72 le 80
seq 20 deny 10:1::/32`
```


### show mac access-lists


The show mac access-lists command displays the contents of all MAC Access Control Lists (ACLs) on the switch, along with their configuration and status. Use the summary option to display only the configuration and status, which contain details such as the name of the ACL, the total rules configured, and where the ACL is configured/active with a status containing specific interface information.


**Command Mode**


Privileged EXEC


**Command Syntax**


show mac access-lists [interface interface_acl] [acl_name acl_name] [scope summary]


**Parameters**


- **interface** - Filter by interfaces such as Ethernet, VLANs, and Port Channels. Selection options include the following:


- **no parameter** - Display all MAC ACLs.

- **interface_acl** - Display MAC ACLs attached to the interface if present.

- **acl_name** Display the list name. Selection options include the following:


- **no parameter** - Display all MAC ACLs.

- **acl_name** - Display a specific MAC ACL.

- **scope** - Display detailed or summarized information. Selection options include the following:


- **no parameter** - Display all rules in the specified lists including the configuration and status.

- **summary** - Display only the configuration and status of the MAC ACL.


**Examples**


- This command displays all rules in **mtest2** MAC ACL.

```
`switch# **show mac access-list mlist2**
MAC Access List mlist2
        10 permit 1024.4510.F125 0.0.0 any aarp
        20 permit any 4100.4500.0000 0.FF.FFFF novell
        30 deny any any

        Total rules configured: 3
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1`
```


The above output can also be displayed with the help of **show mac access-lists interface Ethernet 1/1** command since the ACL mlist2 applies to the Ethernet 1/1 interface.

- This command displays the number of rules in each MAC ACL on the switch.

```
`switch# **show mac access-list summary**
MAC ACL mlist1
        Total rules configured: 6

MAC ACL mlist2
        Total rules configured: 3
        Configured on Ingress: Et1/1
        Active on     Ingress: Et1/1

MAC ACL mlist3
        Total rules configured: 1

MAC ACL mlist4
        Total rules configured: 0`
```


### show platform arad acl tcam summary


The **show platform arad tcam summary** command displays the percentage of TCAM utilization per forwarding ASIC.


**Command Mode**


EXEC


**Command Syntax**


show platform arad acl tcam summary


**Parameter**


**summary** - Displays the ACL TCAM summary.


**Example**


This command displays the percentage of TCAM utilization per forwarding ASIC.

```
`switch# **show platform arad acl tcam summary**
The total number of TCAM lines per bank is 1024.

========================================================
Arad3/0:
========================================================
 Bank      Used           Used %                 Used By
    1         4                0                IP RACLs
Total Number of TCAM lines used is: 4

========================================================
Arad3/4:
========================================================
 Bank      Used           Used %                 Used By
    1         2                0                IP RACLs
Total Number of TCAM lines used is: 2`
```


### show platform arad acl tcam


The **show platform arad acl tcam** command displays the number of TCAM entries (hardware resources) occupied by the ACL on each forwarding ASIC.


This command applies only to DCS-7500E, DCS-7280E series switches.


**Command Mode**


EXEC


**Command Syntax**


show platform arad acl tcam [scope [detail | diff | hw | shadow | summary]


**Parameters**


**scope** Specifies the information displayed. Options include:


- **detail** - Displays the ACL TCAM details.

- **diff** - Displays the difference between hardware and shadow.

- **hw** - Displays the ACL entries from hardware.

- **shadow** - Displays the ACL entries from shadow.

- **summary** - Displays the ACL TCAM summary.


**Examples**


- This command displays the number of TCAM entries used by Arad0 ASIC. In this example, apply the ACL on two VLANs (**Vl2148** and **Vl2700**) but number of TCAM entries occupied is only one.

```
`switch# **show platform arad acl tcam detail**
ip access-list ipAclLimitTest (Shared RACL, 0 rules, 1 entries, direction out,
state success, Acl Label 2)
Fap: Arad0, Shared: true, Interfaces: Vl2148, Vl2700
Bank Offset Entries
0         0       1
Fap: Arad1, Shared: true, Interfaces: Vl2148
Bank Offset Entries
0         0       1`
```

- This command displays the percentage of TCAM utilization per forwarding ASIC.

```
`switch# **show platform arad acl tcam summary**
The total number of TCAM lines per bank is 1024.
========================================================
Arad0:
========================================================
 Bank   Used                  Used %             Used By
    0      1                       0   IP Egress PACLs/RACLs
Total Number of TCAM lines used is: 1
========================================================
Arad1:
========================================================
 Bank   Used                   Used %            Used By
    0      1                        0   IP Egress PACLs/RACLs
Total Number of TCAM lines used is: 1`
```


### show platform arad mapping


The **show platform arad mapping** command displays the mapping between the interfaces and the forwarding ASICs.


**Command Mode**


EXEC


**Command Syntax**


**show platform arad chip_name mapping**


**Parameter**


**chip_name** Specifies the Arad chip name.


**Example**


This command displays the mapping between the interfaces and the forwarding ASICs on the Arad3/0 chip.

```
`switch# **show platform arad arad3/0 mapping**
Arad3/0  Port                      SysPhyPort    Voq   ( Fap,FapPort)    Xlge     Serdes
-------------------------------------------------------------------------------
         Ethernet3/1/1                     34    288        (0  ,  2)     n/a        (20)
...............................................................................`
```


### show platform fap acl


The **show platform fap acl** command displays the ACL information of Sand platform devices.


**Command Mode**


Privileged EXEC


**Command Syntax**


**show platform fap acl [ipkgv | l4ops | mirroring | opkgv | pmf | tcam | udf | vsicfg**]


**Parameters**


- **ipkgv** - Displays the ACL Ingress Interface Specification (IPKGV) information.

- **l4ops** - Displays the ACL Layer 4 Options (L4OPS) information.

- **mirroring** - Displays the mirroring ACL information.

- **opkgv** - Displays the ACL Egress Interface Specification (OPKGV) information.

- **pmf** - Displays the Pmf.

- **tcam** - Displays the ACL TCAM information.

- **udf** - Displays the ACL UDF information.

- **vsicfg** - Displays the ACL Virtual Switch Instance (VSI) CONFIG information.


**Guidelines**


Supported on DCS-7280SE and DCS-7500E series platforms only.


**Example**


This command displays the brief information of all installed mirroring ACLs.

```
`switch(config)# **show platform fap acl mirroring**

==============
 Aggregate ACLs
==============

 (list2:0->2) type=2; version=0
  - list2 [ prio 0 ] => session 2

 (list1:10->1,list3:20->3) type=0; version=13
  - list3 [ prio 20 ] => session 3
  - list1 [ prio 10 ] => session 1

======================
 Interface-ACL Mapping
======================

  Ethernet1 => (list1:10->1,list3:20->3) [ ipv4 ]
  Ethernet33 => (list2:0->2) [ mac ]`
```


### show platform fap acl tcam


The **show platform fap tcam** command displays the number of TCAM entries (hardware resources) occupied by the ACL on each forwarding ASIC of Sand platform devices.


**Command Mode**


Privileged EXEC


**Command Syntax**


**show platform fap acl tcam [detail | diff | hw | shadow | summary]**


**Parameter**


- **detail** - Displays the number of TCAM entries (hardware resources) occupied by the ACL on each forwarding ASIC.

- **diff** - Displays the difference between hardware and shadow.

- **hw** - Displays ACL entries from hardware.

- **shadow** - Displays ACL entries from shadow.

- **summary** - Displays the percentage of TCAM utilization per forwarding ASIC.


**Example**


This command displays the number of TCAM entries and other ACL TCAM detail.

```
`switch# **show platform fap acl tcam detail**
ip access-list ipAcl0000 (RACL, 1 rules, 2 entries, direction in, state success)
 Shared: false
 Interface: Vlan0002
 -------------------
 Fap: Arad3/0
 Bank Offset Entries
 1         0       2
 Interface: Vlan0003
 -------------------
 Fap: Arad3/0
 Bank Offset Entries
 1         2       2
 Fap: Arad3/4
 Bank Offset Entries
 1         0       2`
```


### show platform fap acl tcam hw


The **show platform fap acl tcam hw** command displays the TCAM entries configured for each TCAM bank including policy-maps and corresponding traffic match.


This command applies only to DCS-7280(E/R), DCS-7500(E/R) series switches.


**Command Mode**


EXEC


**Command Syntax**


show platform fap fap_name acl tcam hw


**Parameters**


- **fap_name** - Specifies the switch chip-set name.


**Example**


This command displays the TCAM entries configured for each TCAM bank including policy maps and corresponding traffic matches.

```
`switch# **show platform fap Arad1 acl tcam hw**
================================================================================
Arad1 Bank 0 Type: dbPdpIp, dbPdpIp6, dbPdpMpls, dbPdpNonIp, dbPdpTunnel
================================================================================
----------------------------------------------------
|Offs|X|PR|TT|R|QI|V6MC|DPRT|SPRT|F|DEST |V|ACT  |H|
----------------------------------------------------
|29  |4|59|  | |01|    |    |    | |     |3|0008f|0|
|    |4|59|  | |01|    |    |    | |     |0|00000|0|
|30  |4|33|  | |01|    |    |    | |     |3|0008f|0|
|    |4|33|  | |01|    |    |    | |     |0|00000|0|
|31  |4|32|  | |01|    |    |    | |     |3|0008f|0|
|    |4|32|  | |01|    |    |    | |     |0|00000|0|
|32  |4|  |  | |01|ff02|    |    | |     |3|00097|0|
|    |4|  |  | |01|ff02|    |    | |     |0|00000|0|
|33  |4|06|  | |01|    |    |00b3| |26ffd|3|0009b|0|
|    |4|06|  | |01|    |    |00b3| |26ffd|0|00000|0|
|34  |4|06|  | |01|    |00b3|    | |26ffd|3|0009b|0|
----------------------------------------------
|Offs|X|R|QI|DAHI|PT|DALO    |DEST |V|ACT  |H|
----------------------------------------------
-----------------------------------------------------------------------------
|Offs|X|TT0|QI|FOI|TT1|DEST |TT1P |PT|VX_DP|PN|F|MC|O|V|HDR OFFSETS |ACT  |H|
================================================================================
Arad1 Bank 1 Type: dbIpQos
================================================================================
----------------------------------------------------------------------
|Offs|X|TC|CL|DPRT|SPRT|VQ|L4OPS |PP|PR|F|V4_DIP  |V4_SIP  |V|ACT  |H|
----------------------------------------------------------------------
|0   |0|  |  |    |    |  |      |01|  | |        |        |3|00000|0|
|    |0|  |  |    |    |  |      |01|  | |        |        |0|00000|0|
----------------------------------------------------------------------
<-------OUTPUT OMITTED FROM EXAMPLE-------->`
```


### show platform fap acl tcam summary


The **show platform fap acl tcam summary** command displays for each forwarding ASIC, the number of TCAM entries consumed per ACL type, and in which TCAM bank the entries are installed. A mirroring ACL does not consume TCAM resources unless attached to a mirroring source interface, and a mirroring destination is configured. If the mirroring destination is a GRE tunnel, at least one nexthop entry for the tunnel destination must be resolved before a TCAM entry is installed.


**Command Mode**


EXEC


**Command Syntax**


show platform fap acl tcam summary


**Example**


This command displays the number of TCAM entries consumed per ACL type, the bank installed, and ASIC. Three TCAM entries are consumed across two forwarding ASICs, two for IP ACLs, and one for MAC ACLs.

```
`switch# **show platform fap acl tcam summary**
========================================================
 Arad0:
========================================================
    Bank   Used Used %    Used By
    0, 1      2      0    IP Mirroring
 Total Number of TCAM lines used is: 4
========================================================
 Arad1:
========================================================
   Bank   Used            Used %                 Used By
      2      1                 0           Mac Mirroring`
```


### show platform trident tcam


The **show platform trident tcam** command displays the TCAM entries configured for each TCAM group including policy maps and corresponding hits.


**Command Mode**


EXEC


**Command Syntax**


show platform trident tcam [acl | cpu-bound | detail | directed-broadcast | entry | mirror | pbr | pipe | qos | shared | summary]


**Parameters**


- **no parameters** - Displays TCAM entries for each TCAM group.

- **acl** - Displays the trident ACL information.

- **cpu-bound** - Displays the trident cpu-bound information.

- **detail** - Lists all TCAM entries.

- **directed-broadcast** - Allows inbound broadcast IP packets with Source IP address as one of the permitted broadcast host.

- **entry** - Displays the TCAM entry information.

- **mirror** - Displays the trident Mirroring ACL information.

- **pbr** - Displays the trident PBR ACL information.

- **pipe** - Allows to specify a pipe for filtering.

- **qos** - Displays the trident QOS information.

- **shared** - Displays the ACL Sharing information.

- **summary** - Displays the TCAM allocation information.


**Guidelines**


Applies only to DCS-7010, DCS-7050/DCS-7050X, DCS7250X, DCS-7300X series switches.


**Examples**


- This command displays the Trident mirroring ACL information.

```
`switch(config)# **show platform trident tcam mirror**
=== Mirroring ACLs on switch Linecard0/0 ===

Session: mir-sess2

INGRESS ACL mirAcl2* uses 2 entries
 Assigned to ports: Ethernet32/1`
```

- This command displays the allowed IP Destination address from the in coming packets.

```
`switch# **show platform trident tcam directed-broadcast**
DirectedBroadcast Feature Tuples.
Src Ip          Dst Ip          Action          Hits
--------------- --------------- ------- ------------
10.1.1.1        192.164.2.15    Permit             0
20.1.1.1        192.164.2.15    Permit             0
30.1.1.1        192.164.2.15    Permit             0
10.1.1.1        192.166.2.15    Permit             0
20.1.1.1        192.166.2.15    Permit             0
30.1.1.1        192.166.2.15    Permit             0
10.1.1.1        192.168.2.255   Permit             0
20.1.1.1        192.168.2.255   Permit             0
30.1.1.1        192.168.2.255   Permit             0
*               192.164.2.15    Deny               0
*               192.166.2.15    Deny               0
*               192.168.2.255   Deny               0`
```

- This command displays detailed information for the TCAM group.

```
`switch# **show platform trident tcam detail**
=== TCAM detail for switch Linecard0/0 ===
TCAM group 9 uses 42 entries and can use up to 1238 more.
 Mlag control traffic uses 4 entries.
    589826                0 hits - MLAG - SrcPort UDP Entry
    589827                0 hits - MLAG - DstPort UDP Entry
    589828                0 hits - MLAG - SrcPort TCP Entry
    589829                0 hits - MLAG - DstPort TCP Entry
 CVX traffic reserves 6 entries (0 used).
 L3 Control Priority uses 23 entries.
    589836                0 hits - URM - SelfIp UDP Entry
    589837                0 hits - URM - SelfIp TCP Entry
589848                0 hits - OSPF - unicast
    589849            71196 hits - OSPFv2 - Multicast
    589850                0 hits - OSPFv3 - Multicast
    589851                0 hits - OSPF Auth ESP - Multicast
    589852                0 hits - OSPF Auth ESP - Unicast
    589853                0 hits - IP packets with GRE type and ISIS protocol
    589854                0 hits - RouterL3 Vlan Priority 6,7 Elevator
    589855                0 hits - RouterL3 DSCP 48-63 Elevator
    589856                0 hits - RouterL3 Priority Elevator
    589857                0 hits - NextHopToCpu, Glean
    589858                0 hits - L3MC Cpu OIF
 IGMP Snooping Flooding reserves 8 entries (6 used).
589864                0 hits - IGMP Snooping Restricted Flooding L3 from local
mlag peer
    589865                0 hits - IGMP Snooping Restricted Flooding L3
 L4 MicroBfd traffic reserves 1 entries (0 used).
TCAM group 13 uses 99 entries and can use up to 1181 more.
 Dot1x MAB traffic uses 1 entries.
    851968                0 hits - Dot1xMab Rule

<-------OUTPUT OMITTED FROM EXAMPLE-------->

ck338.22:14:38(config-pmap-qos-policy1)#`
```


### show route-map


The **show route-map** command displays the contents of configured route maps.


**Command Mode**


EXEC


**Command Syntax**


**show route-map [map_name]**


**Parameters**


- **no parameter** Displays the content of all configured route maps.

- **map_name** Displays the content of the specified route map.


**Examples**


- This command displays the **map1** route map.

```
`switch(config)# **show route-map map1**
route-map map1 permit 10
  Description:
  Match clauses:
  SubRouteMap:
  Set clauses:
    set as-path prepend last-as 12
    set as-path prepend auto auto`
```

- This command displays the **map** route map.

```
`switch> **show route-map map**
route-map map permit 5
  Match clauses:
    match as 456
Set clauses:
route-map map permit 10
  Match clauses:
match ip next-hop 2.3.4.5
    match as-path path_2
  Set clauses:
    set local-preference 100`
```


### system profile


The **system profile** command creates a new Ternary Content-Addressable Memory (TCAM) profile in the running configuration.


The **default system profile** and **no system profile** commands delete non-default TCAM profiles from the running configuration.


**Command Mode**


Hardware TCAM


**Command Syntax**


system profile [profile_name | default | mirroring-acl | pbr-match-nexthop-group | qos | tap-aggregation-default | tap-aggregation-extended | tc-counters]


**default system profile**


**no system profile**


**Parameters**


- **profile_name** - Creates a profile with the specified name.

- **default** - Creates a default profile.

- **mirroring-acl** - Creates a mirroring-ACL profile.

- **pbr-match-nexthop-group** - Creates a pbr-match-nexthop-group profile.

- **qos** - Creates a Quality of Service (QoS) profile.

- **tap-aggregation-default** - Creates a tap-aggregation-default profile.

- **tap-aggregation-extended** - Creates a tap-aggregation-extended profile.

- **tc-counters** - Creates a tc-counters profile.


**Guideline**


Compatible with the DCS-7280SE and DCS-7500E series switches only.


**Examples**


- These commands create a mirroring-ACL profile.

```
`switch(config)# **hardware tcam**
switch(config-hw-tcam)# **system profile mirroring-acl**
switch(config-hw-tcam)# **show hardware tcam profile**
                     Configuration        Status
FixedSystem          mirroring-acl        mirroring-acl
switch(config-hw-tcam)#`
```

- These commands delete non-default TCAM profiles.

```
`switch(config)# **hardware tcam**
switch(config-hw-tcam)#show hardware tcam profile
                     Configuration        Status
Linecard9            mirroring-acl        mirroring-acl
Linecard8            mirroring-acl        mirroring-acl
Linecard3            mirroring-acl        mirroring-acl
Linecard4            mirroring-acl        mirroring-acl
Linecard6            mirroring-acl        mirroring-acl
switch(config-hw-tcam)# **default system profile**
switch(config-hw-tcam)# **show hardware tcam profile**
                     Configuration        Status
Linecard9            default              default
Linecard8            default              default
Linecard3            default              default
Linecard4            default              default
Linecard6            default              default
switch(config-hw-tcam)#`
```

- These commands delete TCAM profiles.

```
`switch(config-hw-tcam)# **show hardware tcam profile**
                     Configuration        Status
Linecard9            tc-counters          tc-counters
Linecard8            tc-counters          tc-counters
Linecard3            tc-counters          tc-counters
Linecard4            tc-counters          tc-counters
Linecard6            tc-counters          tc-counters
switch(config-hw-tcam)# **no system profile**
switch(config-hw-tcam)# **show hardware tcam profile**
                     Configuration        Status
Linecard9            default              default
Linecard8            default              default
Linecard3            default              default
Linecard4            default              default
Linecard6            default              default
switch(config-hw-tcam)#`
```
