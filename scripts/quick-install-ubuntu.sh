#!/bin/bash
set -euo pipefail  ## https://vaneyckt.io/posts/safer_bash_scripts_with_set_euxo_pipefail/

# WARNING: read this script in detail and understand what it does, prior to running it blindly 
# This script assumes root permissions on a fresh Ubuntu Digital Ocean droplet
# with these recommended specs: 16 GB Memory / 8 Intel vCPUs / 320 GB Disk

# dismiss the popups
export DEBIAN_FRONTEND=noninteractive 

apt update -y && apt upgrade -y

apt install docker.io jq -y

## need to do this for Linux <-> docker compose when not installed with Docker Desktop
mkdir -p ~/.docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.11.2/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose

# install latest `laconic-so`
mkdir -p  ~/bin
curl -L -o ~/bin/laconic-so https://github.com/cerc-io/stack-orchestrator/releases/latest/download/laconic-so
chmod +x ~/bin/laconic-so

# set here for this script
PATH=$PATH:~/bin

# added to profile, manually running `source ~/.profile` is then required
echo "export PATH=$PATH:~/bin" >> ~/.profile

# TODO: run this manually again after the script ends
# source ~/.profile

# verify operation
laconic-so version
