# Demo

* Get the root invite link URL for mobymask-app:

  ```bash
  laconic-so --stack mobymask-v2 deploy-system logs mobymask

  # If only running watcher-mobymask-v2 pod
  laconic-so --stack mobymask-v2 deploy-system --include watcher-mobymask-v2 logs mobymask
  ```

  The invite link is seen at the end of the logs. Example log:

  ```bash
  laconic-bfb01caf98b1b8f7c8db4d33f11b905a-mobymask-1  | http://127.0.0.1:3002/#/members?invitation=%7B%22v%22%3A1%2C%22signedDelegations%22%3A%5B%7B%22signature%22%3A%220x7559bd412f02677d60820e38243acf61547f79339395a34f7d4e1630e645aeb30535fc219f79b6fbd3af0ce3bd05132ad46d2b274a9fbc4c36bc71edd09850891b%22%2C%22delegation%22%3A%7B%22delegate%22%3A%220xc0838c92B2b71756E0eAD5B3C1e1F186baeEAAac%22%2C%22authority%22%3A%220x0000000000000000000000000000000000000000000000000000000000000000%22%2C%22caveats%22%3A%5B%7B%22enforcer%22%3A%220x558024C7d593B840E1BfD83E9B287a5CDad4db15%22%2C%22terms%22%3A%220x0000000000000000000000000000000000000000000000000000000000000000%22%7D%5D%7D%7D%5D%2C%22key%22%3A%220x98da9805821f1802196443e578fd32af567bababa0a249c07c82df01ecaa7d8d%22%7D
  ```

* Open the invite link in a browser to use the mobymask-app.

  NOTE: Before opening the invite link, clear the browser cache (local storage) for http://127.0.0.1:3002 to remove old invitations

* In the debug panel, check if it is connected to the p2p network (it should be connected to at least one other peer for pubsub to work).

* Create an invite link in the app by clicking on `Create new invite link` button.

* Switch to the `MESSAGES` tab in debug panel for viewing incoming messages later.

* Open the invite link in a new browser with different profile (to simulate remote browser)
  * Check that it is connected to any other peer in the network.

* In `Report a phishing attempt` section, report multiple phishers using the `submit` button. Click on the `Submit batch to p2p network` button. This broadcasts signed invocations to the connected peers.

* In the `MESSAGES` tab of other browsers, a message can be seen with the signed invocations.

* In a terminal check logs from the watcher peer container.

  * Get the container id:

    ```bash
    laconic-so --stack mobymask-v2 deploy-system ps | grep mobymask-watcher-server

    # If only running watcher-mobymask-v2 pod
    laconic-so --stack mobymask-v2 deploy-system --include watcher-mobymask-v2 ps | grep mobymask-watcher-server
    ```

  * Check logs:

    ```bash
    docker logs -f <CONTAINER_ID>
    ```

* It should have received the message, sent transaction to L2 chain and received a transaction receipt for an `invoke` message with block details.

  Example log:

  ```bash
  2023-03-23T10:25:19.771Z vulcanize:peer-listener [10:25:19] Received a message on mobymask P2P network from peer: 12D3KooWAVNswtcrX12iDYukEoxdQwD34kJyRWcQTfZ4unGg2xjd
  2023-03-23T10:25:24.143Z laconic:libp2p-utils Transaction receipt for invoke message {
    to: '0x558024C7d593B840E1BfD83E9B287a5CDad4db15',
    blockNumber: 1996,
    blockHash: '0xebef19c21269654804b2ef2d4bb5cb6c88743b37ed77e82222dc5671debf3afb',
    transactionHash: '0xf8c5a093a93f793012196073a7d0cb3ed6fbd2846126c066cb31c72100960cb1',
    effectiveGasPrice: '1500000007',
    gasUsed: '250000'
  }
  ```

* Check the phisher in watcher GQL: http://localhost:3001/graphql
  * Use the blockHash from transaction receipt details or query for latest block:

    ```gql
    query {
      latestBlock {
        hash
        number
      }
    }
    ```

  * Get the deployed contract address:

    ```bash
    laconic-so --stack mobymask-v2 deploy-system exec mobymask-app "cat src/config.json"

    # If only running watcher-mobymask-v2 pod
    laconic-so --stack mobymask-v2 deploy-system --include watcher-mobymask-v2 exec mobymask-app "cat src/config.json"
    ```

    The value of `address` field is the deployed contract address

  * Check for phisher value

    ```gql
    query {
      isPhisher(
        blockHash: "TX_OR_LATEST_BLOCK_HASH",
        contractAddress: "CONTRACT_ADDRESS",
        # If reported phisher name was "test" then key0 value is "TWT:test"
        key0: "TWT:PHISHER_NAME"
      ) {
        value
      }
    }
    ```

    It should return `true` for reported phisher names.

  * Watcher internally is using L2 chain `eth_getStorageAt` method.

* Check the phisher name in mobymask app in `Check Phisher Status` section.
    * Watcher GQL API is used for checking phisher.

* Manage the invitations by clicking on the `Outstanding Invitations in p2p network`.

* Revoke the created invitation by clicking on `Revoke (p2p network)`

* Revocation messages can be seen in the debug panel `MESSAGES` tab of other browsers.

* Check the watcher peer logs. It should receive a message and log the transaction receipt for a `revoke` message.

* Try reporting a phisher from the revoked invitee's browser.

  * The invocation message for reporting phisher would be broadcasted to all peers.

  * Check the watcher peer logs. A transaction failed error should be logged.

  * Check the reported phisher in [watcher GQL](https://localhost:3001/graphql)

    ```gql
    query {
      isPhisher(
        blockHash: "LATEST_BLOCK_HASH",
        contractAddress: "CONTRACT_ADDRESS",
        key0: "TWT:PHISHER_NAME"
      ) {
        value
      }
    }
    ```

    It should return `false` as the invitation/delegation used for reporting phishers has been revoked.
