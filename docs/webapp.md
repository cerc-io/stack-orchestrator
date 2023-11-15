### Building and Running Webapps

It is possible to build and run Next.js webapps using the `build-webapp` and `run-webapp` subcommands.

To make it easier to build once and deploy into different environments and with different configuration,
compilation and static page generation are separated in the `build-webapp` and `run-webapp` steps.

This offers much more flexibilty than standard Next.js build methods, since any environment variables accessed
via `process.env`, whether for pages or for API, will have values drawn from their runtime deployment environment,
not their build environment. 

## Building

```
$ cd ~/cerc
$ git clone git@git.vdb.to:cerc-io/test-progressive-web-app.git
$ laconic-so build-webapp --source-repo ~/cerc/test-progressive-web-app
...

Built host container for ~/cerc/test-progressive-web-app with tag:

    cerc/test-progressive-web-app:local

To test locally run:

    laconic-so run-webapp --image cerc/test-progressive-web-app:local --env-file /path/to/environment.env

```

## Running

```
$ laconic-so run-webapp --image cerc/test-progressive-web-app:local --env-file ~/tmp/env.igloo

Image: cerc/test-progressive-web-app:local
ID: 4c6e893bf436b3e91a2b92ce37e30e499685131705700bd92a90d2eb14eefd05
URL: http://localhost:32768
```
