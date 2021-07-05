
// Here we configure a url provider. This function will be passed the selected
// objects and the base url that was specified in the 'Open with' configuration above.
OME.setOpenWithUrlProvider("web_zarr_vizarr", function (selected, url) {
    return `${url}vizarr/?source=${url}image/${selected[0].id}.zarr`
});