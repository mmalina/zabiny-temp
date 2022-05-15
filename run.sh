#!/bin/sh

IMG_URL="https://www.chmi.cz/files/portal/docs/poboc/PR/grafy/br/~TEP2M.PNG"
IMG_FILENAME=main_img.png
OUTPUT_JSON=temp.json

# Specify an alternate output dir as a cli argument.
# Otherwise the json is saved in the current dir.
if [ $# -gt 0 ]
then
    OUTPUT_JSON=$1/$OUTPUT_JSON
fi

PREV_MD5SUM="0"
while true
do
    curl -s -o $IMG_FILENAME $IMG_URL
    MD5SUM=$(md5sum $IMG_FILENAME)
    if ! [ "$MD5SUM" = "$PREV_MD5SUM" ]
    then
        ./zabinytemp.py -f $IMG_FILENAME -o $OUTPUT_JSON || true
        PREV_MD5SUM=$MD5SUM
    fi
    sleep 60
done
