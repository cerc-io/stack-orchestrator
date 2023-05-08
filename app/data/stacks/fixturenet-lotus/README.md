# Lotus Fixturenet

Instructions for deploying a local Lotus (Filecoin) chain for development and testing purposes using laconic-stack-orchestrator.

## 1. Clone required repositories
```
$ laconic-so --stack fixturenet-lotus setup-repositories
```
## 2. Build the stack's packages and containers
```
$ laconic-so --stack fixturenet-lotus build-containers
```
## 3. Deploy the stack
```
$ laconic-so --stack fixturenet-lotus deploy up
```
Correct operation should be verified by checking the laconicd container's logs with:
```
$ laconic-so --stack fixturenet-lotus deploy logs
```
## 4. Get the multiaddress of miner node
The full nodes will need the multiaddress of the miner node to form a peer connection. Find the miner's multiaddress with:
```
$ laconic-so --stack fixturenet-lotus deploy exec lotus-miner "lotus net listen"
/ip4/192.168.160.4/tcp/44523/p2p/12D3KooWQiLfXiyQQY79Bn4Yhuti2PwekBc6cccp1rFpCo5WssLC
/ip4/127.0.0.1/tcp/44523/p2p/12D3KooWQiLfXiyQQY79Bn4Yhuti2PwekBc6cccp1rFpCo5WssLC
```
(Your node id will be different) Note the multiaddress and save it for a later step.

## 5. Start the miner
Import the key:
```
$ laconic-so --stack fixturenet-lotus deploy exec lotus-miner "lotus wallet import --as-default ~/.genesis-sectors/pre-seal-t01000.key"
imported key t3spusn5ia57qezc3fwpe3n2lhb4y4xt67xoflqbqy2muliparw2uktevletuv7gl4qakjpafgcl7jk2s2er3q successfully!
```
Init the miner (this will take several minutes):
```
$ laconic-so --stack fixturenet-lotus deploy exec lotus-miner "lotus-miner init --genesis-miner --actor=t01000 --sector-size=2KiB --pre-sealed-sectors=~/.genesis-sectors --pre-sealed-metadata=~/.genesis-sectors/pre-seal-t01000.json --nosync"

...
...
2023-05-08T15:48:32.660Z        INFO    main    lotus-miner/init.go:282 Miner successfully created, you can now start it with 'lotus-miner run'
```
Start the miner:
```
$ laconic-so --stack fixturenet-lotus deploy exec lotus-miner "lotus-miner run --nosync"
```

## 6. Connect the nodes
Connect each full node to the miner using the multiaddress from step 4.
```
$ laconic-so --stack fixturenet-lotus deploy exec lotus-node-1 "lotus net connect <MULTIADDRESS_OF_MINER>"
connect 12D3KooWQiLfXiyQQY79Bn4Yhuti2PwekBc6cccp1rFpCo5WssLC: success

$ laconic-so --stack fixturenet-lotus deploy exec lotus-node-2 "lotus net connect <MULTIADDRESS_OF_MINER>"
connect 12D3KooWQiLfXiyQQY79Bn4Yhuti2PwekBc6cccp1rFpCo5WssLC: success
```
