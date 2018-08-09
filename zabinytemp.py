#!/usr/bin/env python3

import requests
import re
import imageio
import numpy as np
from datetime import datetime
import pytz

MAIN_PAGE_URL = 'http://portal.chmi.cz/files/portal/docs/poboc/PR/grafy/br/grafy-ams-lnk.html'

def load_img():
    # Get the main page and extract the chart image url.
    # Then open the image and return it.
    r = requests.get(MAIN_PAGE_URL)
    assert r.status_code == 200, 'Status code should be 200'
    imgname = re.search('<td><img src="([^"]*)".*',r.text).group(1)
    baseurl = MAIN_PAGE_URL[0:MAIN_PAGE_URL.rindex('/')]
    imgurl = baseurl + '/' + imgname
    im = imageio.imread(imgurl,ignoregamma=True)
    assert isinstance(im, np.ndarray)
    return im[:,:,:3] # Remove the alpha channel, we don't need it

def find_color(img):
    # Get a 3-pixel stripe from the chart - it contains the top of Ž
    places_a = img[435:438,:,:]
    # Just for debugging - print() prints the whole thing and not just a sample
    np.set_printoptions(threshold=np.inf)
    # Create a new array that will have 0 for grey pixels and 1 for all others
    bin_a = binary_array(places_a)
    # The template to look for - the caron + upper line in Ž
    template = np.array([[0,1,1,1,1,1],[0,0,1,1,1,0],[1,1,1,1,1,1]])
    for i in range(bin_a.shape[1]-5):
        if np.array_equal(template,bin_a[:,i:i+6]):
            # We found our match
            break
    # The color is a few pixels to the right and down from our match
    color = places_a[2,i+1] # e.g. [255 255 255]
    assert color.shape == (3,)
    return color

def find_temp(img, color):
    chart = img[25:]

    # We need to figure out where 0 is on the y axis (temperature)
    numbers = img[:,880:]
    bin_a = binary_array(numbers)
    # This is the standalone 0 marking zero degrees
    template = np.array([[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 1., 1., 1., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 1., 1., 1., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
       [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]])
    for i in range(bin_a.shape[0]-9):
        if np.array_equal(template,bin_a[i:i+10,:]):
            # We found our match
            break
    assert i < bin_a.shape[0]-9
    zero_offset = i + 5
    ten_deg = 48+47 # how many rows per 10 degrees
    top,bottom,right = 21,405,868
    # print('Zero offset is', zero_offset)
    # print('Total range is', (bottom-top)*10/ten_deg)
    # crawl the chart from the right until we find a value for our color
    # (it can be overriden by other colors in some columns)
    for x in range(right,100,-1):
        hits = [] # sometimes there can be more than one
        for y in range(21,405):
            if np.array_equal(img[y,x],color):
                #print('Match at x,y:',x,y)
                hits.append(y)
        if hits:
            break # we found our color in the current column
    assert hits, 'We could not find our color in the whole chart'
    hit = sum(hits)/len(hits)
    temperature = (zero_offset-hit)*10/ten_deg

    # Find where midnight is on x-axis. Then it's 18px per hr (or 3min per px).
    for midnight_col,pixel in enumerate(img[430]):
        if not np.array_equal(pixel,np.array([153,153,153])):
            break
    # print('Midnight_col:',midnight_col)

    # If there is daytime saving in effect in our time zone
    # we need to add one hour as the chart always shows GMT+1
    if datetime.now(pytz.timezone('Europe/Prague')).utcoffset().seconds == 7200:
        offset = 60
    else:
        offset = 0

    time = (x - midnight_col) * 60 // 18 + offset
    time_str = "{}:{:02d}".format(time // 60 % 24, time % 60)

    return round(temperature,1),time_str

def binary_array(img):
    # Create a new array that will have 0 for grey pixels and 1 for all others
    ret = np.zeros(img.shape[:2])
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            if img[i,j,0] != 153 or\
                img[i,j,1] != 153 or\
                img[i,j,2] != 153:
                ret[i,j] = 1
    return ret

def temp():
    main_img = load_img()
    zabiny_color = find_color(main_img)
    t,_ = find_temp(main_img, zabiny_color)
    return t

if __name__ == "__main__":
        main_img = load_img()
        zabiny_color = find_color(main_img)
        # print('Color:', zabiny_color)
        t,time = find_temp(main_img, zabiny_color)
        print('Temperature:', t)
        print('Time:', time)
