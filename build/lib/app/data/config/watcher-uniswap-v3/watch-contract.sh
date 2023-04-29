#!/bin/sh

set -e
set -u

echo "Watching factory contract 0x1F98431c8aD98523631AE4a59f267346ea31F984"
yarn watch:contract --address 0x1F98431c8aD98523631AE4a59f267346ea31F984 --kind factory --startingBlock 12369621 --checkpoint

echo "Watching nfpm contract 0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
yarn watch:contract --address 0xC36442b4a4522E871399CD717aBDD847Ab11FE88 --kind nfpm --startingBlock 12369651 --checkpoint
