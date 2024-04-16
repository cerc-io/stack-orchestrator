# Lotus stack

## Clone required repositories
```
$ laconic-so --stack mainnet-lotus setup-repositories
```
## Build the stack's containers
```
$ laconic-so --stack mainnet-lotus build-containers
```
## Create a deployment of the stack
```
$ laconic-so --stack mainnet-lotus deploy init --map-ports-to-host any-same --output lotus-spec.yml
```
Update the URLs in the generated spec file to use your systems' actual IP addresses.
```
$ laconic-so --stack mainnet-lotus deploy create --deployment-dir lotus-deployment --spec-file lotus-spec.yml
```
## Start the stack
```
$ laconic-so deployment --dir lotus-deployment start
```
Check logs:
```
$ laconic-so deployment --dir lotus-deployment logs
```
