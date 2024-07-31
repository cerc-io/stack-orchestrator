# Gitea x NPMs X Laconicd

Deploy a local Gitea server, publish NPM packages to it, then use those packages to build a Laconicd fixturenet. Demonstrates several components of the Laconic stack

### Build and Deploy Gitea

```bash
laconic-so --stack build-support build-containers
laconic-so --stack package-registry setup-repositories
laconic-so --stack package-registry build-containers 
laconic-so --stack package-registry deploy up
```

These commands can take awhile. Eventually, some instructions and a token will output. Set `CERC_NPM_AUTH_TOKEN`:

```bash
export CERC_NPM_AUTH_TOKEN=<your-token>
```

### Configure the hostname gitea.local

How to do this depends on your operating system  but usually involves editing a `hosts` file. For example, on Linux add this line to the file `/etc/hosts` (needs sudo):

```bash
127.0.0.1       gitea.local
```

Test with:

```bash
ping gitea.local
```

```bash
PING gitea.local (127.0.0.1) 56(84) bytes of data.
64 bytes from localhost (127.0.0.1): icmp_seq=1 ttl=64 time=0.147 ms
64 bytes from localhost (127.0.0.1): icmp_seq=2 ttl=64 time=0.033 ms
```

Although not necessary in order to build and publish packages, you can now access the Gitea web interface at: [http://gitea.local:3000](http://gitea.local:3000) using these credentials: `gitea_admin/admin1234` (Note: please properly secure Gitea if public internet access is allowed).

### Build npm Packages

Clone the required repositories:

```bash
laconic-so --stack fixturenet-laconicd setup-repositories
```

Build and publish the npm packages:

```bash
laconic-so --stack fixturenet-laconicd build-npms
```

Navigate to the Gitea console and switch to the `cerc-io` user then find the `Packages` tab to confirm that these two npm packages have been published:

- `@cerc-io/laconic-registry-cli`
- `@cerc-io/registry-sdk`

### Build and deploy fixturenet containers

```bash
laconic-so --stack fixturenet-laconicd build-containers
laconic-so --stack fixturenet-laconicd deploy up
```

Check the logs:

```bash
laconic-so --stack fixturenet-laconicd deploy logs
```

### Test with the registry CLI

```bash
laconic-so --stack fixturenet-laconicd deploy exec cli "laconic registry status"
```

Try additional CLI commands, documented [here](https://github.com/cerc-io/laconic-registry-cli#operations).
