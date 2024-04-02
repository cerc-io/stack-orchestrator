# go-nitro-auth

Deploy a stack for demoing Nitro-based auth, using either a local fixturenet (fully self-contained) or remote testnet.

## Local Fixturenet (Self-Contained)

### Clone required repositories

```
$ laconic-so --stack fixturenet-eth setup-repositories
$ laconic-so --stack go-nitro-auth setup-repositories
```

### Build containers

```
$ laconic-so --stack fixturenet-eth build-containers
$ laconic-so --stack go-nitro-auth build-containers
```

### Create a deployment

```
$ laconic-so --stack fixturenet-eth deploy init --output nitro-net.yml
$ laconic-so --stack fixturenet-eth deploy create --spec-file nitro-net.yml --deployment-dir /srv/nitro-net

$ laconic-so --stack go-nitro-auth deploy init --map-ports-to-host any-same --output nitro-auth.yml
$ laconic-so --stack go-nitro-auth deploy create --spec-file nitro-auth.yml --deployment-dir /srv/nitro-auth

# Place them both in the same namespace (TODO: support setting the deployment name via --cluster).
$ cp /srv/nitro-net/deployment.yml /srv/nitro-auth/deployment.yml
```

### Start the containers

```
$ laconic-so deployment --dir /srv/nitro-net up
$ laconic-so deployment --dir /srv/nitro-auth up
```

### Open the webapp

Visit http://localhost:5678

## Remote Testnet

This example will use the Linea Sepolia testnet.

### Clone required repositories

```
$ laconic-so --stack go-nitro-auth setup-repositories
```

### Build containers

```
$ laconic-so --stack go-nitro-auth build-containers
```

### Create a deployment

```
$ laconic-so --stack go-nitro-auth deploy init --map-ports-to-host any-same --output nitro-auth.yml
$ laconic-so --stack go-nitro-auth deploy create --spec-file nitro-auth.yml --deployment-dir /srv/nitro-auth
```

### Set your keys, contract addresses, etc.

You must set the private keys for two accounts with funds on the target network, as well as the contract addresses
(if they already exist) or else an account to create them.  You must also set the URL to use for WebSocket connections,
eg, `wss://linea-sepolia.infura.io/ws/v3/<MY_API_KEY>`

#### Config

```
$ vim /srv/nitro-auth/config.env
# Addresses of existing contracts.
CERC_CA_ADDRESS="0x1Ae815c3e7556e16ceaB6B6d46306C1870EB6d24"
CERC_NA_ADDRESS="0xc453C5E3f304bb545A3Df7bBa02fe6274A056636"
CERC_VPA_ADDRESS="0xA11af80D75b1150631FA78178c94fa451c7172a8"

# Else the private key of an account and RPC URL to use create them.
CERC_PRIVATE_KEY_DEPLOYER=<PRIV_KEY_HERE>
CERC_ETH_RPC_ENDPOINT=https://rpc.sepolia.linea.build

# The WebSocket chain URL.
CERC_NITRO_CHAIN_URL=wss://linea-sepolia.infura.io/ws/v3/<MY_API_KEY_HERE>

# Private key for "Alice" account (payer)
CERC_NITRO_CHAIN_PK_ALICE=<ALICE_PRIVATE_KEY_HERE>

# Private key for "Bob" account (payee)
CERC_NITRO_CHAIN_PK_BOB=<BOB_PRIVATE_KEY_HERE>
```

### Start the stack
```
$ laconic-so deployment --dir /srv/nitro-auth up
```

### Open the webapp

Visit http://localhost:5678
