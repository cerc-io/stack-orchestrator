# Build Support Stack

## Instructions

JS/TS/NPM builds need an npm registry to store intermediate package artifacts.
This can be supplied by the user (e.g. using a hosted registry or even npmjs.com), or a local registry using gitea can be deployed by stack orchestrator.
To use a user-supplied registry set these environment variables:

`CERC_NPM_REGISTRY_URL` and 
`CERC_NPM_AUTH_TOKEN`

Leave `CERC_NPM_REGISTRY_URL` un-set to use the local gitea registry.

### Build support containers
```
$ laconic-so --stack build-support build-containers
```
### Deploy Gitea Package Registry

```
$ laconic-so --stack package-registry setup-repositories
$ laconic-so --stack package-registry deploy-system up
This is your gitea access token: 84fe66a73698bf11edbdccd0a338236b7d1d5c45. Keep it safe and secure, it can not be fetched again from gitea.
$ export CERC_NPM_AUTH_TOKEN=84fe66a73698bf11edbdccd0a338236b7d1d5c45
```
Now npm packages can be built:
### Build npm Packages
```
$ laconic-so build-npms --include laconic-sdk
```
