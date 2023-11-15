### Building and Running Webapps

It is possible to build and run webapps using the `build-webapp` and `run-webapp` subcommand.

To make it easier to build once, and deploy to with varying configuration, compilation and static
page generation are separated in the `build-webapp` and `run-webapp` steps, and the use of the
environment variables via `process.env` is detected at compile-time and placeholder substituted
which will be filled in at runtime.

This offers much more flexibilty in configuration and deployment than standard build methods.

## Build

```
$ cd ~/cerc
$ git clone git@git.vdb.to:cerc-io/test-progressive-web-app.git
$ laconic-so build-webapp --source-repo ~/cerc/test-progressive-web-app
...
Successfully tagged cerc/test-progressive-web-app:local


#################################################################

Built host container for ~/cerc/test-progressive-web-app with tag:

    cerc/test-progressive-web-app:local

To test locally run:

    laconic-so run-webapp --image cerc/test-progressive-web-app:local --env-file /path/to/environment.env

```

## Run

```
$ laconic-so run-webapp --image cerc/test-progressive-web-app:local --env-file ~/tmp/env.igloo

Image: cerc/test-progressive-web-app:local
ID: 4c6e893bf436b3e91a2b92ce37e30e499685131705700bd92a90d2eb14eefd05
URL: http://localhost:32768
```
