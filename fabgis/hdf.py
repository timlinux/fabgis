# coding=utf-8
"""Helpers for installing hdf5"""

import fabtools
from fabric.contrib.files import exists
from fabric.api import fastprint, run, cd, env, task, sudo, settings

from .system import setup_ccache
from .common import setup_env
from .utilities import append_if_not_present


@task
def build_hdf5(version='1.8.11'):
    """Get proj4 from tarball and build it.

    :param version: hdf5 version to build. The version should be consistent
        with a downloadable tar file from the project web site. Default is
        the current stable release.
    :type version: str
    """
    setup_env()
    fabtools.require.deb.package('build-essential')
    setup_ccache()

    code_base = '%s/cpp' % env.fg.workspace
    filename = 'hdf5-%s' % version
    source_url = (
        'http://www.hdfgroup.org/ftp/HDF5/current/src/%s.tar.gz' %
        filename)
    code_path = '%s/%s' % (code_base, filename)

    if not exists(code_path):
        fastprint('Extracted tarball does not exist, creating.')
        with cd(code_base):
            if exists('%s.tar.gz' % filename):
                run('rm %s.tar.gz' % filename)
            run('wget %s' % source_url)
            run('tar xfz %s.tar.gz' % filename)

    processor_count = run('cat /proc/cpuinfo | grep processor | wc -l')

    with cd(code_path):
        # Dont fail if make clean does not work
        with settings(warn_only=True):
            run('make clean')
        run('./configure')
        run('make -j %s' % processor_count)
        sudo('make install')
    # Write to ld path too so libs are loaded nicely
    ld_file = '/etc/ld.so.conf.d/usr_local_lib.conf'
    with settings(warn_only=True):
        sudo('rm %s' % ld_file)
    append_if_not_present(ld_file, '/usr/local/lib', use_sudo=True)
    sudo('ldconfig')
