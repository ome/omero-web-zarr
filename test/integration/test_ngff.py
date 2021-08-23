#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2021 University of Dundee & Open Microscopy Environment.
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

"""Integration tests for testing saving and loading figure files."""

from omeroweb.testlib import IWebTest, get, get_json
import pytest
from django.core.urlresolvers import reverse
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

    def test_image_zarr(self, user1):

        size_x = 100
        size_y = 200
        size_z = 5
        size_c = 2
        size_t = 4

        conn = get_connection(user1)
        user_name = conn.getUser().getName()
        django_client = self.new_django_client(user_name, user_name)

        image = self.create_test_image(session=conn.c.sf, size_x=size_x, size_y=size_y,
                                       size_z=size_z, size_c=size_c, size_t=size_t)
        image_id = image.id.val

        zattrs_url = reverse('zarr_image_zattrs', kwargs={"iid": image_id})
        zattrs_json = get_json(django_client, zattrs_url)
        assert(len(zattrs_json["multiscales"]) == 1)

        zgroup_url = reverse('zarr_image_zgroup', kwargs={"iid": image_id})
        zgroup_json = get_json(django_client, zgroup_url)
        assert zgroup_json["zarr_format"] == 2

        zarray_url = reverse('zarr_image_zarray', kwargs={"iid": image_id, "level": 0})
        zarray_json = get_json(django_client, zarray_url)
        assert zarray_json["shape"] == [size_t, size_c, size_z, size_y, size_x]
