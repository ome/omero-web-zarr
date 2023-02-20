
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
        coordinate_transformations = []
        # calculate minimal 'scale' transform based on pyramid dims
        for shape in shapes:
            assert len(shape) == len(data_shape)
            scale = [full / level for full, level in zip(data_shape, shape)]
            coordinate_transformations.append([{"type": "scale", "scale": scale}])

        return coordinate_transformations