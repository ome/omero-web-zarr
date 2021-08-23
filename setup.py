from setuptools import setup, find_packages

setup(
    name='omero-web-zarr',
    version='0.0.1',
    description="OMERO.web plugin for OME-Zarr",
    packages=find_packages(),
    keywords=['omero', 'zarr', 'ome', 'web'],
    install_requires=['zarr'],
    include_package_data=True,
)
