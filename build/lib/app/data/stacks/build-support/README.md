# Build Support Stack

## Instructions

JS/TS/NPM builds need an npm registry to store intermediate package artifacts.
This can be supplied by the user (e.g. using a hosted registry or even npmjs.com), or a local registry using gitea can be deployed by stack orchestrator.
To use a user-supplied registry set these environment variables:

`CERC_NPM_REGISTRY_URL` and 
`CERC_NPM_AUTH_TOKEN`

Leave `CERC_NPM_REGISTRY_URL` un-set to use the local gitea registry.

### 1. Build support containers

Note: the scheme/gerbil container is excluded as it isn't currently required for the package registry.

```
$ laconic-so --stack build-support build-containers --exclude cerc/builder-gerbil
```
### 2. Deploy Gitea Package Registry

```
$ laconic-so --stack package-registry setup-repositories
$ laconic-so --stack package-registry build-containers 
$ laconic-so --stack package-registry deploy up
[+] Running 3/3
 ⠿ Network laconic-aecc4a21d3a502b14522db97d427e850_gitea       Created                                                                                    0.0s
 ⠿ Container laconic-aecc4a21d3a502b14522db97d427e850-db-1      Started                                                                                    1.2s
 ⠿ Container laconic-aecc4a21d3a502b14522db97d427e850-server-1  Started                                                                                    1.9s
New user 'gitea_admin' has been successfully created!
This is your gitea access token: 84fe66a73698bf11edbdccd0a338236b7d1d5c45. Keep it safe and secure, it can not be fetched again from gitea.
To use with laconic-so set this environment variable: export CERC_NPM_AUTH_TOKEN=3e493e77b3e83fe9e882f7e3a79dd4d5441c308b
Created the organization cerc-io
Gitea was configured to use host name: gitea.local, ensure that this resolves to localhost, e.g. with sudo vi /etc/hosts
Success, gitea is properly initialized
$
```

Note: the above commands can take several minutes depending on the specs of your machine.

### 3. Configure the hostname gitea.local
How to do this is OS-dependent but usually involves editing a `hosts` file. For example on Linux add this line to the file `/etc/hosts` (needs sudo):
```
127.0.0.1       gitea.local
```
Test with:
```
$ ping gitea.local
PING gitea.local (127.0.0.1) 56(84) bytes of data.
64 bytes from localhost (127.0.0.1): icmp_seq=1 ttl=64 time=0.147 ms
64 bytes from localhost (127.0.0.1): icmp_seq=2 ttl=64 time=0.033 ms
```
Although not necessary in order to build and publish packages, you can now access the Gitea web interface at: [http://gitea.local:3000](http://gitea.local:3000) using these credentials: gitea_admin/admin1234 (Note: please properly secure Gitea if public internet access is allowed).

Now npm packages can be built:
### Build npm Packages
Ensure that `CERC_NPM_AUTH_TOKEN` is set with the token printed above when the package-registry stack was deployed (the actual token value will be different than shown in this example):
```
$ export CERC_NPM_AUTH_TOKEN=84fe66a73698bf11edbdccd0a338236b7d1d5c45
$ laconic-so build-npms --include laconic-sdk,laconic-registry-cli
```
