#
# Copyright (c) 2021 University of Dundee.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import numpy as np
import tempfile
import zarr
import os
import json
import requests

from django.http import HttpResponse, JsonResponse
from django.core.urlresolvers import reverse

from omero.model.enums import PixelsTypeint8, PixelsTypeuint8, PixelsTypeint16
from omero.model.enums import PixelsTypeuint16, PixelsTypeint32
from omero.model.enums import PixelsTypeuint32, PixelsTypefloat
from omero.model.enums import PixelsTypedouble
from omeroweb.webclient.decorators import login_required
from omeroweb.webgateway.marshal import channelMarshal

PIXEL_TYPES = {
    PixelsTypeint8: np.int8,
    PixelsTypeuint8: np.uint8,
    PixelsTypeint16: np.int16,
    PixelsTypeuint16: np.uint16,
    PixelsTypeint32: np.int32,
    PixelsTypeuint32: np.uint32,
    PixelsTypefloat: np.float32,
    PixelsTypedouble: np.float64
}


@login_required()
def index(request, conn=None, **kwargs):
    """
    omero-web-zarr app Home page
    """
    home = request.build_absolute_uri(reverse("omero_web_zarr_index"))
    return HttpResponse(
        "To open an Image in Vizarr go to "
        "https://hms-dbmi.github.io/vizarr/?source=%simage/[IMAGE_ID].zarr"
        % home
    )


@login_required()
def image_zattrs(request, iid, conn=None, **kwargs):

    image = conn.getObject("Image", iid)

    levels = [0]
    if image.requiresPixelsPyramid():
        # init the rendering engine
        image.getZoomLevelScaling()
        res_descs = image._re.getResolutionDescriptions()
        levels = range(len(res_descs))

    datasets = [{"path": str(level)} for level in levels]

    rv = {
        "multiscales": [
            {
                "datasets": datasets,
                "version": "0.3",
                "axes": get_axes(image)
            }
        ],
        "omero": {
            "channels": [channelMarshal(x) for x in image.getChannels()],
            "id": image.id,
            "rdefs": {
                "defaultT": image._re.getDefaultT(),
                "defaultZ": image._re.getDefaultZ(),
                "model": (image.isGreyscaleRenderingModel()
                          and "greyscale" or "color"),
            }
        }
    }
    return JsonResponse(rv)


def image_zgroup(request, **kwargs):
    return JsonResponse({"zarr_format": 2})


def get_axes(image):
    dims = ['t', 'c', 'z', 'y', 'x']
    axes = []
    for dim in dims:
        if getattr(image, 'getSize' + dim.upper())() > 1:
            axes.append(dim)
    return axes


def get_image_shape(image, level):

    shape = [getattr(image, 'getSize' + dim)() for dim in ('TCZYX')]
    shape = [size for size in shape if size > 1]
    # For down-sampled levels of pyramid, get shape
    if image.requiresPixelsPyramid() and level > 0:
        # init the rendering engine
        image.getZoomLevelScaling()
        levels = image._re.getResolutionDescriptions()
        if level >= len(levels):
            raise Exception(
                "Level %s higher than %s levels for this image" %
                (level, len(levels)))
        shape[-1] = levels[level].sizeX
        shape[-2] = levels[level].sizeY
    return shape


def get_chunk_shape(image):
    chunks = []
    for dim in ('TCZ'):
        if getattr(image, 'getSize' + dim)() > 1:
            chunks.append(1)
    if image.requiresPixelsPyramid():
        # For big images...
        image.getZoomLevelScaling()
        width, height = image._re.getTileSize()
    else:
        # If image is small, could have chunk as whole plane
        width = image.getSizeY()
        height = image.getSizeX()
    chunks.extend([height, width])
    return chunks


@login_required()
def image_zarray(request, iid, level, conn=None, **kwargs):

    level = int(level)
    image = conn.getObject("Image", iid)
    shape = get_image_shape(image, level)
    chunks = get_chunk_shape(image)

    ptype = image.getPrimaryPixels().getPixelsType().getValue()
    np_type = PIXEL_TYPES[ptype]

    rsp = {"data": "fail"}
    with tempfile.TemporaryDirectory() as tmpdirname:
        # creates EMPTY zarray, but it's all we need to write .zarray
        zarr.open_array(tmpdirname, mode='w', shape=shape,
                        chunks=chunks, dtype=np_type)

        # reads zarray
        zattrs_path = os.path.join(tmpdirname, '.zarray')
        with open(zattrs_path, 'r') as reader:
            json_text = reader.read()
            rsp = json.loads(json_text)

    # seems that zarr.open_arry doesn't support dimension_separator
    rsp["dimension_separator"] = "/"

    return JsonResponse(rsp)


@login_required()
def image_chunk(request, iid, level, chunk, conn=None, **kwargs):

    dims = [int(dim) for dim in chunk.split("/")]

    image = conn.getObject("Image", iid)
    axes = get_axes(image)
    shape = get_image_shape(image, level)
    chunks = get_chunk_shape(image)
    ptype = image.getPrimaryPixels().getPixelsType().getValue()
    np_type = PIXEL_TYPES[ptype]

    x = dims[-1]
    y = dims[-2]
    z = dims[axes.index('z')] if 'z' in axes else 0
    c = dims[axes.index('c')] if 'c' in axes else 0
    t = dims[axes.index('t')] if 't' in axes else 0

    tile_w = chunks[-1]
    tile_h = chunks[-2]
    tile_x = x * tile_w
    tile_y = y * tile_h
    # edge tiles might be truncated
    tile_w = min(shape[-1] - tile_x, tile_w)
    tile_h = min(shape[-2] - tile_y, tile_h)
    tile = [tile_x, tile_y, tile_w, tile_h]

    # For tiled images, set Resolution...
    if image.requiresPixelsPyramid() and level > 0:
        # pixels.setResolutionLevel(level)
        pix = image._conn.c.sf.createRawPixelsStore()
        pid = image.getPixelsId()
        try:
            # Need to invert the level...
            max_level = len(image.getZoomLevelScaling()) - 1
            # level 0 is smallest
            level = max_level - level
            pix.setPixelsId(pid, False)
            pix.setResolutionLevel(level)
            tile = pix.getTile(z, c, t, tile_x, tile_y, tile_w, tile_h)
        finally:
            pix.close()

        tile = np.frombuffer(tile, dtype=np_type)
        plane = tile.reshape((tile_h, tile_w))
    else:
        plane = image.getPrimaryPixels().getTile(z, c, t, tile)
    # pad incomplete chunk to full chunk size
    if chunks[-1] != tile_w or chunks[-2] != tile_h:
        plane2 = np.zeros((chunks[-2], chunks[-1]), dtype=plane.dtype)
        plane2[0:tile_h, 0:tile_w] = plane
        plane = plane2

    indices = []
    for dim in "tcz":
        if dim in axes:
            indices.append(0)

    data = ""
    with tempfile.TemporaryDirectory() as tmpdirname:
        # write single chunk to array of same shape
        zarr_array = zarr.open_array(tmpdirname, mode='w', shape=chunks,
                                     chunks=chunks, dtype=plane.dtype)
        zarr_array[tuple(indices)] = plane

        # reads chunk
        indices.extend([0, 0])
        indices = [str(size) for size in indices]
        # path/to/0.0.0.0.0 for 5D image
        chunk_path = os.path.join(tmpdirname, ".".join(indices))
        with open(chunk_path, 'rb') as reader:
            data = reader.read()

    chunk_name = ".".join([str(dim) for dim in [t, c, z, y, x]])
    rsp = HttpResponse(data)
    rsp["Content-Length"] = len(data)
    rsp["Content-Disposition"] = "attachment; filename=%s" % chunk_name
    return rsp


def vizarr(request, url):
    """
    Self-host vizarr to avoit CORS issues

    Delegate all requests to https://hms-dbmi.github.io/vizarr/
    """

    base_url = "https://hms-dbmi.github.io/vizarr/"
    target_url = base_url + url

    response = requests.get(target_url)

    rsp = HttpResponse(response.content)

    if url.endswith(".js"):
        rsp['content-type'] = "application/javascript"

    return rsp
