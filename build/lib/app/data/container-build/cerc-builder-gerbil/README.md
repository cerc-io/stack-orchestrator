## Gerbil Scheme Builder

This container is designed to be used as a simple "build runner" environment for building and running Scheme projects using Gerbil and gerbil-ethereum. Its primary purpose is to allow build/test/run of gerbil code without the need to install and configure all the necessary prerequisites and dependencies on the host system.

### Usage

First build the container with:

```
$ laconic-so build-containers --include cerc/builder-gerbil
```

Now, assuming a gerbil project located at `~/projects/my-project`, run bash in the container mounting the project with:

```
$ docker run -it -v $HOME/projects/my-project:/src cerc/builder-gerbil:latest bash
root@7c4124bb09e3:/src#
```

Now gerbil commands can be run.

