# Release Process

## Manually publish to github releases

In order to build, the shiv and wheel packages must be installed:
```
$ pip install shiv
$ pip install wheel
```

Then:

1. Define `CERC_GH_RELEASE_SCRIPTS_DIR`
1. Define `CERC_PACKAGE_RELEASE_GITHUB_TOKEN`
1. Run `./scripts/tag_new_release.sh <major> <minor> <patch>`
1. Run `./scripts/build_shiv_package.sh`
1. Run `./scripts/publish_shiv_package_github.sh <major> <minor> <patch>`
1. Commit the new version file.

e.g.

```
$ export CERC_GH_RELEASE_SCRIPTS_DIR=~/projects/cerc/github-release-api/
$ export CERC_PACKAGE_RELEASE_GITHUB_TOKEN=github_pat_xxxxxx
$ ./scripts/tag_new_release.sh 1 0 17
$ ./scripts/build_shiv_package.sh
$ ./scripts/publish_shiv_package_github.sh 1 0 17
```

