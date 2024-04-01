# linea-testnet-nitro-auth

Deployes a demo stack for Nitro-based auth using the Linea Sepolia testnet.

## Clone required repositories

```
$ laconic-so --stack linea-testnet-nitro-auth setup-repositories
```

## Build containers

```
$ laconic-so --stack linea-testnet-nitro-auth build-containers
```

## Create a deployment

```
$ laconic-so --stack linea-testnet-nitro-auth deploy init --map-ports-to-host any-same --output linea-testnet-nitro-auth-spec.yml
$ laconic-so --stack linea-testnet-nitro-auth deploy create --spec-file linea-testnet-nitro-auth-spec.yml --deployment-dir linea-testnet-nitro-auth-deployment
```

## Set your keys

You must set the private keys for two accounts with funds on the target network.  You must also set the URL to use
for a WebSocket connection, eg, `wss://linea-sepolia.infura.io/ws/v3/<MY_API_KEY>`

```
# For the first account (payer).
$ vim linea-testnet-nitro-auth-deployment/config/alice.env

CERC_NITRO_CHAIN_PK=<MY_PRIVATE_KEY>
CERC_NITRO_CHAIN_URL=wss://linea-sepolia.infura.io/ws/v3/<MY_API_KEY>

# For the second account (payee).
$ vim linea-testnet-nitro-auth-deployment/config/bob.env

CERC_NITRO_CHAIN_PK=<MY_PRIVATE_KEY>
CERC_NITRO_CHAIN_URL=wss://linea-sepolia.infura.io/ws/v3/<MY_API_KEY>

# For the bootnode, just set the URL.
$ vim linea-testnet-nitro-auth-deployment/config/bootnode.env

CERC_NITRO_CHAIN_URL=wss://linea-sepolia.infura.io/ws/v3/<MY_API_KEY>
```

## Start the stack
```
$ laconic-so deployment --dir linea-testnet-nitro-auth-deployment start
```

## Open the webapp

Visit http://localhost:5678
