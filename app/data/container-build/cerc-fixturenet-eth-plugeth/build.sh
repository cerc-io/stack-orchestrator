#!/usr/bin/env bash
# Build cerc/fixturenet-eth-plugeth
set -x

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ ! -d "${SCRIPT_DIR}/genesis" ]; then
  cp -frp ${SCRIPT_DIR}/../cerc-fixturenet-eth-geth/genesis ${SCRIPT_DIR}/genesis
fi

if [ ! -d "${SCRIPT_DIR}/run-el.sh" ]; then
  cp -fp ${SCRIPT_DIR}/../cerc-fixturenet-eth-geth/run-el.sh ${SCRIPT_DIR}/
fi

docker build -t cerc/fixturenet-eth-plugeth:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} $SCRIPT_DIR
