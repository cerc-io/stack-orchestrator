#!/usr/bin/env bash
# Build cerc/fixturenet-plugeth-plugeth
set -x

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ ! -e "${SCRIPT_DIR}/run-el.sh" ]; then
  cp -fp ${SCRIPT_DIR}/../cerc-fixturenet-eth-geth/run-el.sh ${SCRIPT_DIR}/
fi

docker build -t cerc/fixturenet-plugeth-plugeth:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} $SCRIPT_DIR
