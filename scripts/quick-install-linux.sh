#!/usr/bin/env bash
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi

install_dir=~/bin

# First display a reasonable warning to the user unless run with -y
if ! [[ $# -eq 1 && $1 == "-y" ]]; then
  echo "**************************************************************************************"
  echo "This script requires sudo privilege. It installs Laconic Stack Orchestrator"
  echo "into: ${install_dir}. It also *removes* any existing docker installed on"
  echo "this machine and then installs the latest docker release as well as other"
  echo "required packages."
  echo "Only proceed if you are sure you want to make those changes to this machine."
  echo "**************************************************************************************"
  read -p "Are you sure you want to proceed? " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# This script assumes root permissions on a fresh Ubuntu Digital Ocean droplet
# with these recommended specs: 16 GB Memory / 8 Intel vCPUs / 320 GB Disk

# TODO:
#   Check python3 is available
#   Check machine resources are sufficient

# Determine if we are on Debian or Ubuntu
linux_distro=$(lsb_release -a 2>/dev/null | grep "^Distributor ID:" | cut -f 2)
case $linux_distro in
  Debian)
    echo "Installing docker for Debian"
    ;;
  Ubuntu)
    echo "Installing docker for Ubuntu"
    ;;
  *)
    echo "ERROR: Detected unknown distribution $linux_distro, can't install docker"
    exit 1
    ;;
esac

# dismiss the popups
export DEBIAN_FRONTEND=noninteractive

## https://docs.docker.com/engine/install/ubuntu/
## https://docs.docker.com/engine/install/debian/
## https://superuser.com/questions/518859/ignore-packages-that-are-not-currently-installed-when-using-apt-get-remove1
packages_to_remove="docker docker-engine docker.io containerd runc docker-compose docker-doc podman-docker"
installed_packages_to_remove=""
for package_to_remove in $(echo $packages_to_remove); do
  $(dpkg --info $package_to_remove &> /dev/null)
  if [[ $? -eq 0 ]]; then
    installed_packages_to_remove="$installed_packages_to_remove $package_to_remove"
  fi
done

# Enable stop on error now, since we needed it off for the code above
set -euo pipefail  ## https://vaneyckt.io/posts/safer_bash_scripts_with_set_euxo_pipefail/

if [[ -n "${installed_packages_to_remove}" ]]; then
  echo "**************************************************************************************"
  echo "Removing existing docker packages"
  sudo apt -y remove $installed_packages_to_remove
fi

echo "**************************************************************************************"
echo "Installing dependencies"
sudo apt -y update

# laconic-so depends on jq
sudo apt -y install jq
# laconic-so depends on git
sudo apt -y install git
# curl used below
sudo apt -y install curl 
# docker repo add depends on gnupg and updated ca-certificates
sudo apt -y install ca-certificates gnupg

# Add dockerco package repository
# For reasons not obvious, the dockerco instructions for installation on
# Debian and Ubuntu are slightly different here
case $linux_distro in
  Debian)
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    ;;
  Ubuntu)
    sudo mkdir -m 0755 -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    ;;
  *)
    echo "ERROR: Detected unknown distribution $linux_distro, can't install docker"
    exit 1
    ;;
esac
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${linux_distro,,} \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Penny in the update jar
sudo apt -y update

echo "**************************************************************************************"
echo "Installing docker"
sudo apt -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow the current user to use Docker
sudo usermod -aG docker $USER

echo "**************************************************************************************"
echo "Installing laconic-so"
# install latest `laconic-so`
install_filename=${install_dir}/laconic-so
mkdir -p  ${install_dir}
curl -L -o ${install_filename} https://github.com/cerc-io/stack-orchestrator/releases/latest/download/laconic-so
chmod +x ${install_filename}

echo "**************************************************************************************"
# Check if our PATH line is already there
path_add_command="export PATH=\$PATH:${install_dir}"
if ! grep -q "${path_add_command}" ~/.profile
then
  echo "Adding this line to the end of ~/.profile:"
  echo ${path_add_command}
  echo ${path_add_command} >> ~/.profile
fi

echo "**************************************************************************************"
# PATH set here for commands run in this script
export PATH=$PATH:${install_dir}
echo Installed laconic-so version: $(laconic-so version)

echo "**************************************************************************************"
echo "The Laconic Stack Orchestrator program laconic-so has been installed at ${install_filename}"
echo "The directory ${install_dir} has been added to PATH in *new* shells via ~/.profile"
echo "**************************************************************************************"
# Message the user to check docker is working for them
echo "Please log in again (docker will not work in this current shell) then:"
echo "test that docker is correctly installed and working for your user by running the"
echo "command below (it should print a message beginning \"Hello from Docker!\"):"
echo
echo "docker run hello-world"
echo
