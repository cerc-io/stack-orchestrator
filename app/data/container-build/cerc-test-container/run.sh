#!/bin/sh

# Test if the container's filesystem is old (run previously) or new
EXISTSFILENAME=/var/exists
echo "Test container starting"
if [[ -f "$EXISTSFILENAME" ]];
then
    TIMESTAMP = `cat $EXISTSFILENAME`
    echo "Filesystem is old, created: $TIMESTAMP" 
else
    echo "Filesystem is fresh"
    echo `date` > $EXISTSFILENAME
fi

# Sleep forever to keep docker happy
while true; do sleep 10; done