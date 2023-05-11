#
# Copyright (c) 2021-2022 University of Dundee.
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

from django.http.response import Http404
import numpy as np
import tempfile
import zarr
import os
import json
import requests

from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.shortcuts import redirect

from .utils import marshal_axes, marshal_axes_v3
from .utils import generate_coordinate_transformations

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
def image_zattrs(request, iid, version, conn=None, **kwargs):

    print("version", version)
    if version not in ("0.3", "0.4"):
        raise Http404("version not supported")

    image = conn.getObject("Image", iid)

    levels = [0]
    if image.requiresPixelsPyramid():
        # init the rendering engine
        image.getZoomLevelScaling()
        res_descs = image._re.getResolutionDescriptions()
        levels = range(len(res_descs))

    datasets = [{"path": str(level)} for level in levels]

    if version != "0.3":
        shapes = get_image_shapes(image)
        transformations = generate_coordinate_transformations(shapes)
        for dataset, transform in zip(datasets, transformations):
            dataset["coordinateTransformations"] = transform

    rv = {
        "multiscales": [
            {
                "datasets": datasets,
                "version": version,
                "axes": marshal_axes(image, version)
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


def get_image_shape(image, level):

    shapes = get_image_shapes(image)
    if level >= len(shapes):
        raise Exception(
            "Level %s higher than %s levels for this image" %
            (level, len(shapes)))
    return shapes[level]


def get_image_shapes(image):

    shape = [getattr(image, 'getSize' + dim)() for dim in ('TCZYX')]
    base_shape = [size for size in shape if size > 1]
    # For down-sampled levels of pyramid, get shape
    shapes = [base_shape]
    if image.requiresPixelsPyramid():
        # init the rendering engine
        image.getZoomLevelScaling()
        levels = image._re.getResolutionDescriptions()
        for level in levels[1:]:
            shape = base_shape[:]
            shape[-1] = level.sizeX
            shape[-2] = level.sizeY
            shapes.append(shape)
    return shapes


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

    # E.g. dims [0, 0, 0, 0, 0] for 5D image or [0, 0, 0] for 3D image
    dims = [int(dim) for dim in chunk.split("/")]

    image = conn.getObject("Image", iid)
    # E.g. axes = ['t', 'c', 'z', 'y', 'x'] for 5D image or ['c', 'y', 'x']
    axes = marshal_axes_v3(image)

    # dims from URL must match number of axes
    if len(dims) != len(axes):
        raise Http404(
            "chunk %s has incorrect number of dimensions for axes: %s" %
            (chunk, axes))

    level = int(level)
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


def apps(request, app, url):
    """
    Self-host app (vizarr or ome-ngff-validator) to avoid CORS issues

    Delegate all vizarr requests to https://hms-dbmi.github.io/vizarr/
    and validator requests to https://ome.github.io/ome-ngff-validator/
    """

    # Both vizarr and validator use 'source'
    # Openwith initially uses a 'source' that is not a valid URL e.g.
    # http://omero-server.org/zarr/vizarr/?source=/zarr/image/3978085.zarr
    # If so, make the 'source' absolute and redirect...
    source = request.GET.get("source")
    if source is not None and not source.startswith("http"):
        source = request.build_absolute_uri(source)
        new_url = reverse("zarr_app", kwargs={"url": "", "app": app})
        # in case Django doesn't know .is_secure() and gives http instead of https
        if not source.startswith(request.scheme + ":"):
            source = request.scheme + ":" + source.split(":", 1)[1]
        return redirect(new_url + "?source=" + source)

    base_urls = {
        "vizarr": "https://hms-dbmi.github.io/vizarr/",
        "validator": "https://ome.github.io/ome-ngff-validator/",
    }
    if app not in base_urls:
        raise Http404("App: %s not found" % app)

    base_url = base_urls[app]
    target_url = base_url + url

    response = requests.get(target_url)

    rsp = HttpResponse(response.content)

    if url.endswith(".js"):
        rsp['content-type'] = "application/javascript"

    return rsp
