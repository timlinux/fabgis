# coding=utf-8
"""Tools for deployment of tilestream.

.. note:: Usually you should run tilemill on your local host and prepare your
    mbtiles, then use tilestream (https://github.com/mapbox/tilestream) to
    host the resulting mbtiles output.

.. seealso:: :file:`tilemill.py`

"""
import os

from fabric.api import fastprint, task, sudo, run, cd, env
import fabtools
from fabtools.files import exists
from fabtools import require
from .common import setup_env


@task
def setup_tilestream():
    """Set up tile stream - see https://github.com/mapbox/tilestream.

    This one deserves a little explanation:

    Tilestream is a nodejs application. Node seems to be pretty unparticular
    about maintaining api compatibility between releases so if you grab one
    from e.g. apt, chances are it won't work with tilestream.

    To address this, we use the nodeenv virtualisation environment (somewhat
    equivalent to using python virtualenv) to ensure that we have the
    expected version of tilestream. e.g.::

        nodeenv env --node=0.8.15
    """
    setup_env()
    require.deb.package('curl')
    require.deb.package('build-essential')
    require.deb.package('libssl-dev')
    require.deb.package('libsqlite3-0')
    require.deb.package('libsqlite3-dev')
    require.deb.package('git-core')
    require.deb.package('nodejs nodejs-dev npm')
    require.deb.package('python-pip')

    sudo('pip install nodeenv')

    dev_dir = '/home/%s/dev/javascript' % env.fg.user
    fastprint('making directory %s' % dev_dir)
    require.directory(dev_dir)

    tile_stream_dir = os.path.join(dev_dir, 'tilestream')
    fastprint('checkout out tilestream to %s' % tile_stream_dir)

    if not exists(tile_stream_dir):
        with cd(dev_dir):
            run('git clone http://github.com/mapbox/tilestream.git')

    with cd(tile_stream_dir):
        if not exists(os.path.join(tile_stream_dir, 'env')):
            run('nodeenv env --node=0.8.15')
        # If doing this interactively from a shell you would first do:
        # . env/bin/activate
        # npm install
        # From our scripted environment (where we cant activate the venv):
        run('env/bin/npm install')


@task
def start_tilestream(tile_dir=None, ui_port=8888, tiles_port=8888, host=None):
    """Start the tilestream service - ensure it is installed first.

    :param tile_dir: Optional directory on the remote host that holds one or
        more mbtiles files to be published. If ommitted the default of
        `~/Documents/MapBox/tiles` will be used by tilestream.
    :type tile_dir: str

    :param ui_port: Port on which the tilestream ui should be available.
    :type ui_port: int

    :param tiles_port: Port on which tilestream tile service should be
        available. You may want to use a different port here and then run a
        CDN such as cloudflare in front of the tile service.
    :type tiles_port: int

    :param host: Host name under which the service will run. Must match the
        hostname to which requests are made (even if you run it behind mod
        proxy).
    :type host: str

    Example invocation of tilestream with all the bells and whistles::

        start --host = 41.74.158.13 \
            --accesslog = /tmp/tilestream.log \
            --uiPort=8888 \
            --tilePort = 8889
    """
    setup_env()
    dev_dir = '/home/%s/dev/javascript' % env.fg.user
    tile_stream_dir = os.path.join(dev_dir, 'tilestream')
    with cd(tile_stream_dir):
        params = ''
        if tile_dir is not None:
            params += ' --tiles=%s' % tile_dir
        params += ' --uiPort=%i' % ui_port
        params += ' --tilePort=%i' % tiles_port
        if host is not None:
            params += ' --host=%s' % host
        run('PATH=env/bin:$PATH ./index.js %s' % params)

    fastprint(
        'You may need to port forward to port 8888 or set up your '
        'vagrant instance to do so....')
