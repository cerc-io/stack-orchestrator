#!/bin/sh
laconicd keys show mykey | grep address | cut -d ' ' -f 3
