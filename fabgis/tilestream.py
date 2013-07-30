# coding=utf-8
"""Tools for deployment of tilestream.

.. note:: Usually you should run tilemill on your local host and prepare your
    mbtiles, then use tilestream (https://github.com/mapbox/tilestream) to
    host the resulting mbtiles output.

.. seealso:: :file:`tilemill.py`

"""
import os

from fabric.api import fastprint, task, sudo, run, cd
import fabtools
from fabtools.files import exists
from .common import setup_env


@task
def setup_tilestream():
    """Set up tile stream - see https://github.com/mapbox/tilestream.

    This one deserves a little explanation:

    Tilestream is a nodejs application. Node seems to be pretty unparticular
    about maintaining api compatibility between releases so if you grab one
    from e.g. apt, chances are it won't work with tilestream.

    We use the nodeenv virtualisation environment (somewhat equivalent to
    using python virtualenv) to ensure that we have the expected version of
    tilestream. e.g.::

        nodeenv env --node=0.8.15
    """
    setup_env()
    fabtools.require.deb.package('curl')
    fabtools.require.deb.package('build-essential')
    fabtools.require.deb.package('libssl-dev')
    fabtools.require.deb.package('libsqlite3-0')
    fabtools.require.deb.package('libsqlite3-dev')
    fabtools.require.deb.package('git-core')
    fabtools.require.deb.package('nodejs nodejs-dev npm')
    run('git clone https://github.com/mapbox/tilestream.git')

    sudo('pip install nodeenv')

    dev_dir = 'dev/javascript'

    if not exists(dev_dir):
        run('mkdir -p %s' % dev_dir)

    with cd(dev_dir):
        if not exists('tilestream'):
            run('git clone http://github.com/mapbox/tilestream.git')

    tile_stream_dir = os.path.join(dev_dir, 'tilestream')
    with cd(tile_stream_dir):
        run('nodeenv env --node=0.8.15')
        # Dot below is required when used interactively in shell
        # . env/bin/activate
        # npm install
        run('env/bin/npm install')


@task
def start_tilestream():
    """Start the tilestream service - ensure it is installed first."""
    with cd('dev/javascript/tilestream'):
        run('./index.js')

    fastprint(
        'You may need to port forward to port 8888 or set up your '
        'vagrant instance to do so....')
