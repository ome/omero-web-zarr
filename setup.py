from setuptools import setup, find_packages

VERSION = '0.1.0.dev0'

setup(
    name='omero-web-zarr',
    version=VERSION,
    description="OMERO.web plugin for OME-Zarr",
    packages=find_packages(),
    keywords=['omero', 'zarr', 'ome', 'web'],
    install_requires=['zarr'],
    include_package_data=True,
)
