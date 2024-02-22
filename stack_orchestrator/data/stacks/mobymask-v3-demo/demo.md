# Demo

## Setup

* Follow logs and check that all 3 watchers are running in consensus:

  ```bash
  # Follow the logs in three different terminals and keep them running
  docker logs -f $(docker ps --filter "name=mobymask-watcher-1" -q)
  docker logs -f $(docker ps --filter "name=mobymask-watcher-2" -q)
  docker logs -f $(docker ps --filter "name=mobymask-watcher-3" -q)

  # Expected output when all three are running in consensus:
  # ...
  # 2024-02-21T10:42:23.932Z laconic:consensus State changed to 3 (FOLLOWER) with term 286
  # 2024-02-21T10:42:23.932Z laconic:consensus State changed to 2 (CANDIDATE) with term 287
  # 2024-02-21T10:42:24.406Z laconic:consensus State changed to 1 (LEADER) with term 287
  # ...

  # At any moment, only one of watchers is the 'LEADER'
  ```

* In MetaMask, go to settings add a custom network with the following settings:

  ```bash
  # Network name
  Local Optimism

  # New RPC URL
  http://127.0.0.1:8545

  # Chain ID
  42069

  # Currency symbol
  ETH
  ```

  Switch to the newly added network

* Import a pre-funded account (using it's private key) for Nitro client in the MobyMask app:

  ```bash
  # PK: 689af8efa8c651a91ad287602527f3af2fe9f6501a7ac4b061667b5a93e037fd
  # Address: 0xbDA5747bFD65F08deb54cb465eB87D40e51B197E
  ```

## Run

### Open MobyMask app

* Copy the generated invite link from MobyMask deployment container logs:

  ```bash
  docker logs -f $(docker ps -a --filter "name=mobymask-1" -q)

  # A SIGNED DELEGATION/INVITE LINK:
  # ...
  # http://127.0.0.1:3004/#/members?invitation=<INVITATION>
  ```

* Open the invite link in browser where MetaMask was setup

* In the app’s debug panel (bottom-right), check from `PEERS` and `GRAPH` tabs that the peer gets connected to relay nodes and watcher peers

* Perform phisher status checks from the app
  * First 10 queries are served for free; repeat until the free quota is exhausted
  * Same can be seen in the watcher-1's logs (the app makes all the GQL queries to watcher-1):

    ```bash
    # ...
    # 2024-02-21T11:01:20.084Z laconic:payments Query rate not configured for "latestBlock", serving free query
    # 2024-02-21T11:01:20.084Z vulcanize:resolver latestBlock
    # 2024-02-21T11:01:20.108Z laconic:payments Serving a free query to 0x3c9B491ACA5cf17B6C11E39bbFddCA603F387d41
    # 2024-02-21T11:01:20.109Z vulcanize:resolver isPhisher 0xf8995f83bbab2bc13fb9a43c6fea4a605616e6f59503f36cbe2ad3abffd0efd3 0xAFA36c47E130d89bcE4470a9030d99f3CEcaD146 TWT:dummyPhisher
    # 2024-02-21T11:01:20.113Z vulcanize:indexer isPhisher: db miss, fetching from upstream server
    # ...

    # After free quota has been exhausted:
    # 2024-02-21T11:06:49.311Z laconic:payments Query rate not configured for "latestBlock", serving free query
    # 2024-02-21T11:06:49.312Z vulcanize:resolver latestBlock
    # 2024-02-21T11:06:49.337Z laconic:payments Rejecting query from 0x3c9B491ACA5cf17B6C11E39bbFddCA603F387d41: Free quota exhausted
    ```

### Setup app's Nitro node

* Open the `NITRO` tab in debug panel

* Click on `Connect Wallet` button to connect to MetaMask (use the imported account with funds)

* Click on `Connect Snap` to install / connect snap; the watcher Nitro clients should show up in the `NITRO` tab

* Click on `DIRECT FUND` button against watcher-1's Nitro account (`0xAAA6628Ec44A8a742987EF3A114dDFE2D4F7aDCE`) to create a ledger channel with the pre-set amount
  * Confirm the tx in MetaMask popup; wait some time for the tx to be confirmed and ledger channel to be created
  * The progress can be followed from watcher-1's logs
  * The created ledger channel should now be visible in the `NITRO` tab; click on `REFRESH` button otherwise

* Change amount to `10000` and click on `VIRTUAL FUND` button to create a virtual payment channel
  * This results in a payment channel between the app and watcher-1
  * The payment channel's details should now be visible along with a `PAY` and `VIRTUAL DEFUND` buttons

* Close the debug panel

### Paid queries and mutations

* Perform phisher status checks now that a payment channel has been created
  * Amount set in the debug panel's `NITRO` tab is sent along with each request to the watcher
  * Check the watcher-1 logs for the received payments:

    ```bash
    # ...
    # 2024-02-21T11:35:25.538Z ts-nitro:engine {"msg":"Received message","_msg":{"to":"0xAAA662","from":"0x5D12ac","payloadSummaries":[],"proposalSummaries":[],"payments":[{"amount":50,"channelId":"0x654a85725442828f89b497e3973640613c03b5f5ec47302bfa4402d42c07de30"}],"rejectedObjectives":[]}}
    # 2024-02-21T11:35:25.552Z laconic:payments Query rate not configured for "latestBlock", serving free query
    # 2024-02-21T11:35:25.553Z vulcanize:resolver latestBlock
    # 2024-02-21T11:35:25.557Z laconic:payments Received a payment voucher of 50 from 0x5D12acfbBB1caD65fD61983003a50E0CB6900Fd3
    # 2024-02-21T11:35:25.570Z laconic:payments Serving a paid query for 0x5D12acfbBB1caD65fD61983003a50E0CB6900Fd3
    # 2024-02-21T11:35:25.570Z vulcanize:resolver isPhisher 0x6a1f0dce967aefd4adf7762c523cde358960236f05734f616ebe69c0abfcb0cc 0xAFA36c47E130d89bcE4470a9030d99f3CEcaD146 TWT:dummyPhisher
    # 2024-02-21T11:35:25.580Z vulcanize:indexer isPhisher: db miss, fetching from upstream server
    # ...
    ```

* Rate for mutations is set to `100` in the watcher; go back to the `NITRO` tab in the debug panel and change amount value besides `PAY` button to >=100

* Perform a phisher report
  * Enter a new record(s) and click on `Submit batch to p2p network` button
  * Among all three watchers running in consensus, whoever is the `LEADER` at time of reporting sends a tx to the chain
  * Check all the watchers' logs:

    If the payment receiving watcher (1) is leader at that moment:

    ```bash
    # On watcher-1 (payment received + tx sent)
    # ...
    # 2024-02-21T11:42:55.088Z vulcanize:libp2p-utils [11:42:55] Received a message on mobymask P2P network from peer: 12D3KooWGXxcwevUY7KCfw8fcGhxqxPaiFMGSU4tgJDjE54QGKzf
    # 2024-02-21T11:42:55.102Z ts-nitro:engine {"msg":"Received message","_msg":{"to":"0xAAA662","from":"0x5D12ac","payloadSummaries":[],"proposalSummaries":[],"payments":[{"amount":150,"channelId":"0x654a85725442828f89b497e3973640613c03b5f5ec47302bfa4402d42c07de30"}],"rejectedObjectives":[]}}
    # 2024-02-21T11:42:55.115Z laconic:payments Received a payment voucher of 100 from 0x5D12acfbBB1caD65fD61983003a50E0CB6900Fd3
    # 2024-02-21T11:42:55.115Z vulcanize:libp2p-utils Payment received for a mutation request from 0x5D12acfbBB1caD65fD61983003a50E0CB6900Fd3
    # 2024-02-21T11:42:59.115Z vulcanize:libp2p-utils Transaction receipt for invoke message {
    #   to: '0xAFA36c47E130d89bcE4470a9030d99f3CEcaD146',
    #   blockNumber: 4638,
    #   blockHash: '0x23a42bc2ae43771c62b0d59cc48b5858e6e2e488953527ba6a9f5119ae72b42a',
    #   transactionHash: '0xb61cfdfd0ffe937a191a230e1355b9bc5cdd32507f7b4f24a8e6356adf089b64',
    #   effectiveGasPrice: '1500000050',
    #   gasUsed: '136450'
    # }
    # ...

    # On other watchers (payment not received + tx not sent)
    ...
    # 2024-02-21T11:42:50.329Z laconic:consensus State changed to 3 (FOLLOWER) with term 478
    # 2024-02-21T11:42:55.089Z vulcanize:libp2p-utils [11:42:55] Received a message on mobymask P2P network from peer: 12D3KooWGXxcwevUY7KCfw8fcGhxqxPaiFMGSU4tgJDjE54QGKzf
    # 2024-02-21T11:42:55.096Z vulcanize:libp2p-utils Not a leader, skipped sending L2 tx
    # 2024-02-21T11:43:05.095Z vulcanize:libp2p-utils Payment not received
    # ...
    ```

    If the payment receiving watcher (1) is NOT leader at that moment:

    ```bash
    # On watcher 1 (payment received + tx not sent)
    # ...
    # 2024-02-21T11:46:52.049Z vulcanize:libp2p-utils [11:46:52] Received a message on mobymask P2P network from peer: 12D3KooWGXxcwevUY7KCfw8fcGhxqxPaiFMGSU4tgJDjE54QGKzf
    # 2024-02-21T11:46:52.051Z vulcanize:libp2p-utils Not a leader, skipped sending L2 tx
    # 2024-02-21T11:46:52.074Z ts-nitro:engine {"msg":"Received message","_msg":{"to":"0xAAA662","from":"0x5D12ac","payloadSummaries":[],"proposalSummaries":[],"payments":[{"amount":450,"channelId":"0x654a85725442828f89b497e3973640613c03b5f5ec47302bfa4402d42c07de30"}],"rejectedObjectives":[]}}
    # 2024-02-21T11:46:52.097Z laconic:payments Received a payment voucher of 100 from 0x5D12acfbBB1caD65fD61983003a50E0CB6900Fd3
    # 2024-02-21T11:46:52.097Z vulcanize:libp2p-utils Payment received for a mutation request from 0x5D12acfbBB1caD65fD61983003a50E0CB6900Fd3
    # ...

    # On the leader watcher (payment not received + tx sent)
    # ...
    # 2024-02-21T11:46:40.111Z vulcanize:libp2p-utils Payment not received
    # 2024-02-21T11:46:52.048Z vulcanize:libp2p-utils [11:46:52] Received a message on mobymask P2P network from peer: 12D3KooWGXxcwevUY7KCfw8fcGhxqxPaiFMGSU4tgJDjE54QGKzf
    # 2024-02-21T11:46:56.048Z vulcanize:libp2p-utils Transaction receipt for invoke message {
    #   to: '0xAFA36c47E130d89bcE4470a9030d99f3CEcaD146',
    #   blockNumber: 4757,
    #   blockHash: '0x859aa54cb02e8a3f910a01b85c2a7bf9bff7540e83018e7e846f87ca1770e55e',
    #   transactionHash: '0x92f087e4b6ac5604c9d4ecd823d526ca5f8f1bf5c2a92861d6b0f69bd899ba83',
    #   effectiveGasPrice: '1500000050',
    #   gasUsed: '136438'
    # }
    ```

* Check phisher status for the reported phishers to confirm state update

## Clean up

* From the `NITRO` tab in debug panel, perform `VIRTUAL DEFUND` and `DIRECT DEFUND` (in order) for any payment channels created

* In the browser's console, delete all indexedDBs:

  ```bash
  await clearNodeStorage()
  ```

* Remove the snap from MetaMask flask extension
