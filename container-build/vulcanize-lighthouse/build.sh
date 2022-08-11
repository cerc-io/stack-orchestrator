#!/usr/bin/env bash
# Build vulcanize/lighthouse

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t vulcanize/lighthouse:local ${SCRIPT_DIR}

#version: "3.2"
#services:
#  lighthouse:
#    restart: always
#    build:
#      context: ../../
#      dockerfile: ./docker/latest/lighthouse.Dockerfile
#    environment:
#      - NETWORK=mainnet
#    volumes:
#      - lighthouse_db:/root/.lighthouse
#    ports:
#      - 127.0.0.1:5052:5052
#      - 9000:9000/udp
#      - 9000:9000/tcp
#    command: ["tail", "-f", "/dev/null"]
#
#volumes:
#  lighthouse_db:
