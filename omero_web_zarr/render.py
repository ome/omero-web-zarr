
import os
from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
import numpy as np
from PIL import Image
import requests
from pathlib import Path


def render_image_to_pil(url, image, z=None, t=None):

    if z is None:
        z = image.getDefaultZ()
    else:
        z = int(z)
    if t is None:
        t = image.getDefaultT()
    else:
        t = int(t)

    # read the image data
    reader = Reader(parse_url(url))
    # nodes may include images, labels etc
    nodes = list(reader())
    # first node will be the image pixel data
    image_node = nodes[0]

    pyramid = image_node.data
    # Use highest (full size) resolution of the pyramid
    dask_data = pyramid[0]
    ndims = len(dask_data.shape)

    active_channels = []
    active_colors = []
    active_windows = []

    for index, ch in enumerate(image.getChannels()):
        if ch.isActive():
            active_channels.append(index)
            active_colors.append([val / 255 for val in ch.getColor().getRGB()])
            active_windows.append([int(ch.getWindowStart()), int(ch.getWindowEnd())])

    rgb_plane = None

    for idx, ch_index in enumerate(active_channels):
        color = active_colors[idx]
        window = active_windows[idx]

        # slice nd plane to 2d...
        # bioformats2raw produces 5D data, even if sizeZ/C/T is 1
        indices = []
        if image.getSizeT() > 1 or ndims == 5:
            indices.append(t)
        if image.getSizeC() > 1 or ndims == 5:
            indices.append(ch_index)
        if image.getSizeZ() > 1 or ndims == 5:
            indices.append(z)

        indices.append(np.s_[:])
        indices.append(np.s_[:])

        print("dask_data", dask_data.shape, indices)

        plane_2d = dask_data[tuple(indices)]
        plane_2d = plane_2d.compute()

        plane = display(plane_2d, window[0], window[1])
        if rgb_plane is None:
            rgb_plane = np.zeros((*plane.shape, 3), np.uint16)
        for index, fraction in enumerate(color):
            if fraction > 0:
                rgb_plane[:, :, index] += (fraction * plane).astype(rgb_plane.dtype)

    rgb_plane.clip(0, 255, out=rgb_plane)
    rgb_plane = rgb_plane.astype(np.uint8)

    img = Image.fromarray(rgb_plane)
    return img


def display(image, display_min, display_max): # copied from Bi Rico
    # https://stackoverflow.com/questions/14464449/using-numpy-to-efficiently-convert-16-bit-image-data-to-8-bit-for-display-with
    image.clip(display_min, display_max, out=image)
    image -= display_min
    np.floor_divide(image, (display_max - display_min + 1) / 256,
                    out=image, casting='unsafe')
    return image.astype(np.uint8)


# def render_plane(dask_data, z, c, t, window=None):
#     # slice nD -> 2D
#     print("dask_data", dask_data.shape, z, c, t)
#     channel0 = dask_data[c, z, :, :]
#     channel0 = channel0.compute()

#     if window is None:
#         min_val = channel0.min()
#         max_val = channel0.max()
#         window = [min_val, max_val]

#     return display(channel0, window[0], window[1])


# def setActiveChannels(dask_data, active_indecies, colors, windows=None):
#     # colors are (r, g, b)
#     rgb_plane = None

#     # TODO: set Z/T properly!
#     the_z = 0
#     the_t = 0
#     for idx, ch_index in enumerate(active_indecies):
#         color = colors[idx]
#         window = windows[idx] if windows is not None else None
#         print("----", ch_index, color, window)
#         plane = render_plane(dask_data, the_t, ch_index, the_z, window)
#         if rgb_plane is None:
#             rgb_plane = np.zeros((*plane.shape, 3), np.uint16)
#         for index, fraction in enumerate(color):
#             if fraction > 0:
#                 rgb_plane[:, :, index] += (fraction * plane).astype(rgb_plane.dtype)

#     rgb_plane.clip(0, 255, out=rgb_plane)
#     return rgb_plane.astype(np.uint8)
