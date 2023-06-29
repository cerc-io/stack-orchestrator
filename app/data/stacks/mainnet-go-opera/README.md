# Opera (Fantom)

Deploy a Fantom API node.

## Clone required repositories

```
$ laconic-so --stack mainnet-go-opera setup-repositories
```

## Build the fixturenet-eth containers

```
$ laconic-so --stack mainnet-go-opera build-containers
```

## Deploy the stack

```
$ laconic-so --stack mainnet-go-opera deploy up
```

## Check logs

```
$ laconic-so --stack mainnet-go-opera deploy logs
```

You'll see something like:

```
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | Connecting to download.fantom.network (65.108.45.88:443)
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | saving to 'mainnet-109331-no-history.g'
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | mainnet-109331-no-hi 100% |********************************| 16326  0:00:00 ETA
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | 'mainnet-109331-no-history.g' saved
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.034] Maximum peer count                       total=50
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.034] Smartcard socket not found, disabling    err="stat /run/pcscd/pcscd.comm: no such file or directory"
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.034] Genesis file is a known preset           name="Mainnet-109331 without history"
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.052] Applying genesis state 
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.052] - Reading epochs unit 0 
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.054] - Reading blocks unit 0 
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.530] Applied genesis state                    name=main                             id=250 genesis=0x4a53c5445584b3bfc20dbfb2ec18ae20037c716f3ba2d9e1da768a9deca17cb4
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.531] Regenerated local transaction journal    transactions=0 accounts=0
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.532] Starting peer-to-peer node               instance=go-opera/v1.1.2-rc.5-50cd051d-1677276206/linux-amd64/go1.19.10
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.536] New local node record                    seq=1 id=5e40f984908317cd ip=127.0.0.1 udp=5050 tcp=5050
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.537] Started P2P networking                   self=enode://3ffb15988ca5a79b63dbe48be89d9d8b48dc4845d318fe08231a0ab49d3b23476e2561044311dc257405f882f7c52ff7b128c8bd1b6d85cf7205a6fed6555443@127.0.0.1:5050
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.537] IPC endpoint opened                      url=/root/.opera/opera.ipc
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.538] HTTP server started                      endpoint=[::]:18545 prefix= cors=* vhosts=localhost
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.538] WebSocket enabled                        url=ws://[::]:18546
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.538] Rebuilding state snapshot 
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.538] EVM snapshot                             module=gossip-store at=000000..000000 generating=true
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.538] Resuming state snapshot generation       accounts=0 slots=0 storage=0.00B elapsed="189.74µs"
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:33.538] Generated state snapshot                 accounts=0 slots=0 storage=0.00B elapsed="265.061µs"
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:34.788] New LLR summary                          last_epoch=0 last_block=37676611 new_evs=0 new_ers=0 new_bvs=64 new_brs=0 age=none
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:35.040] New local node record                    seq=2 id=5e40f984908317cd ip=186.233.184.56 udp=5050 tcp=5050
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:42.788] New LLR summary                          last_epoch=114604 last_block=37753891 new_evs=24581 new_ers=5272 new_bvs=233257 new_brs=780 age=1y1mo5d
laconic-f028f14527b95e2eb97f0c0229d00939-go-opera-1  | INFO [06-20|13:32:50.827] New LLR summary                          last_epoch=115574 last_block=38118749 new_evs=4907  new_ers=971  new_bvs=1098760 new_brs=3768 age=1y1mo2d
```

Consecutive lines of "New LLR summary" shows that your node is sync'ing.

## Use the opera admin console

```
$ docker exec -it $(docker ps -q --filter "name=go-opera") /bin/sh
```

then:

```
$ ./opera attach
```

and check the node info:

```
> admin.nodeInfo
```

Run `exit` twice to return to your terminal.

## Clean up

Stop all services running in the background:

```bash
$ laconic-so --stack mainnet-go-opera deploy down
```
