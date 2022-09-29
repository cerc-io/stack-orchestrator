#!/bin/sh

python3 -m venv venv
source ./venv/bin/activate
pip install --editable .
pip install shiv
shiv -c laconic-so -o laconic-so .
./laconic-so --verbose --local_stack setup-repositories
