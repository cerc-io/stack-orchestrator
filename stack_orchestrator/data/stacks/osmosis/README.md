# self-hosted osmosis

Build and deploy:
- 1) self-hosted gitea,
- 2) an ipfs node,
- 3) the osmosis front end,
- 4) a laconicd chain


```
# support image for the gitea package registry
laconic-so --stack build-support build-containers

# todo: pre-run clone

# clones and builds several things
laconic-so --stack osmosis setup-repositories
laconic-so --stack osmosis build-containers 
laconic-so --stack osmosis deploy up
```

Setup a test chain:
```
export CERC_NPM_REGISTRY_URL=https://git.vdb.to/api/packages/cerc-io/npm/

laconic-so --stack fixturenet-laconic-loaded setup-repositories --include git.vdb.to/cerc-io/laconicd,git.vdb.to/cerc-io/laconic-sdk,git.vdb.to/cerc-io/laconic-registry-cli,git.vdb.to/cerc-io/laconic-console

laconic-so --stack fixturenet-laconic-loaded build-containers

export LACONIC_HOSTED_ENDPOINT=http://<your-IP>

laconic-so --stack fixturenet-laconic-loaded deploy up
```

then `docker exec` into the `laconicd` container and either export the private key or create a new one and send funds to it. Use that private key for `LACONIC_HOTWALLET_KEY`.
