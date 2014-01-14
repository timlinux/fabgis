# coding=utf-8
"""
Tools relating to the use of python virtualenv.
===============================================

"""

import os
from fabric.api import fastprint, run, cd, task
from fabric.contrib.files import sed
from fabric.colors import blue, green
from fabtools.require.deb import packages as require_packages
from fabtools.require.python import virtualenv

from .common import setup_env


@task
def setup_venv(code_path, requirements_file='requirements.txt'):
    """Initialise or update the virtual environment.

    It will also ensure build-essential is installed, though you may need to
    install required dev library using your own script.

    :param code_path: Base directory under which the venv dir should be made.
    :type code_path: str

    :param requirements_file: Name of the requirements file to use in the
        base directory. Defaults to ``requirements.txt``.
    :type requirements_file: str

    To run e.g.::

        fab -H 192.168.1.1:2222 setup_venv

    """
    setup_env()
    fastprint(blue('Setting up virtual env in: \n%s\nusing\n%s' % (
        code_path, requirements_file)))
    require_packages(['python-virtualenv', 'build-essential'])
    with cd(code_path):
        # Ensure we have a venv set up
        virtualenv('venv')
        run('venv/bin/pip install -r %s' % requirements_file)
    fastprint(green('Virtualenv setup completed.'))


@task
def build_pil(code_path):
    """Build pil with proper support for jpeg etc.

    :param code_path: Directory where the code lives.
    :type code_path: str

    .. note:: Any existing PIL will be uninstalled.

    .. versionadded: 0.16.0
    """
    require_packages(['libjpeg-dev', 'libfreetype6', 'libfreetype6-dev'])

    tcl = 'TCL_ROOT = None'
    jpg = 'JPEG_ROOT = None'
    zlib = 'ZLIB_ROOT = None'
    tiff = 'TIFF_ROOT = None'
    freetype = 'FREETYPE_ROOT = None'

    tcl_value = (
        'TCL_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')
    jpg_value = (
        'JPEG_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')
    zlib_value = (
        'ZLIB_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')
    tiff_value = (
        'TIFF_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')
    freetype_value = (
        'FREETYPE_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')

    venv = os.path.join(code_path, 'venv')
    with cd(venv):
        run('bin/pip uninstall pil')
        run('wget -c http://effbot.org/downloads/Imaging-1.1.7.tar.gz')
        run('tar xfz Imaging-1.1.7.tar.gz')
        with cd(os.path.join(venv, 'Imaging-1.1.7')):
            sed('setup.py', tcl, tcl_value)
            sed('setup.py', jpg, jpg_value)
            sed('setup.py', zlib, zlib_value)
            sed('setup.py', tiff, tiff_value)
            sed('setup.py', freetype, freetype_value)
            run('../bin/python setup.py install')


@task
def build_python_gdal(code_path):
    """Build python gdal in a virtualenv etc.

    :param code_path: Directory where the code lives.
    :type code_path: str

    .. note:: Any existing GDAL will be uninstalled.

    .. versionadded: 0.16.0
    """

    # Gdal does not build cleanly from requirements so we follow advice
    # from http://ubuntuforums.org/showthread.php?t=1769445
    pip_path = os.path.join(code_path, 'venv', 'bin', 'pip')
    gdal_build_path = os.path.join(code_path, 'venv', 'build', 'GDAL')

    result = run('%s install --no-install GDAL' % pip_path)
    if 'Requirement already satisfied ' not in result:
        with cd(gdal_build_path):
            run('python setup.py build_ext --include-dirs=/usr/include/gdal')
            run('%s install --no-download GDAL' % pip_path)
