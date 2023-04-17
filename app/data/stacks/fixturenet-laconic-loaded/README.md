# Laconic Fixturenet (experimental)

Testing a "Loaded" fixturenet with console.

Instructions for deploying a local Laconic blockchain "fixturenet" for development and testing purposes using laconic-stack-orchestrator.

## 1. Install Laconic Stack Orchestrator
Installation is covered in detail [here](https://github.com/cerc-io/stack-orchestrator#user-mode) but if you're on Linux and already have docker installed it should be as simple as:
```
$ mkdir my-working-dir
$ cd my-working-dir
$ curl -L -o ./laconic-so https://github.com/cerc-io/stack-orchestrator/releases/latest/download/laconic-so
$ chmod +x ./laconic-so
$ export PATH=$PATH:$(pwd)  # Or move laconic-so to ~/bin or your favorite on-path directory
```
## 2. Prepare the local build environment
Note that this step needs only to be done once on a new machine. 
Detailed instructions can be found [here](../build-support/README.md). For the impatient run these commands:
```
$ laconic-so --stack build-support build-containers --exclude cerc/builder-gerbil
$ laconic-so --stack package-registry setup-repositories
$ laconic-so --stack package-registry build-containers
$ laconic-so --stack package-registry deploy-system up
```
Then add the localhost alias `gitea.local` and set `CERC_NPM_AUTH_TOKEN` to the token printed when the package-registry stack was deployed above:
```
$ sudo vi /etc/hosts
$ export CERC_NPM_AUTH_TOKEN=<my-token>
```

## 3. Clone required repositories
```
$ laconic-so --stack fixturenet-laconicd setup-repositories
```
## 4. Build the stack's packages and containers
```
$ laconic-so --stack fixturenet-laconicd build-npms
$ laconic-so --stack fixturenet-laconicd build-containers
```
## 5. Deploy the stack
```
$ laconic-so --stack fixturenet-laconicd deploy up
```
Correct operation should be verified by checking the laconicd container's logs with:
```
$ laconic-so --stack fixturenet-laconicd deploy logs
```
## 6. Test with the Registry CLI
```
$ laconic-so --stack fixturenet-laconicd deploy exec cli "laconic cns status"
```
## 7. View the laconic console
Get the URL for the console web app with this command (the port number will be different for each deployment):
```
$ echo http://localhost:$(laconic-so --stack fixturenet-laconic-loaded deploy port laconic-console 80 | cut -d ':' -f 2)
http://localhost:58364
```
Open that address with a browser. The console should display
## 8. Load demo data into the registry
```
$ laconic-so --stack fixturenet-laconic-loaded deploy exec cli ./scripts/create-demo-records.sh
Balance is: 99998999999999998999600000
Created bond with id: dd88e8d6f9567b32b28e70552aea4419c5dd3307ebae85a284d1fe38904e301a
Published demo-record-1.yml with id: bafyreierh3xnfivexlscdwubvczmddsnf46uytyfvrbdhkjzztvsz6ruly
```
The published record should be visible in the console.
