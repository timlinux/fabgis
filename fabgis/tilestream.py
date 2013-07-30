# coding=utf-8
"""Tools for deployment of tilestream.

.. note:: Usually you should run tilemill on your local host and prepare your
    mbtiles, then use tilestream (https://github.com/mapbox/tilestream) to
    host the resulting mbtiles output.

.. seealso:: :file:`tilemill.py`

"""
import fabtools
from fabric.api import fastprint, task, sudo, run, cd
from .common import setup_env


@task
def setup_tilestream():
    """Set up tile stream - see https://github.com/mapbox/tilestream."""
    setup_env()
    fabtools.require.deb.package('curl')
    fabtools.require.deb.package('build-essential')
    fabtools.require.deb.package('libssl-dev')
    fabtools.require.deb.package('libsqlite3-0')
    fabtools.require.deb.package('libsqlite3-dev')
    fabtools.require.deb.package('git-core')
    fabtools.require.deb.package('nodejs nodejs-dev npm')
    run('git clone https://github.com/mapbox/tilestream.git')

@task
def start_tilestream():
    """Start the tilestream service - ensure it is installed first."""
    sudo('start tilemill')
    fastprint('You may need to port forward to port 20009 or set up your '
              'vagrant instance to do so....')

    with cd('tilestream'):
        run('npm install')
        run('./index.js')

