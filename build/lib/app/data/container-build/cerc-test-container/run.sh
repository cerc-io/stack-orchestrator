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

# Run nginx which will block here forever
/usr/sbin/nginx -g "daemon off;"
