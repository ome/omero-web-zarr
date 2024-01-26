
#
# Copyright (c) 2023 University of Dundee.
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

from django.http import Http404
from omero.sys import ParametersI
from omero.rtypes import rstring


def marshal_pixel_sizes(image):

    pixel_sizes = {}
    pix_size_x = image.getPixelSizeX(units=True)
    pix_size_y = image.getPixelSizeY(units=True)
    pix_size_z = image.getPixelSizeZ(units=True)
    # All OMERO units.lower() are valid UDUNITS-2 and therefore NGFF spec
    if pix_size_x is not None:
        pixel_sizes["x"] = {
            "unit": str(pix_size_x.getUnit()).lower(),
            "value": pix_size_x.getValue(),
        }
    if pix_size_y is not None:
        pixel_sizes["y"] = {
            "unit": str(pix_size_y.getUnit()).lower(),
            "value": pix_size_y.getValue(),
        }
    if pix_size_z is not None:
        pixel_sizes["z"] = {
            "unit": str(pix_size_z.getUnit()).lower(),
            "value": pix_size_z.getValue(),
        }
    return pixel_sizes


def marshal_axes_v3(image):
    dims = ['t', 'c', 'z', 'y', 'x']
    axes = []
    for dim in dims:
        if getattr(image, 'getSize' + dim.upper())() > 1:
            axes.append(dim)
    return axes


def marshal_axes(image, version):

    if version not in ("0.3", "0.4"):
        raise Http404("version not supported")

    if version == "0.3":
        return marshal_axes_v3(image)

    # Prepare axes and transformations info...
    size_c = image.getSizeC()
    size_z = image.getSizeZ()
    size_t = image.getSizeT()
    pixel_sizes = marshal_pixel_sizes(image)

    axes = []
    if size_t > 1:
        axes.append({"name": "t", "type": "time"})
    if size_c > 1:
        axes.append({"name": "c", "type": "channel"})
    if size_z > 1:
        axes.append({"name": "z", "type": "space"})
        if pixel_sizes and "z" in pixel_sizes:
            axes[-1]["unit"] = pixel_sizes["z"]["unit"]
    # last 2 dimensions are always y and x
    for dim in ("y", "x"):
        axes.append({"name": dim, "type": "space"})
        if pixel_sizes and dim in pixel_sizes:
            axes[-1]["unit"] = pixel_sizes[dim]["unit"]

    return axes


def generate_coordinate_transformations(shapes):

        data_shape = shapes[0]
        transformations = []
        # calculate minimal 'scale' transform based on pyramid dims
        for shape in shapes:
            assert len(shape) == len(data_shape)
            scale = [full / level for full, level in zip(data_shape, shape)]
            transformations.append([{"type": "scale", "scale": scale}])

        return transformations


def get_clientpath_by_endswith(conn, image_id, pathending):
    query_service = conn.getQueryService()
    params = ParametersI()
    params.addId(image_id)
    params.add("zarr", rstring("%%%s" % pathending))
    query = """ select u.clientPath from Fileset fs
        join fs.usedFiles u
        left outer join fs.images as image
        where image.id=:id
        and u.clientPath like :zarr"""
    result = query_service.projection(query, params, conn.SERVICE_OPTS)
    if len(result) == 0:
        return None
    return result[0][0].val


def get_zarr_s3_path(conn, image_id):
    """
    Check Fileset clientPaths for path ending zarr/.zattrs

    If Image is in a Plate/Well, add eg. /A/1/0/ to path.
    """
    client_path = get_clientpath_by_endswith(conn, image_id, "zarr/.zattrs")
    if client_path is None:
        return None

    # We also need clientPath to be a publicly-accessible URL
    zarr_path = client_path.replace("/.zattrs", "")

    # Check if Image is in a Well - need to add /row/col/field/ e.g. /A/1/0
    query_service = conn.getQueryService()
    wsparams = ParametersI()
    wsparams.addId(image_id)
    wsquery = """select well.plate.id, well.row, well.column, index(ws) from Well well
        join well.wellSamples ws where ws.image.id=:id"""
    ws = query_service.projection(wsquery, wsparams, conn.SERVICE_OPTS)
    if len(ws) > 0:
        plate_id = ws[0][0].val
        plate = conn.getObject("Plate", plate_id)
        row = plate.getRowLabels()[ws[0][1].val]
        column = plate.getColumnLabels()[ws[0][2].val]
        ws_index = ws[0][3].val
        row_col_field = f"/{row}/{column}/{ws_index}/"
        zarr_path += row_col_field
    else:
        # Check whether this is a bioformats2raw image
        metadata_path = get_clientpath_by_endswith(conn, image_id,
                                                   "OME/METADATA.ome.xml")
        if metadata_path is not None:
            zarr_path += "/0/"

    return zarr_path
