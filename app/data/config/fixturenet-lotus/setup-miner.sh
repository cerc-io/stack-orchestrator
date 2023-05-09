#!/bin/bash

lotus --version
#lotus daemon  --genesis=/devgen.car --profile=bootstrapper --bootstrap=false > /var/log/lotus.log 2>&1
#lotus daemon  --genesis=/devgen.car --bootstrap=false

nohup lotus daemon  --genesis=/devgen.car --profile=bootstrapper --bootstrap=false > /var/log/lotus.log 2>&1 &

# initialization check here
