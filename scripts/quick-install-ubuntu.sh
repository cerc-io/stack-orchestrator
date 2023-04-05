#!/usr/bin/env bash
set -euo pipefail  ## https://vaneyckt.io/posts/safer_bash_scripts_with_set_euxo_pipefail/

install_dir=~/bin

# This script assumes root permissions on a fresh Ubuntu Digital Ocean droplet
# with these recommended specs: 16 GB Memory / 8 Intel vCPUs / 320 GB Disk

# dismiss the popups
export DEBIAN_FRONTEND=noninteractive

## https://docs.docker.com/engine/install/ubuntu/
sudo apt -y remove docker docker-engine docker.io containerd runc
sudo apt -y update -y && apt -y upgrade

# laconic-so depends on jq
sudo apt -y install jq
# laconic-so depends on git
sudo apt -y install git
# curl used below
sudo apt -y install jq
# docker repo add depends on gnupg and updated ca-certificates
sudo apt -y install ca-certificates gnupg

# Add dockerco package repository
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Penny in the update jar
sudo apt -y update

# Install docker
sudo apt -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow the current user to use Docker
sudo groupadd docker
sudo usermod -aG docker $USER

# install latest `laconic-so`
install_filename=${install_dir}/laconic-so
mkdir -p  ${install_dir}
curl -L -o ${install_filename} https://github.com/cerc-io/stack-orchestrator/releases/latest/download/laconic-so
chmod +x ${install_filename}

# set here for this script
export PATH=$PATH:${install_dir}

# added to profile, manually running `source ~/.profile` is then required
echo "Adding this to ~/.profile: export PATH=$PATH:${install_dir}"
echo "export PATH=$PATH:${install_dir}" >> ~/.profile

# TODO: run this manually again after the script ends
# source ~/.profile

# verify operation
laconic-so version

echo "The Laconic Stack Orchestrator program has been installed at ${install_filename}"
echo "The directory ${install_dir} has been added to PATH in new shells via ~/.profile"
echo "Either open a new shell to use laconic-so on the PATH, or run this command in this shell:"
echo "export PATH=$PATH:${install_dir}"

# Message the user to check docker is working for them
echo "Please test that docker installed correctly by running this command:"
echo "docker run hello-world"

