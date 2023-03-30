.. image:: https://github.com/ome/omero-web-zarr/workflows/OMERO/badge.svg
    :target: https://github.com/ome/omero-web-zarr/actions

.. image:: https://badge.fury.io/py/omero-web-zarr.svg
    :target: https://badge.fury.io/py/omero-web-zarr

omero-web-zarr
==============
Implementation of OME-Zarr API with an omero-web app


Requirements
------------

* OMERO.web 5.6 or newer.
* Python 3.6 or newer.

Installation
------------

This section assumes that an OMERO.web is already installed.

::

    $ pip install omero-web-zarr

To install for development, run:

::

    $ pip install -e .

Configuration settings:

::

    $ omero config append omero.web.apps '"omero_web_zarr"'

    # Allow to open-with Vizarr

    $ omero config append omero.web.open_with '["web_zarr_vizarr", "omero_web_zarr_index", {"supported_objects":["image"], "label": "Vizarr", "script_url": "omero_web_zarr/openwith.js"}]'

Restart OMERO.web in the usual way.

::

    $ omero web restart


This appli self-hosts Vizarr to avoid CORS issues (delegating to https://hms-dbmi.github.io/vizarr/).

In the webclient UI you can use the context menu to `Open With > Vizarr`, or use your Image ID and go directly to:

::

    [omero-server]/zarr/vizarr/?source=[omero-server]/zarr/image/[ID].zarr

Release process
---------------

This repository uses `bump2version <https://pypi.org/project/bump2version/>`_ to manage version numbers.

License
-------

This application is released under the AGPL.

Copyright
---------

2021-2022, The Open Microscopy Environment
