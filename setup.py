from setuptools import setup, find_packages

def read(fname):
    """
    Utility function to read the README file.
    :rtype : String
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

VERSION = '0.1.0.dev0'

setup(
    name='omero-web-zarr',
    version=VERSION,
    description="OMERO.web plugin for OME-Zarr",
    long_description=read("README.rst")
    classifiers=[
          'Environment :: Web Environment',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Internet :: WWW/HTTP :: WSGI',
      ],  # Get strings from
          # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    author="The Open Microscopy Team",
    author_email="ome-devel@lists.openmicroscopy.org.uk",
    license='AGPL-3.0',
    url="https://github.com/ome/omero-web-zarr/",
    download_url='https://github.com/ome/omero-web-zarr/archive/v%s.tar.gz' % VERSION,  # NOQA
    packages=find_packages(),
    keywords=['omero', 'zarr', 'ome', 'web'],
    install_requires=['zarr'],
    python_requires='>=3',
    include_package_data=True,
    zip_safe=False,
)
