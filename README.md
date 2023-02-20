# omero-web-zarr

Implementation of [OME-NGFF](https://ngff.openmicroscopy.org/latest/) API with an omero-web app.

Currently this app only supports OME-NGFF v0.1.
For a given Image ID in OMERO, the following URL will refer to an OME-NGFF image:

    https://[omero-server]/zarr/image/ID.zarr/

NB: This app has not been extensively testing and should not be considered "production ready".

Currently supports [OME-NGFF v0.3](https://ngff.openmicroscopy.org/0.3/index.html) and
[OME-NGFF v0.4](https://ngff.openmicroscopy.org/0.4/index.html).

# Dev Install

Install with:

    $ pip install -e .

Config:

    $ omero config append omero.web.apps '"omero_web_zarr"'

    # Allow to open-with Vizarr

    $ omero config append omero.web.open_with '["web_zarr_vizarr", "omero_web_zarr_index", {"supported_objects":["image"], "label": "Vizarr", "script_url": "omero_web_zarr/openwith.js"}]'

    # Open with ome-ngff-validator

    $ omero config append omero.web.open_with '["web_zarr_validator", "omero_web_zarr_index", {"supported_objects":["image"], "label": "NGFF validator", "script_url": "omero_web_zarr/openwith_validator.js"}]'


Then you will be able to access OMERO Images in OME-NGFF format v0.3 or v0.4 with a URLs like:

    # base URL for Image ID
    [omero-server]/zarr/v0.4/image/[ID].zarr

    # URLS for .zattrs, .zgroup
    [omero-server]/zarr/v0.4/image/[ID].zarr/.zattrs
    [omero-server]/zarr/v0.4/image/[ID].zarr/.zgroup

    # .zarray of the dataset at path '0'
    [omero-server]/zarr/v0.4/image/[ID].zarr/0/.zarray

    # first 3D chunk of the dataset at path '0'
    [omero-server]/zarr/v0.4/image/[ID].zarr/0/0/0/0


You can see this in action using the [Vizarr](https://github.com/hms-dbmi/vizarr/) viewer.

This omero-web app self-hosts Vizarr to avoid CORS issues (delegating to https://hms-dbmi.github.io/vizarr/).

In the webclient UI you can use the context menu to `Open With > Vizarr`, or use your Image ID and go directly to:

    [omero-server]/zarr/vizarr/?source=[omero-server]/zarr/v0.4/image/[ID].zarr

# Testing

To run integration tests (in your omero-web conda environment above) with `pytest`.
See [OMERO testing docs](https://docs.openmicroscopy.org/latest/omero/developers/testing.html)
for setting `ICE_CONFIG` and dependencies etc, then:

    $ pytest test/integration/test_ngff.py
