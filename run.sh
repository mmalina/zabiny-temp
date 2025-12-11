#!/bin/sh

OUTPUT_JSON=/data/temp.json

mkdir /data || true

nginx -g "daemon off;" &

while true
do
    echo "Fetching temperature data..."
    ./zabinytemp.sh -o $OUTPUT_JSON || true
    sleep 60
done
