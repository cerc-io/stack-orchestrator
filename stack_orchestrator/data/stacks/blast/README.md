# Blast stack

## Clone required repositories
```
$ laconic-so --stack blast setup-repositories
```
## Build the stack's containers
```
$ laconic-so --stack blast build-containers
```
## Create a deployment of the stack
```
$ laconic-so --stack blast deploy init --map-ports-to-host any-same --output blast-spec.yml
```
[Insert details on how to configure the stack]
```
$ laconic-so --stack blast deploy create --deployment-dir blast-deployment --spec-file blast-spec.yml
```
## Start the stack
```
$ laconic-so deployment --dir blast-deployment start
```
Check logs:
```
$ laconic-so deployment --dir blast-deployment logs
```
