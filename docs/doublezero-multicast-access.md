# DoubleZero Multicast Access Requests

## Status (2026-03-06)

DZ multicast is **still in testnet** (client v0.2.2). Multicast groups are defined
on the DZ ledger with on-chain access control (publishers/subscribers). The testnet
allocates addresses from 233.84.178.0/24 (AS21682). Not yet available for production
Solana shred delivery.

## Biscayne Connection Details

Provide these details when requesting subscriber access:

| Field | Value |
|-------|-------|
| Client IP | 186.233.184.235 |
| Validator identity | 4WeLUxfQghbhsLEuwaAzjZiHg2VBw87vqHc4iZrGvKPr |
| DZ identity | 3Bw6v7EruQvTwoY79h2QjQCs2KBQFzSneBdYUbcXK1Tr |
| DZ device | laconic-mia-sw01 |
| Contributor / tenant | laconic |

## Jito ShredStream

**Not a DZ multicast group.** ShredStream is Jito's own shred delivery service,
independent of DoubleZero multicast. It provides low-latency shreds from leaders
on the Solana network via a proxy client that connects to the Jito Block Engine.

| Property | Value |
|----------|-------|
| What it does | Delivers shreds from Jito-connected leaders with low latency. Provides a redundant shred path for servers in remote locations. |
| How it works | `shredstream-proxy` authenticates to a Jito Block Engine via keypair, receives shreds, forwards them to configured UDP destinations (e.g. validator TVU port). |
| Cost | **Unknown.** Docs don't list pricing. Was previously "complimentary" for searchers (2024). May require approval. |
| Requirements | Approved Solana pubkey (form submission), auth keypair, firewall open on UDP 20000, TVU port of your node. |
| Regions | Amsterdam, Dublin, Frankfurt, London, New York, Salt Lake City, Singapore, Tokyo. Max 2 regions selectable. |
| Limitations | No NAT support. Bridge networking incompatible with multicast mode. |
| Repo | https://github.com/jito-labs/shredstream-proxy |
| Docs | https://docs.jito.wtf/lowlatencytxnfeed/ |
| Status for biscayne | **Not yet requested.** Need to submit pubkey for approval. |

ShredStream is relevant to our shred completeness problem — it provides an additional
shred source beyond turbine and the Ashburn relay. It would run as a sidecar process
forwarding shreds to the validator's TVU port.

## DZ Multicast Groups

DZ multicast uses PIM (Protocol Independent Multicast) and MSDP (Multicast Source
Discovery Protocol). Group owners define allowed publishers and subscribers on the
DZ ledger. Switch ASICs handle packet replication — no CPU overhead.

### bebop

Listed in earlier notes as a multicast shred distribution group. **No public
documentation found.** Cannot confirm this exists as a DZ multicast group.

- **Owner:** Unknown
- **Status:** Unverified — may not exist as described

### turbine (future)

Solana's native shred propagation via DZ multicast. Jito has expressed interest
in leveraging multicast for shred delivery. Not yet available for production use.

- **Owner:** Solana Foundation / Anza (native turbine), Jito (shredstream)
- **Status:** Testnet only (DZ client v0.2.2)

## bloXroute OFR (Optimized Feed Relay)

Commercial shred delivery service. Runs a gateway docker container on your node that
connects to bloXroute's BDN (Blockchain Distribution Network) to receive shreds
faster than default turbine (~30-50ms improvement, beats turbine ~98% of the time).

| Property | Value |
|----------|-------|
| What it does | Delivers shreds via bloXroute's BDN with optimized relay topologies. Not just a different turbine path — uses their own distribution network. |
| How it works | Docker gateway container on your node, communicates with bloXroute OFR relay over UDP 18888. Forwards shreds to your validator. |
| Cost | **$300/mo** (Professional, 1500 tx/day), **$1,250/mo** (Enterprise, unlimited tx). OFR gateway without local node requires Enterprise Elite ($5,000+/mo). |
| Requirements | Docker, UDP port 18888 open, bloXroute subscription. |
| Open source | Gateway at https://github.com/bloXroute-Labs/solana-gateway |
| Docs | https://docs.bloxroute.com/solana/optimized-feed-relay |
| Status for biscayne | **Not yet evaluated.** Monthly cost may not be justified. |

bloXroute's value proposition: they operate nodes at multiple turbine tree positions
across their network, aggregate shreds, and redistribute via their BDN. This is the
"multiple identities collecting different shreds" approach — but operated by bloXroute,
not by us.

## How These Services Get More Shreds

Turbine tree position is determined by validator identity (pubkey). A single validator
gets shreds from one position in the tree per slot. Services like Jito ShredStream
and bloXroute OFR operate many nodes with different identities across the turbine
tree, aggregate the shreds they each receive, and redistribute the combined set to
subscribers. This is why they can deliver shreds the subscriber's own turbine position
would never see.

**An open-source equivalent would require running multiple lightweight validator
identities (non-voting, minimal stake) at different locations, each collecting shreds
from their unique turbine tree position, and forwarding them to the main validator.**
No known open-source project implements this pattern.

## Sources

- [Jito ShredStream docs](https://docs.jito.wtf/lowlatencytxnfeed/)
- [shredstream-proxy repo](https://github.com/jito-labs/shredstream-proxy)
- [bloXroute OFR docs](https://docs.bloxroute.com/solana/optimized-feed-relay)
- [bloXroute pricing](https://bloxroute.com/pricing/)
- [bloXroute OFR intro](https://bloxroute.com/pulse/introducing-ofrs-faster-shreds-better-performance-on-solana/)
- [DZ multicast announcement](https://doublezero.xyz/journal/doublezero-introduces-multicast-support-smarter-faster-data-delivery-for-distributed-systems)

## Request Template

When contacting a group owner, use something like:

> We'd like to subscribe to your DoubleZero multicast group for our Solana
> validator. Our details:
>
> - Validator: 4WeLUxfQghbhsLEuwaAzjZiHg2VBw87vqHc4iZrGvKPr
> - DZ identity: 3Bw6v7EruQvTwoY79h2QjQCs2KBQFzSneBdYUbcXK1Tr
> - Client IP: 186.233.184.235
> - Device: laconic-mia-sw01
> - Tenant: laconic
