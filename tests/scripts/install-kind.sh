#!/usr/bin/env bash
# TODO: handle ARM
curl --silent -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
mv ./kind /usr/local/bin
