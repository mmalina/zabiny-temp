# zabiny-temp

## Summary

Check current temperature in Brno-Žabovřesky taken from [CHMI/ČHMU](http://portal.chmi.cz)

The only data that CHMI provides from the meteorological station in Brno-Žabovřesky
is a graph here: http://portal.chmi.cz/files/portal/docs/poboc/PR/grafy/br/grafy-ams-lnk.html

The goal of this project is to read the graphical representation of that image
and return the current temperature as a number. A json file with the temperature
and timestamp is then exposed via nginx running in an addon in
[my installation](https://github.com/mmalina/hass)
of [Home Assistant](https://www.home-assistant.io).

There are two pieces that make up this project:

1. Python script

   This parses the image and returns the current temperature and
   the corresponding time read from the image.

1. Home Assistant addon

   This is a container that runs the python script periodically and exposes
   the resulting json via nginx web server.


## How to run the standalone python app

Clone the repo
```bash
git clone https://github.com/mmalina/zabiny-temp.git
cd zabiny-temp
```

Install virtual environment, install deps and run the script
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 zabinytemp.py
```

## How to install addon

This addon is meant to be consumed in Home Assistant as a local
addon via cloning the repo.

Clone this repo in the `addons/` volume (e.g. mounted via the samba HA
add-on), then refresh the add-ons and install the local addon. Once
the add-on is running, the resulting json will be available on the internal network inside HA containers. You can get the temperature
via the restfull sensor in HA using the local address
http://local-zabiny-temp/temp.json .

## Legacy Setup

In the past, the app would be deployed in a public cloud and I would be able
to consume and display the data using a Connect IQ app running
on my Garmin fenix 5s watch.

![Turn a chart into a number](show.png)

### Connect IQ app

This is a simple app based on the WebRequest sample app included
in the Connect IQ SDK. It loads the json from my webhosting and displays
the temperature and delay in minutes between the time read from the image and
current time.

## Contents

The files and directories included in this repo.

### ZabinyTemp

This is the Eclipse project for the Connect IQ app. You can easily import it into
Eclipse. See here for for more information about Connect IQ app development:
https://developer.garmin.com/connect-iq/programmers-guide/getting-started/

### config.json

Home Assistant addon config.

### Dockerfile

Definition of the Home Assistant addon container.

### requirements.txt

Python modules required for `zabinytemp.py`.

### run.sh

The main script that is started in the container. It periodically
runs `zabinytemp.py` to check the current temperature and saves
the json in /data (this is the persistent volume available
to each Home Assistant addon and the nginx web server is configured
to use it as document root).

### zabinytemp.py

Python app that returns the current temperature read from the image
on CHMI web.
