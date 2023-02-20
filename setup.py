
import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as test_command


class PyTest(test_command):

    def initialize_options(self):
        test_command.initialize_options(self)
        self.test_pythonpath = None
        self.test_string = None
        self.test_marker = None
        self.test_path = 'test'
        self.test_failfast = False
        self.test_quiet = False
        self.test_verbose = False
        self.test_no_capture = False
        self.junitxml = None
        self.pdb = False
        self.test_ice_config = None

    def finalize_options(self):
        test_command.finalize_options(self)
        self.test_args = [self.test_path]
        if self.test_string is not None:
            self.test_args.extend(['-k', self.test_string])
        if self.test_marker is not None:
            self.test_args.extend(['-m', self.test_marker])
        if self.test_failfast:
            self.test_args.extend(['-x'])
        if self.test_verbose:
            self.test_args.extend(['-v'])
        if self.test_quiet:
            self.test_args.extend(['-q'])
        if self.junitxml is not None:
            self.test_args.extend(['--junitxml', self.junitxml])
        if self.pdb:
            self.test_args.extend(['--pdb'])
        self.test_suite = True
        if 'ICE_CONFIG' not in os.environ:
            os.environ['ICE_CONFIG'] = self.test_ice_config

    def run_tests(self):
        if self.test_pythonpath is not None:
            sys.path.insert(0, self.test_pythonpath)

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omeroweb.settings")

        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='omero-web-zarr',
    version='0.0.2',
    description="OMERO.web plugin for OME-Zarr",
    packages=find_packages(),
    keywords=['omero', 'zarr', 'ome', 'web'],
    install_requires=['zarr'],
    include_package_data=True,
    cmdclass={'test': PyTest},
    tests_require=['pytest', 'ome_zarr'],
)
