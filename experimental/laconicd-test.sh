#!/usr/bin/env bash

# Start fixturenet-laconicd
# Wait for chain to start
# Run command to extract key
# docker exec -it 383cdc5afeb1 laconicd keys export mykey --unarmored-hex --unsafe
# WARNING: The private key will be exported as an unarmored hexadecimal string. USE AT YOUR OWN RISK. Continue? [y/N]: y
# ef564f8af713f62112cb6588bc2a33ece873f9a4336821fffeda9477667b3b8f
# Configure key in env var
# export PRIVATE_KEY=ef564f8af713f62112cb6588bc2a33ece873f9a4336821fffeda9477667b3b8f
# Find external ports
# restEndpoint: process.env.LACONICD_REST_ENDPOINT || 'http://localhost:1317',
#     gqlEndpoint: process.env.LACONICD_GQL_ENDPOINT || 'http://localhost:9473/api'
# Configure env vars for ports
# Start laconicd-test container in separate cluster?
# Tell it to run tests
# Grab results from log
