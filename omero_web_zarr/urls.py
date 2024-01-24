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

from django.urls import re_path

from . import views

urlpatterns = [

    # index 'home page' of the app
    re_path(r'^$', views.index, name="omero_web_zarr_index"),

    re_path(r'^v(?P<version>0\.[3-4]+)/image/(?P<iid>[0-9]+).zarr/.zattrs$',
            views.image_zattrs, name='zarr_image_zattrs'),

    re_path(r'^v(?P<version>0\.[3-4]+)/image/(?P<iid>[0-9]+).zarr/.zgroup$',
            views.image_zgroup, name='zarr_image_zgroup'),

    re_path(r'^v(?P<version>0\.[3-4]+)/image/(?P<iid>[0-9]+).zarr/(?P<level>[0-9]+)/.zarray$',  # noqa
            views.image_zarray, name='zarr_image_zarray'),

    re_path(r'^v(?P<version>0\.[3-4]+)/image/(?P<iid>[0-9]+).zarr/(?P<level>[0-9]+)/(?P<chunk>[0-9/]+)$',  # noqa
            views.image_chunk, name='zarr_image_chunk'),

    # Delegate all /vizarr/ or /validator/ urls to statically-hosted files
    re_path(r'^(?P<app>vizarr|validator)/(?P<url>.*)$', views.apps, name='zarr_app'),  # noqa

    # supports same rendering settings in query as webgateway/render_image
    re_path(r"^render_image/(?P<iid>[0-9]+)/(?:(?P<z>[0-9]+)/)?(?:(?P<t>[0-9]+)/)?$",
            views.render_image, name="zarr_render_image"),
]
