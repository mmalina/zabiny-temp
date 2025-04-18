#!/bin/sh

IMG_URL="https://www.chmi.cz/files/portal/docs/poboc/OS/KW/Captor/tmp/DMULTI-B2BZAB01.gif"
IMG_FILENAME=main_img.gif
OUTPUT_JSON=/data/temp.json

mkdir /data || true

nginx -g "daemon off;" &

PREV_MD5SUM=0
while true
do
    curl -s -o $IMG_FILENAME $IMG_URL
    MD5SUM=$(md5sum $IMG_FILENAME)
    if ! [ "$MD5SUM" = "$PREV_MD5SUM" ]
    then
        echo "Image changed, running zabinytemp.py"
        ./zabinytemp.py -f $IMG_FILENAME -o $OUTPUT_JSON || true
        PREV_MD5SUM=$MD5SUM
    fi
    sleep 60
done
