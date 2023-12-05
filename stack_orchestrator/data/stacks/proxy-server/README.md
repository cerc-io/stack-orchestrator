# Proxy Server

Instructions to setup and deploy a HTTP proxy server

## Setup

Clone required repository:

```bash
laconic-so --stack proxy-server setup-repositories --pull

# If this throws an error as a result of being already checked out to a branch/tag in a repo, remove the repositories mentioned below and re-run the command
```

Build the container image:

```bash
laconic-so --stack proxy-server build-containers
```

## Create a deployment

* First, create a spec file for the deployment, which will allow mapping the stack's ports and volumes to the host:

  ```bash
  laconic-so --stack proxy-server deploy init --output proxy-server-spec.yml
  ```

* Edit `network` in spec file to map container ports to same ports in host:

  ```yml
  ...
  network:
    ports:
      proxy-server:
        - '4000:4000'
  ...
  ```

* Once you've made any needed changes to the spec file, create a deployment from it:

  ```bash
  laconic-so --stack proxy-server deploy create --spec-file proxy-server-spec.yml --deployment-dir proxy-server-deployment
  ```

* Inside the deployment directory, open the file `config.env` and set the following env variables:

  ```bash
  # Upstream endpoint
  CERC_PROXY_UPSTREAM=

  # Origin header to be used (Optional)
  CERC_PROXY_ORIGIN_HEADER=
  ```

## Start the stack

Start the deployment:

```bash
laconic-so deployment --dir proxy-server-deployment start
```

* List and check the health status of the container using `docker ps`

* The proxy server will now be listening at http://localhost:4000

## Clean up

To stop the service running in background:

```bash
laconic-so deployment --dir proxy-server-deployment stop
```
