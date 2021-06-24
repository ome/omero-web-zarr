# omero-web-zarr
Implementation of OME-Zarr API with an omero-web app


# Dev Install

Install with:

    $ pip install -e .

Config:

    $ omero config append omero.web.apps '"omero_web_zarr"'


Then open an image in Vizarr:

https://hms-dbmi.github.io/vizarr/?source=[YOUR-SERVER]/zarr/image/[IMAGEID].zarr

However, this currently only works if the Image is publicly accessible.
In order for Vizarr to use an existing login, it needs to use `fetch()` with
`{ credentials: 'include' }`. A PR to propose this is in progress at:

https://github.com/hms-dbmi/vizarr/pull/99

NB: However, even with that PR, when connecting from Vizarr hosted on `https` we
can't pass credentials to a regular `http` OMERO host.

E.g. testing locally with this fails:

https://deploy-preview-99--vizarr.netlify.app/?source=http://localhost:4080/zarr/image/2566.zarr
