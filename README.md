# omero-web-zarr
Implementation of OME-Zarr API with an omero-web app.

Currently this app only supports OME-NGFF v0.1.
For a given Image ID in OMERO, the following URL will refer to an OME-NGFF image:

    https://[omero-server]/zarr/image/ID.zarr/

NB: This app has not been extensively testing and should not be considered "production ready".


# Dev Install

Install with:

    $ pip install -e .

Config:

    $ omero config append omero.web.apps '"omero_web_zarr"'

    # Allow to open-with Vizarr

    $ omero config append omero.web.open_with '["web_zarr_vizarr", "omero_web_zarr_index", {"supported_objects":["image"], "label": "Vizarr", "script_url": "omero_web_zarr/openwith.js"}]'


This app self-hosts Vizarr to avoid CORS issues (delegating to https://hms-dbmi.github.io/vizarr/).

In the webclient UI you can use the context menu to `Open With > Vizarr`, or use your Image ID and go directly to:

    [omero-server]/zarr/vizarr/?source=[omero-server]/zarr/image/[ID].zarr
