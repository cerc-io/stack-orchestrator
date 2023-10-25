# keycloak

Deploys a stand alone [keycloak](https://www.keycloak.org)

## Clone required repositories

```
$ laconic-so --stack keycloak setup-repositories
```

## Build containers

```
$ laconic-so --stack keycloak build-containers
```

## Create a deployment

```
$ laconic-so --stack keycloak deploy init --map-ports-to-host any-same --outputkeycloak-spec.yml
$ laconic-so deploy create --spec-file keycloak-spec.yml --deployment-dir keycloak-deployment
```
## Start the stack
```
$ laconic-so deployment --dir keycloak-deployment start
```
Display stack status:
```
$ laconic-so deployment --dir keycloak-deployment ps
Running containers:

```
See stack logs:
```
$ laconic-so deployment --dir keycloak-deployment logs

```
