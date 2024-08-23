# Package Registry Stack

The Package Registry Stack supports a build environment that requires a package registry (initially for NPM packages only).

## Setup

* Setup required repos and build containers:

  ```bash
  laconic-so --stack package-registry setup-repositories
  laconic-so --stack package-registry build-containers
  ```

* Create a deployment:

  ```bash
  laconic-so --stack package-registry deploy init --output package-registry-spec.yml
  # Update port mapping in the laconic-loaded.spec file to resolve port conflicts on host if any

  laconic-so --stack package-registry deploy create --deployment-dir package-registry-deployment --spec-file package-registry-spec.yml
  ```

* Start the deployment:

  ```bash
  laconic-so deployment --dir package-registry-deployment start
  ```

* The local gitea registry can now be accessed at <http://localhost:3000> (the username and password can be taken from the deployment logs)
