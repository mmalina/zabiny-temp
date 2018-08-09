# zabiny-temp

## Summary

Check current temperature in Brno-Žabovřesky taken from [CHMI/ČHMU](http://portal.chmi.cz)

The only data that CHMI provides from the meteorological station in Brno-Žabovřesky
is a graph here: http://portal.chmi.cz/files/portal/docs/poboc/PR/grafy/br/grafy-ams-lnk.html

The goal of this project is to read the graphical representation of that image
and return the current temperature as a number.

## Requirements

1. Python 3

1. Required modules - requests, imageio
```bash
pip3 install requests imageio
```

## How to use

```bash
python3 zabinytemp.py
```
