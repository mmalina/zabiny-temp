#!/usr/bin/env python3

import pytz
import urllib3
import re
from datetime import datetime, timedelta
import argparse
import json

import requests
import imageio
import numpy as np

# from functools import wraps
# from time import time
#
#
# def timing(f):
#     @wraps(f)
#     def wrapper(*args, **kwargs):
#         start = time()
#         result = f(*args, **kwargs)
#         end = time()
#         print ('Elapsed time: {}'.format(end-start))
#         return result
#     return wrapper

MAIN_PAGE_URL =\
 'http://portal.chmi.cz/files/portal/docs/poboc/PR/grafy/br/grafy-ams-lnk.html'

urllib3.disable_warnings()


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        "--file",
        "-f",
        help="Load the image from a file instead of the default url"
    )
    parser.add_argument("--output", "-o", help="Output file to save json to")

    return parser.parse_args()


def load_img(file):
    """Get the main page and extract the chart image url.
    Then open the image and return it.
    """
    if file is not None:
        uri = file
    else:
        r = requests.get(MAIN_PAGE_URL, verify=False)
        r.raise_for_status()
        imgname = re.search('<td><img src="([^"]*)".*', r.text).group(1)
        baseurl = MAIN_PAGE_URL[0:MAIN_PAGE_URL.rindex('/')]
        imgurl = baseurl + '/' + imgname
        # print(f"Loading image from {imgurl}")
        r = requests.get(imgurl, verify=False)
        r.raise_for_status()
        uri = r.content
    im = imageio.imread(uri, ignoregamma=True)
    assert isinstance(im, np.ndarray)
    return im[:, :, :3]  # Remove the alpha channel, we don't need it


def find_color(img):
    # Get a 3-pixel stripe from the chart - it contains the top of Ž
    places_a = img[435:438, :, :]
    # imageio.imwrite("places_a.png", places_a)
    # Just for debugging - print() prints the whole thing and not just a sample
    np.set_printoptions(threshold=np.inf)
    # Create a new array that will have 0 for grey pixels and 1 for all others
    bin_a = binary_array(places_a)
    # print(bin_a)
    # The template to look for - the caron + upper line in Ž
    template = np.array([[0, 1, 1, 1, 1, 1],
                         [0, 0, 1, 1, 1, 0],
                         [1, 1, 1, 1, 1, 1]], dtype=np.int16)
    for i in range(bin_a.shape[1]-5):
        if np.array_equal(template, bin_a[:3, i:i+6]):
            # We found our match
            # print(f"Found the color at x = {i}")
            break
    # The color is a few pixels to the right and down from our match
    color = places_a[2, i+1]  # e.g. [255 255 255]
    assert color.shape == (3,)
    # print(f"Color: {color}")
    return color


def find_temp(img, color):
    # chart = img[25:]

    # We need to figure out where 0 is on the y axis (temperature)
    numbers = img[:, 980:]
    bin_a = binary_array(numbers)
    # This is the standalone 0 marking zero degrees
    template = np.array([
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
        dtype=np.int16)
    match_row = 0
    for i in range(bin_a.shape[0]-9):
        if np.array_equal(template, bin_a[i:i+10, :]):
            # We found our match
            # print(f"We found the zero: {i}")
            match_row = i
            break
    assert match_row != 0, "We couldn't find 0 on the y axis"
    zero_offset = match_row + 5
    ten_deg = 48 + 47  # how many rows per 10 degrees
    top, bottom, right = 21, 405, 969
    # crawl the chart from the right until we find a value for our color
    # (it can be overriden by other colors in some columns)
    for x in range(right, 100, -1):
        hits = []  # sometimes there can be more than one
        for y in range(top, bottom):
            if np.array_equal(img[y, x], color):
                # print('Match at x,y:', x, y)
                hits.append(y)
        if hits:
            break  # we found our color in the current column
    assert hits, 'We could not find our color in the whole chart'
    hit = sum(hits)/len(hits)
    temperature = round((zero_offset-hit)*10/ten_deg, 1)

    # Find where midnight is on x-axis. It's the think | above 00:00.
    # Then it's 18px per hr (or 3min per px).
    for midnight_col, pixel in enumerate(img[409, 6:]):
        if not np.array_equal(pixel, np.array([153, 153, 153])):
            break
    # We started from x = 6, and then it's 1px to the right
    midnight_col = midnight_col + 7
    # print(f"midnight_col = {midnight_col}")

    time = (x - (midnight_col)) * 60 // 18
    # If there is daytime saving in effect in our time zone
    # we need to add one hour as the chart always shows GMT+1
    if datetime.now(pytz.timezone('Europe/Prague')).utcoffset().seconds ==\
            7200:
        time += 60
    hour = time // 60 % 24
    minute = time % 60
    # print(f"time={time} hour={hour} minute={minute}")

    now = datetime.now(pytz.timezone('Europe/Prague'))
    ts = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # we derive our timestamp from now().
    # there is a possibility that we changed e.g. 0:04 to 23:55.
    # in such case we have to substract 1 from the day
    if ts > now:
        ts = ts - timedelta(days=1)

    # time_str = "{}:{:02d}".format(time // 60 % 24, time % 60)
    # print('Old time_str:',time_str)

    return temperature, ts


def binary_array(im):
    """Create a new array with 0 for grey pixels and 1 for all others"""
    return np.clip(np.where(im == 153, 0, 1).sum(axis=2), 0, 1)


def run(main_img):
    # imageio.imwrite("main_img.png", main_img)
    zabiny_color = find_color(main_img)
    temp, time = find_temp(main_img, zabiny_color)

    return temp, time


def main():
    args = parse_args()

    img = load_img(args.file)
    temp, time = run(img)

    if args.output is not None:
        data = {
            "isotime": time.isoformat(),
            "timestamp": int(time.timestamp()),
            "temp": temp
        }
        with open(args.output, "w") as file:
            file.write(json.dumps(data))
    else:
        print('Temperature:', temp)
        print('Time:', time)
        delta = datetime.now(pytz.timezone('Europe/Prague')) - time
        print('Delay:', delta.seconds//60)


if __name__ == "__main__":
    main()
