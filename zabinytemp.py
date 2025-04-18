#!/usr/bin/env python3

import pytz
import urllib3
from datetime import datetime
import argparse
import json

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

# Taken from https://www.chmi.cz/files/portal/docs/poboc/OS/KW/Captor/pobocka.BR.1.html
IMG_URL = (
    "https://www.chmi.cz/files/portal/docs/poboc/OS/KW/Captor/tmp/DMULTI-B2BZAB01.gif"
)

urllib3.disable_warnings()


def parse_args():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "--file", "-f", help="Load the image from a file instead of the default url"
    )
    parser.add_argument("--output", "-o", help="Output file to save json to")

    return parser.parse_args()


def load_img(file):
    """Get the main page and extract the chart image url.
    Then open the image and return it.
    """
    if file is not None:
        print(f"Loading image from file: {file}")
        uri = file
    else:
        uri = IMG_URL
    # im = imageio.v3.imread(uri, ignoregamma=True)
    # ignoregamma is no longer supported, but it seems somehow
    # it works even without it? I think it was a problem before.
    # need to double check

    # Somehow the gif appears to be an animated gif, so we need to
    # select the first frame only
    im = imageio.v3.imread(uri)[0]
    assert isinstance(im, np.ndarray)
    return im


def find_temp(img):
    bin_img = binary_array(img)

    # Search for vertical dark blue lines and skip 6 of them
    template = np.array(
        [
            [1],
            [1],
            [1],
            [1],
            [1],
            [1],
            [1],
            [1],
            [1],
            [1],
        ]
    )
    y = 300
    lines_count = 0
    for x in range(img.shape[1] - 10, 1, -1):
        snippet = bin_img[y : y + 10, x : x + 1]
        if np.array_equal(template, snippet):
            lines_count += 1
            if lines_count == 6:
                # We found vertical line right of temp legend
                # print(f"We found final line: {x} {y}")
                zero_right_limit = x - 14
            elif lines_count == 7:
                # We found vertical line left of temp legend
                zero_left_limit = x + 2
                break
    if lines_count != 7:
        raise ValueError("We couldn't find the final line before temp legend")

    # Find the red 0 on the y axis (temperature legend)
    # This is the standalone red 0 marking zero degrees (with 3px of white on the left)
    template = np.array(
        [
            [0, 0, 0, 1, 1, 1, 1, 1],
            [0, 0, 0, 1, 1, 0, 1, 1],
            [0, 0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0, 1],
        ],
        dtype=np.uint8,
    )
    match_row = 0
    match_col = 0
    for x in range(zero_left_limit, zero_right_limit):
        for y in range(50, 550):
            snippet = bin_img[y : y + 5, x : x + 8]
            # print(f"Checking row {y} col {x}")
            # print(snippet)
            if np.array_equal(template, snippet):
                # We found our match
                # print(f"We found the zero: {x} {y}")
                match_row = y
                match_col = x
                zero_y = y + 3
                temp_color = img[zero_y, x + 3]
                # print("Color:", temp_color)
                break
        if match_row != 0:
            break
    assert match_row != 0, "We couldn't find 0 on the y axis"
    assert match_col != 0, "We couldn't find 0 on the x axis"

    # Crawl the chart from the right until we find a value for our color
    # (it can be overriden by other colors in some columns)
    for x in range(match_col - 4, 100, -1):
        hits = []  # sometimes there can be more than one
        for y in range(50, 530):
            if np.array_equal(img[y, x], temp_color):
                # print("Temp match at x,y:", x, y)
                hits.append(y)
        if hits:
            break  # we found our color in the current column
    assert hits, "We could not find our color in the whole chart"
    # 113px per 10 degrees
    hit = sum(hits) / len(hits)
    temperature = round((zero_y - hit) * 10 / 113, 1)
    return temperature


def binary_array(im):
    """Create a new array with 0 for near-white pixels and 1 for all others."""
    # Tolerance to account for small rendering noise
    tolerance = 2
    return np.clip(np.where(np.abs(im - 254) <= tolerance, 0, 1).sum(axis=2), 0, 1)


def main():
    args = parse_args()

    img = load_img(args.file)
    # print("Image shape:", img.shape)
    # imageio.imwrite("main_img.png", main_img)
    temp = find_temp(img)
    time = datetime.now(pytz.timezone("Europe/Prague")).replace(microsecond=0)
    if args.output is not None:
        data = {
            "isotime": time.isoformat(),
            "timestamp": int(time.timestamp()),
            "temp": temp,
        }
        with open(args.output, "w") as file:
            file.write(json.dumps(data))
    else:
        print("Temperature:", temp)
        print("Time:", time)


if __name__ == "__main__":
    main()
