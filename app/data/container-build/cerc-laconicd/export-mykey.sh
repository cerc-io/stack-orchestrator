#!/bin/sh
echo y | docker compose exec laconicd laconicd keys export mykey --unarmored-hex --unsafe
