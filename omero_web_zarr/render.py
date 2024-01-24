
import os
from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
import numpy as np
from PIL import Image
import requests
from pathlib import Path


def render_image_to_pil(url):

    # read the image data
    reader = Reader(parse_url(url))
    # nodes may include images, labels etc
    nodes = list(reader())
    # first node will be the image pixel data
    image_node = nodes[0]

    pyramid = image_node.data
    # Use highest (full size) resolution of the pyramid
    dask_data = pyramid[0]

    # rgb = np.dstack((red, green, blue))
    RED = (1, 0, 0)
    GREEN = (0, 1, 0)
    BLUE = (0, 0, 1)
    YELLOW = (1, 1, 0)
    WHITE = (1, 1, 1)

    active_channels = [0, 1]
    active_colors = [RED, GREEN]
    active_windows = [[50, 4095], [50, 4095]]

    rgb = setActiveChannels(dask_data, active_channels, active_colors, active_windows)
    img = Image.fromarray(rgb)
    return img


def display(image, display_min, display_max): # copied from Bi Rico
    # https://stackoverflow.com/questions/14464449/using-numpy-to-efficiently-convert-16-bit-image-data-to-8-bit-for-display-with
    image.clip(display_min, display_max, out=image)
    image -= display_min
    np.floor_divide(image, (display_max - display_min + 1) / 256,
                    out=image, casting='unsafe')
    return image.astype(np.uint8)

def render_plane(dask_data, z, c, t, window=None):
    # slice 5D -> 2D
    channel0 = dask_data[t, c, z, :, :]
    channel0 = channel0.compute()

    if window is None:
        min_val = channel0.min()
        max_val = channel0.max()
        window = [min_val, max_val]

    return display(channel0, window[0], window[1])


def setActiveChannels(dask_data, active_indecies, colors, windows=None):
    # colors are (r, g, b)
    rgb_plane = None

    the_z = 0
    the_t = 0
    for idx, ch_index in enumerate(active_indecies):
        color = colors[idx]
        window = windows[idx] if windows is not None else None
        print("----", ch_index, color, window)
        plane = render_plane(dask_data, the_t, ch_index, the_z, window)
        if rgb_plane is None:
            rgb_plane = np.zeros((*plane.shape, 3), np.uint16)
        for index, fraction in enumerate(color):
            if fraction > 0:
                rgb_plane[:, :, index] += (fraction * plane)

    rgb_plane.clip(0, 255, out=rgb_plane)
    return rgb_plane.astype(np.uint8)
