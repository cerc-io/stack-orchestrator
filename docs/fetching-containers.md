# Fetching pre-built container images
When Stack Orchestrator deploys a stack containing a suite of one or more containers it expects images for those containers to be on the local machine with a tag of the form `<image-name>:local` Images for these containers can be built from source (and optionally base container images from public registries) with the `build-containers` subcommand. 

However, the task of building a large number of containers from source may consume considerable time and machine resources. This is where the `fetch-containers` subcommand steps in. It is designed to work exactly like `build-containers` but instead the images, pre-built, are fetched from an image registry then re-tagged for deployment. It can be used in place of `build-containers` for any stack provided the necessary containers, built for the local machine architecture (e.g. arm64 or x86-64) have already been published in an image registry.
## Usage
To use `fetch-containers`, provide an image registry path, a username and token/password with read access to the registry, and optionally specify `--force-local-overwrite`. If this argument is not specified, if there is already a locally built or previously fetched image for a stack container on the machine, it will not be overwritten and a warning issued.
```
$ laconic-so --stack mobymask-v3-demo fetch-containers --image-registry git.vdb.to/cerc-io --registry-username <registry-user> --registry-token <registry-token> --force-local-overwrite
```