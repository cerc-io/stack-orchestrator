# Running a laconicd fixturenet with console

The following tutorial explains the steps to run a laconicd fixturenet with CLI and web console that displays records in the registry. It is designed as an introduction to Stack Orchestrator and to showcase one component of the Laconic Stack. Prior to Stack Orchestrator, the following repositories had to be cloned and setup manually:

- https://git.vdb.to/cerc-io/laconicd
- https://git.vdb.to/cerc-io/laconic-registry-cli
- https://git.vdb.to/cerc-io/laconic-console

Now, with Stack Orchestrator, it is a few quick commands. Additionally, the `docker` and `docker compose` integration on the back-end allows the stack to easily persist, facilitating workflows.

## Setup laconic-so

To avoid hiccups on Mac M1/M2 and any local machine nuances that may affect the user experience, this tutorial is focused on using a fresh Digital Ocean (DO) droplet with similar specs:
16 GB Memory / 8 Intel vCPUs / 160 GB Disk.

1. Login to the droplet as root (either by SSH key or password set in the DO console)
    ```
    ssh root@IP
    ```

1. Get the install script, give it executable permissions, and run it:

    ```
    curl -o install.sh https://raw.githubusercontent.com/cerc-io/stack-orchestrator/main/scripts/quick-install-linux.sh
    ```
    ```
    chmod +x install.sh
    ```
    ```
    bash install.sh
    ```

1. Confirm docker was installed and activate the changes in `~/.profile`:

    ```
    docker run hello-world
   ```
   ```
   source ~/.profile
   ```

1. Verify installation:

    ```
    laconic-so version
    ```

## Setup the laconic fixturenet stack

1. Get the repositories

    ```
    laconic-so --stack fixturenet-laconic-loaded setup-repositories --include git.vdb.to/cerc-io/laconicd
    ```

1. Build the containers:

    ```
    laconic-so --stack fixturenet-laconic-loaded build-containers
    ```

    It's possible to run into an `ESOCKETTIMEDOUT` error, e.g., `error An unexpected error occurred: "https://registry.yarnpkg.com/@material-ui/icons/-/icons-4.11.3.tgz: ESOCKETTIMEDOUT"`. This may happen even if you have a great internet connection. In that case, re-run the `build-containers` command.


1. Set this environment variable to your droplet's IP address or fully qualified DNS host name if it has one:

    ```
    export BACKEND_ENDPOINT=http://<your-IP-or-hostname>:9473
    ```
    e.g.
    ```
    export BACKEND_ENDPOINT=http://my-test-server.example.com:9473
    ```

1. Create a deployment directory for the stack:
    ```
    laconic-so --stack fixturenet-laconic-loaded deploy init --output laconic-loaded.spec --map-ports-to-host any-same --config LACONIC_HOSTED_ENDPOINT=$BACKEND_ENDPOINT

    # Update port mapping in the laconic-loaded.spec file to resolve port conflicts on host if any
    ```
    ```
    laconic-so --stack fixturenet-laconic-loaded deploy create --deployment-dir laconic-loaded-deployment --spec-file laconic-loaded.spec
    ```
2. Start the stack:

    ```
    laconic-so deployment --dir laconic-loaded-deployment start
    ```

3. Check the logs:

    ```
    laconic-so deployment --dir laconic-loaded-deployment logs
    ```

    You'll see output from `laconicd` and the block height should be >1 to confirm it is running:

    ```
    laconicd-1         | 6:12AM INF indexed block events height=16 module=txindex
    laconicd-1         | 6:12AM INF Timed out dur=2993.893332 height=17 module=consensus round=0 step=RoundStepNewHeight
    laconicd-1         | 6:12AM INF received proposal module=consensus proposal="Proposal{17/0 (E15D03C180CE607AE8340A1325A0C134DFB4E1ADD992E173C701EBD362523267:1:DF138772FEF0, -1) 6A6F3B0A42B3 @ 2024-07-25T06:12:31.952967053Z}" proposer=86970D950BC9C16F3991A52D9C6DC55BA478A7C6
    laconicd-1         | 6:12AM INF received complete proposal block hash=E15D03C180CE607AE8340A1325A0C134DFB4E1ADD992E173C701EBD362523267 height=17 module=consensus
    laconicd-1         | 6:12AM INF finalizing commit of block hash=E15D03C180CE607AE8340A1325A0C134DFB4E1ADD992E173C701EBD362523267 height=17 module=consensus num_txs=0 root=AF4941107DC718ED1425E77A3DC7F1154FB780B7A7DE20288DC43442203527E3
    laconicd-1         | 6:12AM INF finalized block block_app_hash=26A665360BB1EE64E54F97F2A5AB7F621B33A86D9896574000C05DE63F43F788 height=17 module=state num_txs_res=0 num_val_updates=0
    laconicd-1         | 6:12AM INF executed block app_hash=26A665360BB1EE64E54F97F2A5AB7F621B33A86D9896574000C05DE63F43F788 height=17 module=state
    laconicd-1         | 6:12AM INF committed state block_app_hash=AF4941107DC718ED1425E77A3DC7F1154FB780B7A7DE20288DC43442203527E3 height=17 module=state
    laconicd-1         | 6:12AM INF indexed block events height=17 module=txindex
    ```

4. Confirm operation of the registry CLI:

   ```
   laconic-so deployment --dir laconic-loaded-deployment exec cli "laconic registry status"
   ```

   ```
   {
     "version": "0.3.0",
     "node": {
       "id": "6e072894aa1f5d9535a1127a0d7a7f8e65100a2c",
       "network": "laconic_9000-1",
       "moniker": "localtestnet"
     },
     "sync": {
       "latestBlockHash": "260102C283D0411CFBA0270F7DC182650FFCA737A2F6F652A985F6065696F590",
       "latestBlockHeight": "49",
       "latestBlockTime": "2024-07-25 06:14:05.626744215 +0000 UTC",
       "catchingUp": false
     },
     "validator": {
       "address": "86970D950BC9C16F3991A52D9C6DC55BA478A7C6",
       "votingPower": "1000000000000000"
     },
     "validators": [
       {
         "address": "86970D950BC9C16F3991A52D9C6DC55BA478A7C6",
         "votingPower": "1000000000000000",
         "proposerPriority": "0"
       }
     ],
     "numPeers": "0",
     "peers": [],
     "diskUsage": "688K"
   }
   ```

## Configure Digital Ocean firewall

(Note this step may not be necessary depending on the droplet image used)

Let's open some ports.

1. In the Digital Ocean web console, navigate to your droplet's main page. Select the "Networking" tab and scroll down to "Firewall".

2. Get the port for the running console:

```
echo http://IP:$(laconic-so --stack fixturenet-laconic-loaded deploy port laconic-console 80 | cut -d ':' -f 2)
```
```
http://IP:32778
```

3. Go back to the Digital Ocean web console and set an Inbound Rule for Custom TCP of the above port:

- `32778` in this example, but yours will be different.
- do the same for port `9473`

Additional ports will need to be opened depending on your application. Ensure you add your droplet to this new Firewall and wait a minute or so for the update to propagate.

4. Navigate to http://IP:port and ensure laconic-console is functioning as expected:

- ensure you are connected to `laconicd`; no error message should pop up;
- the wifi symbol in the bottom right should have a green check mark beside it
- navigate to the status tab; it should display similar/identical information
- navigate to the config tab, you'll see something like (with your IP):

```
wns
  webui http://68.183.195.210:9473/console
  server http://68.183.195.210:9473/api
```

## Publish and query a sample record to the registry

1. The following command will create a bond and publish a record:

```
laconic-so deployment --dir laconic-loaded-deployment exec cli ./scripts/create-demo-records.sh
```

You'll get an output like:

```
Balance is: 9.9999e+25
Created bond with id: dd88e8d6f9567b32b28e70552aea4419c5dd3307ebae85a284d1fe38904e301a
Published demo-record-1.yml with id: bafyreierh3xnfivexlscdwubvczmddsnf46uytyfvrbdhkjzztvsz6ruly
```

The sample record we deployed looks like:

```
record:
  type: WebsiteRegistrationRecord
  url: 'https://cerc.io'
  repo_registration_record_cid: QmSnuWmxptJZdLJpKRarxBMS2Ju2oANVrgbr2xWbie9b2D
  build_artifact_cid: QmP8jTG1m9GSDJLCbeWhVSVgEzCPPwXRdCRuJtQ5Tz9Kc9
  tls_cert_cid: QmbWqxBEKC3P8tqsKc98xmWNzrzDtRLMiMPL8wBuTGsMnR
  version: 1.0.23
```

2. Return to the laconic-console

- the published record should now be viewable
- explore it for more information
- click on the link that opens the GraphQL console
- the query is pre-loaded, click the button to run it
- inspect the output

3. Try out additional CLI commands

- these are documented [here](https://git.vdb.to/cerc-io/laconic-registry-cli#readme) and updates are forthcoming
- e.g,:

```
laconic-so deployment --dir laconic-loaded-deployment exec cli "laconic registry record list"
```
