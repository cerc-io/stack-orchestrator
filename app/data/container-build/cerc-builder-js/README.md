## JS/TS Package Builder

This container is designed to be used as a simple "build runner" environment for building and publishing JS/TS projects
using `yarn`.

### Running a build

As a temporary measure while the necessary functionality is being added to Stack Orchestrator,
it is possible to build packages manually by invoking `docker run` , for example as follows:


```
$ docker run --rm -it --add-host gitea.local:host-gateway \
  -v ${HOME}/cerc/laconic-registry-cli:/workspace cerc/builder-js  \
  sh -c 'cd /workspace && CERC_NPM_AUTH_TOKEN=6613572a28ebebaee20ccd90064251fa8c2b94f6 \
  build-npm-package-local-dependencies.sh http://gitea.local:3000/api/packages/cerc-io/npm/ 0.1.8'
```
