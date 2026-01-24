# mainnet-eth

Deploys a "head-tracking" mainnet Ethereum stack comprising a [go-ethereum](https://github.com/cerc-io/go-ethereum) execution layer node and a [lighthouse](https://github.com/sigp/lighthouse) consensus layer node.

## Clone required repositories

```
$ laconic-so --stack mainnet-eth setup-repositories
```

## Build containers

```
$ laconic-so --stack mainnet-eth build-containers
```

## Create a deployment

```
$ laconic-so --stack mainnet-eth deploy init --map-ports-to-host any-same --output mainnet-eth-spec.yml
$ laconic-so deploy --stack mainnet-eth create --spec-file mainnet-eth-spec.yml --deployment-dir mainnet-eth-deployment
```
## Start the stack
```
$ laconic-so deployment --dir mainnet-eth-deployment start
```
Display stack status:
```
$ laconic-so deployment --dir mainnet-eth-deployment ps
Running containers:
id: f39608eca04d72d6b0f1f3acefc5ebb52908da06e221d20c7138f7e3dff5e423, name: laconic-ef641b4d13eb61ed561b19be67063241-foundry-1, ports:
id: 4052b1eddd886ae0d6b41f9ff22e68a70f267b2bfde10f4b7b79b5bd1eeddcac, name: laconic-ef641b4d13eb61ed561b19be67063241-mainnet-eth-geth-1-1, ports: 30303/tcp, 30303/udp, 0.0.0.0:49184->40000/tcp, 0.0.0.0:49185->6060/tcp, 0.0.0.0:49186->8545/tcp, 8546/tcp
id: ac331232e597944b621b3b8942ace5dafb14524302cab338ff946c7f6e5a1d52, name: laconic-ef641b4d13eb61ed561b19be67063241-mainnet-eth-lighthouse-1-1, ports: 0.0.0.0:49187->8001/tcp
```
See stack logs:
```
$ laconic-so deployment --dir mainnet-eth-deployment logs
time="2023-07-25T09:46:29-06:00" level=warning msg="The \"CERC_SCRIPT_DEBUG\" variable is not set. Defaulting to a blank string."
laconic-ef641b4d13eb61ed561b19be67063241-mainnet-eth-lighthouse-1-1  | Jul 25 15:45:13.362 INFO Logging to file                         path: "/var/lighthouse-data-dir/beacon/logs/beacon.log"
laconic-ef641b4d13eb61ed561b19be67063241-mainnet-eth-lighthouse-1-1  | Jul 25 15:45:13.365 INFO Lighthouse started                      version: Lighthouse/v4.1.0-693886b
laconic-ef641b4d13eb61ed561b19be67063241-mainnet-eth-lighthouse-1-1  | Jul 25 15:45:13.365 INFO Configured for network                  name: mainnet
laconic-ef641b4d13eb61ed561b19be67063241-mainnet-eth-lighthouse-1-1  | Jul 25 15:45:13.366 INFO Data directory initialised              datadir: /var/lighthouse-data-dir
laconic-ef641b4d13eb61ed561b19be67063241-mainnet-eth-lighthouse-1-1  | Jul 25 15:45:13.366 INFO Deposit contract                        address: 0x00000000219ab540356cbb839cbe05303d7705fa, deploy_block: 11184524
laconic-ef641b4d13eb61ed561b19be67063241-mainnet-eth-lighthouse-1-1  | Jul 25 15:45:13.424 INFO Starting checkpoint sync                remote_url: https://beaconstate.ethstaker.cc/, service: beacon
```
## Monitoring stack sync progress
Both go-ethereum and lighthouse will engage in an initial chain sync phase that will last up to several hours depending on hardware performance and network capacity.
Syncing can be monitored by looking for these log messages:
```
Jul 24 12:34:17.001 INFO Downloading historical blocks           est_time: 5 days 11 hrs, speed: 14.67 slots/sec, distance: 6932481 slots (137 weeks 3 days), service: slot_notifier
INFO [07-24|12:14:52.493] Syncing beacon headers                   downloaded=145,920 left=17,617,968 eta=1h23m32.815s
INFO [07-24|12:33:15.238] Syncing: chain download in progress      synced=1.86% chain=148.94MiB headers=368,640@95.03MiB bodies=330,081@40.56MiB receipts=330,081@13.35MiB eta=37m54.505s
INFO [07-24|12:35:13.028] Syncing: state download in progress      synced=1.32% state=4.64GiB   accounts=2,850,314@677.57MiB slots=18,663,070@3.87GiB  codes=26662@111.14MiB eta=3h18m0.699s
```
Once synced up these log messages will be observed:
```
INFO Synced                                  slot: 6952515, block: 0x5bcb…f6d9, epoch: 217266, finalized_epoch: 217264, finalized_root: 0x6342…2c5c, exec_hash: 0x8d8c…2443 (verified), peers: 31, service: slot_notifier
INFO [07-25|03:04:48.941] Imported new potential chain segment     number=17,767,316 hash=84f6e7..bc2cb0 blocks=1  txs=137  mgas=16.123  elapsed=57.087ms     mgasps=282.434 dirty=461.46MiB
INFO [07-25|03:04:49.042] Chain head was updated                   number=17,767,316 hash=84f6e7..bc2cb0 root=ca58b2..8258c1 elapsed=2.480111ms
```
## Clean up

Stop the stack:
```
$ laconic-so deployment --dir mainnet-eth-deployment stop
```
This leaves data volumes in place, allowing the stack to be subsequently re-started.
To permanently *delete* the stack's data volumes run:
```
$ laconic-so deployment --dir mainnet-eth-deployment stop --delete-data-volumes
```
After deleting the volumes, any subsequent re-start will begin chain sync from cold.

## Ports
It is usually necessary to expose certain container ports on one or more the host's addresses to allow incoming connections.
Any ports defined in the Docker compose file are exposed by default with random port assignments, bound to "any" interface (IP address 0.0.0.0), but the port mappings can be
customized by editing the "spec" file generated by `laconic-so deploy init`.

In this example, ports `8545` and `5052` have been assigned to a specific addresses/port combination on the host, while
port `40000` has been left with random assignment:
```
$ cat mainnet-eth-spec.yml
stack: mainnet-eth
ports:
  mainnet-eth-geth-1:
   - '10.10.10.10:8545:8545'
   - '40000'
  mainnet-eth-lighthouse-1:
   - '10.10.10.10:5052:5052'
volumes:
  mainnet_eth_config_data: ./data/mainnet_eth_config_data
  mainnet_eth_geth_1_data: ./data/mainnet_eth_geth_1_data
  mainnet_eth_lighthouse_1_data: ./data/mainnet_eth_lighthouse_1_data
```
In addition, a stack-wide port mapping "recipe" can be applied at the time the
`laconic-so deploy init` command is run, by supplying the  desired recipe with the `--map-ports-to-host` option. The following recipes are supported:
| Recipe | Host Port Mapping |
|--------|-------------------|
| any-variable-random | Bind to 0.0.0.0 using a random port assigned at start time (default) |
| localhost-same | Bind to 127.0.0.1 using the same port number as exposed by the containers |
| any-same | Bind to 0.0.0.0 using the same port number as exposed by the containers |
| localhost-fixed-random | Bind to 127.0.0.1 using a random port number selected at the time the command is run (not checked for already in use)|
| any-fixed-random | Bind to 0.0.0.0 using a random port number selected at the time the command is run (not checked for already in use) |
## Data volumes
Container data volumes are bind-mounted to specified paths in the host filesystem.
The default setup (generated by `laconic-so deploy init`) places the volumes in the `./data` subdirectory of the deployment directory:
```
$ cat mainnet-eth-spec.yml
stack: mainnet-eth
ports:
  mainnet-eth-geth-1:
   - '10.10.10.10:8545:8545'
   - '40000'
  mainnet-eth-lighthouse-1:
   - '10.10.10.10:5052:5052'
volumes:
  mainnet_eth_config_data: ./data/mainnet_eth_config_data
  mainnet_eth_geth_1_data: ./data/mainnet_eth_geth_1_data
  mainnet_eth_lighthouse_1_data: ./data/mainnet_eth_lighthouse_1_data
```
A synced-up stack will consume around 900GB of data volume space:
```
$ sudo du -h mainnet-eth-deployment/data/
150M    mainnet-eth-deployment/data/mainnet_eth_lighthouse_1_data/beacon/freezer_db
25G     mainnet-eth-deployment/data/mainnet_eth_lighthouse_1_data/beacon/chain_db
16K     mainnet-eth-deployment/data/mainnet_eth_lighthouse_1_data/beacon/network
368M    mainnet-eth-deployment/data/mainnet_eth_lighthouse_1_data/beacon/logs
26G     mainnet-eth-deployment/data/mainnet_eth_lighthouse_1_data/beacon
26G     mainnet-eth-deployment/data/mainnet_eth_lighthouse_1_data
8.0K    mainnet-eth-deployment/data/mainnet_eth_config_data
4.0K    mainnet-eth-deployment/data/mainnet_eth_geth_1_data/keystore
527G    mainnet-eth-deployment/data/mainnet_eth_geth_1_data/geth/chaindata/ancient/chain
527G    mainnet-eth-deployment/data/mainnet_eth_geth_1_data/geth/chaindata/ancient
859G    mainnet-eth-deployment/data/mainnet_eth_geth_1_data/geth/chaindata
4.8M    mainnet-eth-deployment/data/mainnet_eth_geth_1_data/geth/nodes
242M    mainnet-eth-deployment/data/mainnet_eth_geth_1_data/geth/ethash
669M    mainnet-eth-deployment/data/mainnet_eth_geth_1_data/geth/triecache
860G    mainnet-eth-deployment/data/mainnet_eth_geth_1_data/geth
860G    mainnet-eth-deployment/data/mainnet_eth_geth_1_data
885G    mainnet-eth-deployment/data/
```
