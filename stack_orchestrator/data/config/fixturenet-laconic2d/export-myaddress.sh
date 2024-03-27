#!/bin/sh
laconic2d keys show mykey | grep address | cut -d ' ' -f 3
