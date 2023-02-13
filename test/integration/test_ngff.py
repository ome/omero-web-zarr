#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2021-2023 University of Dundee & Open Microscopy Environment.
# All rights reserved. Use is subject to license terms supplied in LICENSE.txt
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Integration tests for reading zarr data."""

import json
import os
import pytest
import zarr
from django.urls import reverse
from ome_zarr.reader import Reader
from ome_zarr.io import parse_url

from omeroweb.testlib import IWebTest, get, get_json
from omero.gateway import BlitzGateway


def get_connection(user, group_id=None):
    """Get a BlitzGateway connection for the given user's client."""
    connection = BlitzGateway(client_obj=user[0])
    # Refresh the session context
    connection.getEventContext()
    if group_id is not None:
        connection.SERVICE_OPTS.setOmeroGroup(group_id)
    return connection


class TestNgff(IWebTest):
    """Tests OME-NGFF urls"""

    @pytest.fixture()
    def user1(self):
        """Return a new user in a read-annotate group."""
        group = self.new_group(perms='rwra--')
        user = self.new_client_and_user(group=group)
        return user

    def test_zarr_index(self, user1):
        """Test we can access omero-web"""
        conn = get_connection(user1)
        user_name = conn.getUser().getName()
        django_client = self.new_django_client(user_name, user_name)
        index_url = reverse('omero_web_zarr_index')
        rsp = get(django_client, index_url)
        assert rsp is not None

    @pytest.mark.parametrize("version", ("0.3", "0.4"))
    def test_image_zarr(self, user1, tmpdir, version):

        size_x = 100
        size_y = 200
        size_z = 1
        size_c = 1
        size_t = 1

        conn = get_connection(user1)
        user_name = conn.getUser().getName()
        django_client = self.new_django_client(user_name, user_name)

        image = self.create_test_image(
            session=conn.c.sf, size_x=size_x, size_y=size_y,
            size_z=size_z, size_c=size_c, size_t=size_t)
        image_id = image.id.val

        kwargs = {"iid": image_id, "version": version}
        zattrs_url = reverse('zarr_image_zattrs', kwargs=kwargs)
        zattrs_json = get_json(django_client, zattrs_url)
        assert(len(zattrs_json["multiscales"]) == 1)

        zgroup_url = reverse('zarr_image_zgroup', kwargs=kwargs)
        zgroup_json = get_json(django_client, zgroup_url)
        assert zgroup_json["zarr_format"] == 2

        zarray_url = reverse('zarr_image_zarray',
                             kwargs={**kwargs, "level": 0})
        zarray_json = get_json(django_client, zarray_url)
        assert zarray_json["shape"] == [size_y, size_x]

        # write json to disk in tmpdir
        os.makedirs(tmpdir.join("0"))
        json_data = [zattrs_json, zgroup_json, zarray_json]
        file_names = [".zattrs", ".zgroup", "0/.zarray"]
        for data, name in zip(json_data, file_names):
            with open(tmpdir.join(name), 'w') as f:
                f.write(json.dumps(data))

        # 2D image
        chunk = "0/0"
        chunk_url = reverse("zarr_image_chunk",
                            kwargs={**kwargs,
                                    "level": 0,
                                    "chunk": chunk})
        rsp = get(django_client, chunk_url)
        chunk_data = rsp.content
        os.makedirs(tmpdir.join(chunk))
        # write chunk to disk
        with open(str(tmpdir.join(chunk, "0")), 'wb') as f:
            f.write(chunk_data)

        # check shape - reading pixel data fails: all 0?
        zarr_image = zarr.open(str(tmpdir), mode='r')
        assert zarr_image['0'].shape == (size_y, size_x)

        # Open with ome-zarr to check we have data
        z = parse_url(str(tmpdir))
        reader = Reader(z)
        for n in reader():
            assert n.data[0].max().compute() > 0
