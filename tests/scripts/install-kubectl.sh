#!/usr/bin/env bash
# TODO: handle ARM
# Pin kubectl to match Kind's default k8s version (v1.31.x)
curl --silent -LO "https://dl.k8s.io/release/v1.31.2/bin/linux/amd64/kubectl"
chmod +x ./kubectl
mv ./kubectl /usr/local/bin
