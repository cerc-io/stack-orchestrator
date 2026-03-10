# Laconicd Fixturenet

Instructions for deploying a local Laconic blockchain "fixturenet" for development and testing purposes using laconic-stack-orchestrator.

## 1. Install Laconic Stack Orchestrator
Installation is covered in detail [here](https://git.vdb.to/cerc-io/stack-orchestrator#user-mode) but if you're on Linux and already have docker installed it should be as simple as:
```
$ mkdir my-working-dir
$ cd my-working-dir
$ curl -L -o ./laconic-so https://git.vdb.to/cerc-io/stack-orchestrator/releases/download/latest/laconic-so
$ chmod +x ./laconic-so
$ export PATH=$PATH:$(pwd)  # Or move laconic-so to ~/bin or your favorite on-path directory
```
## 2. Prepare the local build environment
Note that this step needs only to be done once on a new machine.
Detailed instructions can be found [here](../build-support/README.md). For the impatient run these commands:
```
$ laconic-so --stack build-support build-containers --exclude cerc/builder-gerbil
$ laconic-so --stack package-registry setup-repositories
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
$ laconic-so --stack fixturenet-laconicd deploy exec cli "laconic registry status"
```
