#!/usr/bin/env bash
# Build cerc/fixturenet-plugeth-lighthouse

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ ! -d "${SCRIPT_DIR}/genesis" ]; then
  cp -frp ${SCRIPT_DIR}/../cerc-fixturenet-eth-lighthouse/genesis ${SCRIPT_DIR}/genesis
fi

if [ ! -e "${SCRIPT_DIR}/run-cl.sh" ]; then
  cp -fp ${SCRIPT_DIR}/../cerc-fixturenet-eth-lighthouse/run-cl.sh ${SCRIPT_DIR}/
fi

if [ ! -d "${SCRIPT_DIR}/scripts" ]; then
  cp -frp ${SCRIPT_DIR}/../cerc-fixturenet-eth-lighthouse/scripts ${SCRIPT_DIR}/
fi

docker build -t cerc/fixturenet-plugeth-lighthouse:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} $SCRIPT_DIR
