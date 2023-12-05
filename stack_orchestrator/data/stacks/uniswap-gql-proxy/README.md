# Uniswap GQL Proxy

Instructions to setup and deploy a Uniswap GQL proxy server

## Setup

Clone required repository:

```bash
laconic-so --stack uniswap-gql-proxy setup-repositories --pull

# If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the repositories mentioned below and re-run the command
```

Build the container image:

```bash
laconic-so --stack uniswap-gql-proxy build-containers
```

## Create a deployment

First, create a spec file for the deployment, which will allow mapping the stack's ports and volumes to the host:

```bash
laconic-so --stack uniswap-gql-proxy deploy init --output uniswap-gql-proxy-spec.yml
```

Edit `network` in spec file to map container ports to same ports in host:

```
...
network:
  ports:
    uniswap-gql-proxy:
      - '4000:4000'
...
```

Once you've made any needed changes to the spec file, create a deployment from it:

```bash
laconic-so --stack uniswap-gql-proxy deploy create --spec-file uniswap-gql-proxy-spec.yml --deployment-dir uniswap-gql-proxy-deployment
```

## Start the stack

Start the deployment:

```bash
laconic-so deployment --dir uniswap-gql-proxy-deployment start
```

* List and check the health status of the container using `docker ps`

* The Uniswap GQL server will now be listening at http://localhost:4000

## Clean up

To stop the service running in background:

```bash
laconic-so deployment --dir uniswap-gql-proxy-deployment stop
```
