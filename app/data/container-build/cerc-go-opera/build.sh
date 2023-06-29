#!/usr/bin/env bash
# Build cerc/go-opera
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# Repo's dockerfile gives build error because it's hardcoded for go 1.17; go 1.19 is required
sed -i 's/FROM golang:1\.[0-9]*-alpine as builder/FROM golang:1.19-alpine as builder/' ${CERC_REPO_BASE_DIR}/go-opera/docker/Dockerfile.opera

docker build -f ${CERC_REPO_BASE_DIR}/go-opera/docker/Dockerfile.opera -t cerc/go-opera:local ${build_command_args} ${CERC_REPO_BASE_DIR}/go-opera
