# Deploying WebApps from the Laconic Registry to Kubernetes

First, ensure you have `laconicd` and the console running via [this tutorial](./laconicd-with-console.md).

## Setup Kubernetes

If merely requesting deployment, access to the Laconic registry is sufficient, but to *process* deployment requests, Kubernetes configuration is also necessary. The configuration format is the same as used by `kubectl`, and should be places in `/etc/config/kube.yml`

## Setup the Deployer

### Set envs


```
$DEPLOYMENT_DNS_SUFFIX
$DEPLOYMENT_RECORD_NAMESPACE
$IMAGE_REGISTRY
$IMAGE_REGISTRY_CREDS
$IMAGE_REGISTRY_USER

```


```
laconic-so --stack webapp-deployer-backend setup-repositories
laconic-so --stack webapp-deployer-backend build-containers
laconic-so --stack webapp-deployer-backend deploy up
```

## Setup Your Account

Writing to the Laconic Registry, in order to create records for applications and deployment requests, requires a user key, and a bond with adequate funds available.

### Install the registry CLI

```
npm config set @cerc-io:registry https://git.vdb.to/api/packages/cerc-io/npm/
npm install -g @cerc-io/laconic-registry-cli
```

Alternatively, use the pre-configured container that was setup alongside `laconicd`

### Get your private key

```
exec into laconicd
```

### config.yml

```
services:
  cns:
    restEndpoint: http://console.laconic.com:1317
    gqlEndpoint: http://console.laconic.com:9473/api
    userKey: 3d4789e88508c6230d973ccea283032d3e3948775dbe02f4f0a80dc6c1f7c8d5
   # bondId: 3c61577f3c6197ced599e2fc21ccf76f43373004fd29c29f2e560c77f7c4bb6d
    chainId: laconic_9000-1
    gas: 550000
    fees: 200000aphoton
```

### Create a bond

```
laconic cns -c config.yml bond create --type aphoton --quantity 1000000000 --gas 200000 --fees 200000aphoton
```





# Creating Deployments

Deploying an application from the registry requires (and generates)
several records:

1. An `ApplicationRecord` which describes the application itself, including its name, version, and repository.
2. An `ApplicationDeploymentRequest` which references an`ApplicationRecord`, and provides additional information such as the DNS name and configuration.
3. A `DnsRecord`, which contains the FQDN of the deployment. The ownership of this record will be checked against any future deployment or removal requests.
4. An `ApplicationDeploymentRecord` which records the successful processing of the deployment request.

Additionally, since names need to be registered, namespace authorities need to be reserved, for example:

```
$ laconic -c $LACONIC_CONFIG cns authority reserve my-org-name

$ laconic -c $LACONIC_CONFIG cns authority bond set my-org-name 0e9176d854bc3c20528b6361aab632f0b252a0f69717bf035fa68d1ef7647ba7
```

## Application Records

The `ApplicationRecord` should, at a minimum, specify the name of the application (`name`), its version (`app_version`), type (`app_type`), one or more repository URLs (`repository`), and the repository reference (eg, branch, tag, hash, etc.) to use (`repository_ref`).

```
$ cat app.yml
record:
  type: ApplicationRecord
  version: 0.0.4
  name: "@my-org-name/my-test-webapp"
  repository:
    - "https://github.com/my-org-name/my-test-webapp"
  repository_ref: "v0.1.5"
  app_version: "0.1.5"
  app_type: "webapp"

$ laconic -c $LACONIC_CONFIG cns record publish -f app.yml
bafyreihwvu6ynmk4nfrxg2vdcx2ep3tqry775ksqyehjitj2i4kphhyuky
```

One or more names should be registered for the application, which deployment requests can reference.

```
$ laconic -c $LACONIC_CONFIG cns name set "crn://my-org-name/applications/my-test-webapp" bafyreihwvu6ynmk4nfrxg2vdcx2ep3tqry775ksqyehjitj2i4kphhyuky

$ laconic -c $LACONIC_CONFIG cns name set "crn://my-org-name/applications/my-test-webapp@0.1.5" bafyreihwvu6ynmk4nfrxg2vdcx2ep3tqry775ksqyehjitj2i4kphhyuky

$ laconic -c $LACONIC_CONFIG cns record get --id bafyreihwvu6ynmk4nfrxg2vdcx2ep3tqry775ksqyehjitj2i4kphhyuky
[
  {
    "id": "bafyreihwvu6ynmk4nfrxg2vdcx2ep3tqry775ksqyehjitj2i4kphhyuky",
    "names": [
      "crn://my-org-name/applications/my-test-webapp",
      "crn://my-org-name/applications/my-test-webapp@0.1.5",
    ],
    "owners": [
      "2671D38525BDC91A5DF4794EF2059D5771133702"
    ],
    "bondId": "0e9176d854bc3c20528b6361aab632f0b252a0f69717bf035fa68d1ef7647ba7",
    "createTime": "2024-01-12T20:30:33Z",
    "expiryTime": "2025-01-11T20:30:33Z",
    "attributes": {
      "app_type": "webapp",
      "app_version": "0.1.5",
      "name": "@my-org-name/my-test-webapp",
      "repository": [
        "https://github.com/my-org-name/my-test-webapp"
      ],
      "repository_ref": "v0.1.5",
      "type": "ApplicationRecord",
      "version": "0.0.4"
    }
  }
]
```

## Application Deployment Requests

To create the deployment of specific application, and `ApplicationDeploymentRequest` must be published. This request must reference the application to be deployed (`application`) and may optionally provide configuration (`config`) and a DNS name (`dns`). If no DNS name is supplied, one will be generated. A supplied DNS is usually just the short hostname, not the FQDN, since the suffix is supplied by the deployer.

```
$ cat req.yml
record:
  type: ApplicationDeploymentRequest
  version: 1.0.0
  name: "my-org-name/my-test-webapp@0.1.5"
  application: "crn://my-org-name/applications/my-test-webapp@0.1.5"
  dns: "my-test-app"
  config:
    env:
      CERC_WEBAPP_DEBUG: my_debug_value_here

$ laconic -c $LACONIC_CONFIG cns record publish -f req.yml
bafyreihtpvwjka5ecjmca46y4dip5gb2h25vvmc7t27d7g4zecngjssvky
```

It is not necessary to assign a name to the request.

## Building and Deploying

Building and deploying will happen automatically for records published the production registry, but in other environments it can be triggered manually.

Laconic `stack-orchestrator` is used build and launch the application. It will clone the repository, build the application, upload the container to a registry, and launch the instance in Kubernetes, with
automatic DNS and TLS provisioning.

```
$ laconic-so deploy-webapp-from-registry \
    --kube-config $KUBE_CONFIG \
    --image-registry registry.mydeployer.org/app-registry \
    --deployment-parent-dir /opt/deployments \
    --laconic-config $LACONIC_CONFIG \
    --dns-suffix mydeployer.servesthe.world \
    --record-namespace-dns crn://my-deployer-org/dns \
    --record-namespace-deployments crn://my-deployer-org/deployments \
    --request-id bafyreihtpvwjka5ecjmca46y4dip5gb2h25vvmc7t27d7g4zecngjssvky
```

When deployment is complete, an `ApplicationDeploymentRecord` will be created:

```
$ laconic -c $LACONIC_CONFIG cns name resolve crn://my-deployer-org/deployments/my-test-app.mydeployer.servesthe.world
[
  {
    "id": "bafyreiemfmxsue4svzys6tcwsqmhfjeyoo3gp63n7kydi2izbrwuzd4rga",
    "names": [
      "crn://my-deployer-org/deployments/my-test-app.laconic.servesthe.world"
    ],
    "owners": [
      "2671D38525BDC91A5DF4794EF2059D5771133702"
    ],
    "bondId": "0e9176d854bc3c20528b6361aab632f0b252a0f69717bf035fa68d1ef7647ba7",
    "createTime": "2024-01-11T20:45:29Z",
    "expiryTime": "2025-01-10T20:45:29Z",
    "attributes": {
      "application": "bafyreibs6y7jhgjlsoxyqlugvkweanp3bi7ippfmhehk2rslcpoaqic2xi",
      "dns": "bafyreicpac7tar5ua5e42zo7d5zwyp5yv7iord23p3gdox7zdfslrarjle",
      "meta": {
        "config": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
        "so": "82a5f9a3e4924cbb92e28be68759a487"
      },
      "name": "@cerc-io/my-test-webapp",
      "request": "bafyreiex7vmtruiiasra4wvqe7wirl6iuwiso6p3cvb3sjhq55e74zh4ke",
      "type": "ApplicationDeploymentRecord",
      "url": "https://my-test-app.mydeployer.servesthe.world",
      "version": "0.0.1"
    }
  }
]
```

## Checking Status

The status of the deployment may be checked with `stack-orchestrator`.

```
$ laconic-so deployment --dir /opt/deployments/my-test-app.snowball.servesthe.world status
Ingress:
        Hostname: my-test-app.mydeployer.servesthe.world
        IP: 204.130.133.199
        TLS: notBefore: 2024-01-12T23:11:09Z, notAfter: 2024-04-11T23:11:08Z

Pods:
        default/laconic-9560ffc64512e453-deployment-fb58d756f-l77pm: Running (2024-01-13 00:10:42+00:00)
```

# Removing Deployments

As with deployment, removal involves publishing a request, which is then fulfilled by deployment processor.

## Application Deployment Removal Requests

```
$ cat apprm.yml
record:
  type: ApplicationDeploymentRemovalRequest
  version: 1.0.0
  deployment: bafyreiemfmxsue4svzys6tcwsqmhfjeyoo3gp63n7kydi2izbrwuzd4rga

$ laconic -c $LACONIC_CONFIG cns record publish -f apprm.yml
bafyreiejnqhsn5ibc3c6pzlsc26co3mt63djdeuntt3gmfuckcntdmisge
```

## Removal

As with deployment, for records publish to the production service removal should be processed automatically. In other environments, removal can be processed with `stack-orchestrator`.

```
$ laconic-so undeploy-webapp-from-registry   \
    --deployment-parent-dir /opt/deployments   \
    --laconic-config ~/.laconic/local.yml   \
    --request-id bafyreiejnqhsn5ibc3c6pzlsc26co3mt63djdeuntt3gmfuckcntdmisge

Request bafyreiejnqhsn5ibc3c6pzlsc26co3mt63djdeuntt3gmfuckcntdmisge needs to processed.
Found 1 unsatisfied request(s) to process.
Matched deployment ownership: 2671D38525BDC91A5DF4794EF2059D5771133702
record:
  type: ApplicationDeploymentRemovalRecord
  deployment: bafyreiemfmxsue4svzys6tcwsqmhfjeyoo3gp63n7kydi2izbrwuzd4rga
  request: bafyreiejnqhsn5ibc3c6pzlsc26co3mt63djdeuntt3gmfuckcntdmisge
  version: 1.0.0
```
