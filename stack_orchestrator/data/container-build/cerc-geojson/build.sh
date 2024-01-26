#!/usr/bin/env bash
# Build the geojson image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/geojson:local -f ${CERC_CONTAINER_BASE_DIR}/cerc-geojson/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/geojson.io
#docker build -t cerc/geojson:local -f ${CERC_REPO_BASE_DIR}/geojson.io/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/geojson.io
