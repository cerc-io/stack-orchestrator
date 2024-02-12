# mars

On a fresh Digital Ocean droplet with Ubuntu:

```
git clone https://github.com/cerc-io/stack-orchestrator
cd stack-orchestrator
./scripts/quick-install-linux.sh
```
Read and follow the instructions output from the above output to complete installation, then:

```
laconic-so --stack mars setup-repositories
laconic-so --stack mars build-containers
laconic-so --stack mars deploy up
```
