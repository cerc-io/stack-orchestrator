# Shred Collector Relay

## Problem

Turbine assigns each validator a single position in the shred distribution tree
per slot, determined by its pubkey. A validator in Miami with one identity receives
shreds from one set of tree neighbors — typically ~60-70% of shreds for any given
slot. The remaining 30-40% must come from the repair protocol, which is too slow
to keep pace with chain production (see analysis below).

Commercial services (Jito ShredStream, bloXroute OFR) solve this by running many
nodes with different identities across the turbine tree, aggregating shreds, and
redistributing the combined set to subscribers. This works but costs $300-5,000/mo
and adds a dependency on a third party.

## Concept

Run lightweight **shred collector** nodes at multiple geographic locations on
the Laconic network (Ashburn, Dallas, etc.). Each collector has its own keypair,
joins gossip with a unique identity, receives turbine shreds from its unique tree
position, and forwards raw shred packets to the main validator in Miami. The main
validator inserts these shreds into its blockstore alongside its own turbine shreds,
increasing completeness toward 100% without relying on repair.

```
                    Turbine Tree
                   /     |      \
                  /      |       \
    collector-ash    collector-dfw    biscayne (main validator)
    (Ashburn)        (Dallas)         (Miami)
    identity A       identity B       identity C
    ~60% shreds      ~60% shreds      ~60% shreds
         \               |               /
          \              |              /
           → UDP forward via DZ backbone →
                         |
                    biscayne blockstore
                    ~95%+ shreds (union of A∪B∪C)
```

Each collector sees a different ~60% slice of the turbine tree. The union of
three independent positions yields ~94% coverage (1 - 0.4³ = 0.936). Four
collectors yield ~97%. The main validator fills the remaining few percent via
repair, which is fast when only 3-6% of shreds are missing.

## Why This Works

The math from biscayne's recovery (2026-03-06):

| Metric | Value |
|--------|-------|
| Compute-bound replay (complete blocks) | 5.2 slots/sec |
| Repair-bound replay (incomplete blocks) | 0.5 slots/sec |
| Chain production rate | 2.5 slots/sec |
| Turbine + relay delivery per identity | ~60-70% |
| Repair bandwidth | ~600 shreds/sec (estimated) |
| Repair needed to converge at 60% delivery | 5x current bandwidth |
| Repair needed to converge at 95% delivery | Easily sufficient |

At 60% shred delivery, repair must fill 40% per slot — too slow to converge.
At 95% delivery (3 collectors), repair fills 5% per slot — well within capacity.
The validator replays at near compute-bound speed (5+ slots/sec) and converges.

## Infrastructure

Laconic already has DZ-connected switches at multiple sites:

| Site | Device | Latency to Miami | Backbone |
|------|--------|-------------------|----------|
| Miami | laconic-mia-sw01 | 0.24ms | local |
| Ashburn | laconic-was-sw01 | ~29ms | Et4/1 25.4ms |
| Dallas | laconic-dfw-sw01 | ~30ms | TBD |

The DZ backbone carries traffic between sites at line rate. Shred packets are
~1280 bytes each. At ~3,000 shreds/slot and 2.5 slots/sec, each collector
forwards ~7,500 packets/sec (~10 MB/s) — trivial bandwidth for the backbone.

## Collector Architecture

The collector does NOT need to be a full validator. It needs to:

1. **Join gossip** — advertise a ContactInfo with its own pubkey and a TVU
   address (the site's IP)
2. **Receive turbine shreds** — UDP packets on the advertised TVU port
3. **Forward shreds** — retransmit raw UDP packets to biscayne's TVU port

It does NOT need to: replay transactions, maintain accounts state, store a
ledger, load a snapshot, vote, or run RPC.

### Option A: Firedancer Minimal Build

Firedancer (Apache 2, C) has a tile-based architecture where each function
(net, gossip, shred, bank, store, etc.) runs as an independent Linux process.
A minimal build using only the networking + gossip + shred tiles would:

- Join gossip and advertise a TVU address
- Receive turbine shreds via the shred tile
- Forward shreds to a configured destination instead of to bank/store

This requires modifying the shred tile to add a UDP forwarder output instead
of (or in addition to) the normal bank handoff. The rest of the tile pipeline
(bank, pack, poh, store) is simply not started.

**Estimated effort:** Moderate. Firedancer's tile architecture is designed for
this kind of composition. The main work is adding a forwarder sink to the shred
tile and testing gossip participation without the full validator stack.

**Source:** https://github.com/firedancer-io/firedancer

### Option B: Agave Non-Voting Minimal

Run `agave-validator --no-voting` with `--limit-ledger-size 0` and minimal
config. Agave still requires a snapshot to start and runs the full process, but
with no voting and minimal ledger it would be lighter than a full node.

**Downside:** Agave is monolithic — you can't easily disable replay/accounts.
It still loads a snapshot, builds the accounts index, and runs replay. This
defeats the purpose of a lightweight collector.

### Option C: Custom Gossip + TVU Receiver

Write a minimal Rust binary using agave's `solana-gossip` and `solana-streamer`
crates to:
1. Bootstrap into gossip via entrypoints
2. Advertise ContactInfo with TVU socket
3. Receive shred packets on TVU
4. Forward them via UDP

**Estimated effort:** Significant. Gossip protocol participation is complex
(CRDS protocol, pull/push protocol, protocol versioning). Using the agave
crates directly is possible but poorly documented for standalone use.

### Option D: Run Collectors on Biscayne

Run the collector processes on biscayne itself, each advertising a TVU address
at a remote site. The switches at each site forward inbound TVU traffic to
biscayne via the DZ backbone using traffic-policy redirects (same pattern as
`ashburn-validator-relay.md`).

**Advantage:** No compute needed at remote sites. Just switch config + loopback
IPs. All collector processes run in Miami.

**Risk:** Gossip advertises IP + port. If the collector runs on biscayne but
advertises an Ashburn IP, gossip protocol interactions (pull requests, pings)
arrive at the Ashburn IP and must be forwarded back to biscayne. This adds
~58ms RTT to gossip protocol messages, which may cause timeouts or peer
quality degradation. Needs testing.

## Recommendation

Option A (Firedancer minimal build) is the correct long-term approach. It
produces a single binary that does exactly one thing: collect shreds from a
unique turbine tree position and forward them. It runs on minimal hardware
(a small VM or container at each site, or on biscayne with remote TVU
addresses).

Option D (collectors on biscayne with switch forwarding) is the fastest to
test since it needs no new software — just switch config and multiple
agave-validator instances with `--no-voting`. The question is whether agave
can start without a snapshot if we only care about gossip + TVU.

## Deployment Topology

```
biscayne (186.233.184.235)
├── agave-validator (main, identity C, TVU 186.233.184.235:9000)
├── collector-ash (identity A, TVU 137.239.194.65:9000)
│   └── shreds forwarded via was-sw01 traffic-policy
├── collector-dfw (identity B, TVU <dfw-ip>:9000)
│   └── shreds forwarded via dfw-sw01 traffic-policy
└── blockstore receives union of A∪B∪C shreds

was-sw01 (Ashburn)
└── Loopback: 137.239.194.65
└── traffic-policy: UDP dst 137.239.194.65:9000 → nexthop mia-sw01

dfw-sw01 (Dallas)
└── Loopback: <assigned IP>
└── traffic-policy: UDP dst <assigned IP>:9000 → nexthop mia-sw01
```

## Open Questions

1. Can agave-validator start in gossip-only mode without a snapshot?
2. Does Firedancer's shred tile work standalone without bank/replay?
3. What is the gossip protocol timeout for remote TVU addresses (Option D)?
4. How does the turbine tree handle multiple identities from the same IP
   (if running all collectors on biscayne)?
5. Do we need stake on collector identities to be placed in the turbine tree,
   or do unstaked nodes still participate?
6. What IP block is available on dfw-sw01 for a collector loopback?
