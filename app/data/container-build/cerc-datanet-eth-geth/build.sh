#!/usr/bin/env bash
#
#Build cerc/datanet-eth-geth

set +e
set+x

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

rm -rf $SCRIPT_DIR/build
cp -rp $SCRIPT_DIR/../cerc-fixturenet-eth-geth $SCRIPT_DIR/build

cp -f $SCRIPT_DIR/el-config.yaml $SCRIPT_DIR/build/genesis/el/el-config.yaml

docker build -t cerc/datanet-eth-geth:local ${SCRIPT_DIR}/build
