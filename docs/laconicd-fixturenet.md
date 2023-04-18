# Running a laconicd fixturenet with console

The following tutorial explains the steps to run a laconicd fixturenet with CLI and web console that displays records in the registry. It is designed as an introduction to Stack Orchestrator and to showcase one component of the Laconic Stack. Prior to Stack Orchestrator, the following 4 repositories had to be cloned and setup manually:

- https://github.com/cerc-io/laconicd
- https://github.com/cerc-io/laconic-sdk
- https://github.com/cerc-io/laconic-registry-cli
- https://github.com/cerc-io/laconic-console

Now, with Stack Orchestrator, it is a few quick commands. Additionally, the `docker` and `docker compose` integration on the back-end allows the stack to easily persist, facilitating workflows.

## Setup laconic-so

To avoid hiccups on Mac M1/M2 and any local machine nuances that may affect the user experience, this tutorial is focused on using a fresh Digital Ocean (DO) droplet with similar specs: 
16 GB Memory / 8 Intel vCPUs / 160 GB Disk.

1. Login to the droplet as root (either by SSH key or password set in the DO console)

```
ssh root@IP
```

2. Get the install script, give it executable permissions, and run it:

```
curl -o install.sh https://raw.githubusercontent.com/cerc-io/stack-orchestrator/main/scripts/quick-install-ubuntu.sh
```
```
chmod +x install.sh
```
```
bash install.sh
```

3. Confirm docker was installed and activate the changes in `~/.profile`:

```
docker run hello-world
```
```
source ~/.profile
```

4. Verify installation:

```
laconic-so version
```

## Setup the laconic fixturenet stack

1. Get the repositories

```
laconic-so --stack fixturenet-laconic-loaded setup-repositories --include cerc-io/laconicd,cerc-io/laconic-sdk,cerc-io/laconic-registry-cli,cerc-io/laconic-console
```

2. Set this environment variable to the Laconic self-hosted Gitea instance:

```
export CERC_NPM_REGISTRY_URL=https://git.vdb.to/api/packages/cerc-io/npm/
```

3. Build the containers:

```
laconic-so --stack fixturenet-laconic-loaded build-containers
```

It's possible to run into an `ESOCKETTIMEDOUT` error, e.g., `error An unexpected error occurred: "https://registry.yarnpkg.com/@material-ui/icons/-/icons-4.11.3.tgz: ESOCKETTIMEDOUT"`. This may happen even if you have a great internet connection. In that case, re-run the `build-containers` command.

4. Set this environment variable to your droplet's IP address:

```
export LACONIC_HOSTED_ENDPOINT=http://68.183.195.210
```

5. Deploy the stack:

```
laconic-so --stack fixturenet-laconic-loaded deploy up
```

6. Check the logs:

```
laconic-so --stack fixturenet-laconic-loaded deploy logs
```

You'll see output from `laconicd` and the block height should be >1 to confirm it is running:

```
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:29PM INF indexed block exents height=12 module=txindex server=node
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:30PM INF Timed out dur=4976.960115 height=13 module=consensus round=0 server=node step=1
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:30PM INF received proposal module=consensus proposal={"Type":32,"block_id":{"hash":"D26C088A711F912ADB97888C269F628DA33153795621967BE44DCB43C3D03CA4","parts":{"hash":"22411A20B7F14CDA33244420FBDDAF24450C0628C7A06034FF22DAC3699DDCC8","total":1}},"height":13,"pol_round":-1,"round":0,"signature":"DEuqnaQmvyYbUwckttJmgKdpRu6eVm9i+9rQ1pIrV2PidkMNdWRZBLdmNghkIrUzGbW8Xd7UVJxtLRmwRASgBg==","timestamp":"2023-04-18T21:30:01.49450663Z"} server=node
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:30PM INF received complete proposal block hash=D26C088A711F912ADB97888C269F628DA33153795621967BE44DCB43C3D03CA4 height=13 module=consensus server=node
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:30PM INF finalizing commit of block hash={} height=13 module=consensus num_txs=0 root=1A8CA1AF139CCC80EC007C6321D8A63A46A793386EE2EDF9A5CA0AB2C90728B7 server=node
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:30PM INF minted coins from module account amount=2059730459416582643aphoton from=mint module=x/bank
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:30PM INF executed block height=13 module=state num_invalid_txs=0 num_valid_txs=0 server=node
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:30PM INF commit synced commit=436F6D6D697449447B5B363520313037203630203232372039352038352032303820313334203231392032303520313433203130372031343920313431203139203139322038362031323720362031383520323533203137362031333820313735203135392031383620323334203135382031323120313431203230342037335D3A447D
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:30PM INF committed state app_hash=416B3CE35F55D086DBCD8F6B958D13C0567F06B9FDB08AAF9FBAEA9E798DCC49 height=13 module=state num_txs=0 server=node
laconic-5cd0a80c1442c3044c8b295d26426bae-laconicd-1         | 9:30PM INF indexed block exents height=13 module=txindex server=node
```

7. Confirm operation of the registry CLI:

```
laconic-so --stack fixturenet-laconic-loaded deploy exec cli "laconic cns status"
```

## Configure Digital Ocean firewall

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
laconic-so --stack fixturenet-laconic-loaded deploy exec cli ./scripts/create-demo-records.sh
```

You'll get an output like:

```
Balance is: 99998999999999998999600000
Created bond with id: dd88e8d6f9567b32b28e70552aea4419c5dd3307ebae85a284d1fe38904e301a
Published demo-record-1.yml with id: bafyreierh3xnfivexlscdwubvczmddsnf46uytyfvrbdhkjzztvsz6ruly
```

The sample record we deployed looks like:

```
TODO
```

2. Return to the laconic-console

- the published record should now be viewable
- explore it for more information
- click on the link that opens the GraphQL console
- the query is pre-loaded, click the button to run it
- inspect the output

3. Try out additional CLI commands

- these are documented [here](https://github.com/cerc-io/laconic-registry-cli#readme) and updates are forthcoming
- e.g,:

```
laconic-so --stack fixturenet-laconic-loaded deploy exec cli "laconic cns record list"
```
