#!/usr/bin/env bash
# Script to automate the steps needed to make a cloned project repo runnable on the path
# (beware of PATH having some other file with the same name ahead of ours)
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
    echo PATH is $PATH
fi
python3 -m venv venv
source ./venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
pip install shiv
pip install --editable .
