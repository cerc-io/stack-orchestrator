## Building JS/TS Packages

As a temporary measure while the necessary functionality is being added to Stack Orchestrator,
it is possible to build packages manually by invoking `docker run` , for example as follows:

```
docker run -it --add-host host.docker.internal:host-gateway \
  -v ${HOME}/cerc/laconic-sdk:/workspace cerc/builder-js \
  sh -c 'cd /workspace && NPM_AUTH_TOKEN=6613572a28ebebaee20ccd90064251fa8c2b94f6 \
  /build-npm-package.sh http://host.docker.internal:3000/api/packages/cerc-io/npm/ 1.2.3-test'
```