# omero-web-zarr
Implementation of [OME-NGFF](https://ngff.openmicroscopy.org/latest/) API with an omero-web app.

Currently supports [OME-NGFF v0.3](https://ngff.openmicroscopy.org/0.2/index.html).

# Dev Install

Install with:

    $ pip install -e .

Config:

    $ omero config append omero.web.apps '"omero_web_zarr"'

    # Allow to open-with Vizarr

    $ omero config append omero.web.open_with '["web_zarr_vizarr", "omero_web_zarr_index", {"supported_objects":["image"], "label": "Vizarr", "script_url": "omero_web_zarr/openwith.js"}]'

Then you will be able to access OMERO Images in OME-NGFF format with a URL like:

    # base URL for Image ID
    [omero-server]/zarr/image/[ID].zarr

    # URLS for .zattrs, .zgroup, .zarray, chunks
    [omero-server]/zarr/image/[ID].zarr/.zattrs
    [omero-server]/zarr/image/[ID].zarr/.zgroup
    # array of the dataset at path '0'
    [omero-server]/zarr/image/[ID].zarr/0/.zarray
    # 3D chunk of dataset at path '0'
    [omero-server]/zarr/image/[ID].zarr/0/0/0/0


You can see this in action using the [Vizarr](https://github.com/hms-dbmi/vizarr/) viewer.

This omero-web app self-hosts Vizarr to avoid CORS issues (delegating to https://hms-dbmi.github.io/vizarr/).

In the webclient UI you can use the context menu to `Open With > Vizarr`, or use your Image ID and go directly to:

    [omero-server]/zarr/vizarr/?source=/zarr/image/[ID].zarr
