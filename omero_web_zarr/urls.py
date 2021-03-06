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

from django.conf.urls import url

from . import views

urlpatterns = [

    # index 'home page' of the app
    url(r'^$', views.index, name="omero_web_zarr_index"),

    url(r'^image/(?P<iid>[0-9]+).zarr/.zattrs$',
        views.image_zattrs, name='zarr_image_zattrs'),

    url(r'^image/(?P<iid>[0-9]+).zarr/.zgroup$',
        views.image_zgroup, name='zarr_image_zgroup'),

    url(r'^image/(?P<iid>[0-9]+).zarr/(?P<level>[0-9]+)/.zarray$',
        views.image_zarray, name='zarr_image_zarray'),

    url(r'^image/(?P<iid>[0-9]+).zarr/(?P<level>[0-9]+)/(?P<t>[0-9]+).'
        r'(?P<c>[0-9]+).(?P<z>[0-9]+).(?P<y>[0-9]+).(?P<x>[0-9]+)$',
        views.image_chunk, name='zarr_image_chunk'),

    # Delegate all /vizarr/* urls to https://hms-dbmi.github.io/vizarr/
    url(r'^vizarr/(?P<url>.*)$', views.vizarr, name='zarr_vizarr'),
]
