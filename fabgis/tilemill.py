# coding=utf-8
"""
Tools for deployment of tilemill.
=================================

.. note:: Usually you should run tilemill on your local host and prepare your
    mbtiles, then use tilestream (https://github.com/mapbox/tilestream) to
    host the resulting mbtiles output.

.. seealso:: :file:`tilestream.py`

"""
import os
import fabtools
from fabric.api import fastprint, task, run, env, cd, prefix
from fabric.colors import green
from .common import setup_env
from .system import get_ip_address
from .git import update_git_checkout
from .node import setup_node


@task
def add_developmentseed_ppa():
    """Ensure we have development seed ppa (makers of mapbox, tilemill etc.."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.ppa(
        #'ppa:developmentseed/mapbox', auto_yes=True)
        'ppa:developmentseed/mapbox')


@task
def setup_tilemill(proxy_url=None):
    """Set up tile mill - see http://www.mapbox.com/tilemill/ .

    We use a pure node setup as described here:

    https://github.com/mapbox/tilemill/issues/2103#issuecomment-37473991

    in order to avoid potential conflicts with ubuntugis.

    :param proxy_url: Optional parameters to specify the url to use for your
        network proxy. It should be specified in the form: ``<host>:<port>``.
        The same proxy will be used for both http and https urls. If ommitted
        no proxy will be used.
    :type proxy_url: str
    """
    # Note raring seems not to be supported yet...
    setup_env()
    repo_alias = 'tilemill'
    print env
    update_git_checkout(
        env.fg.workspace, 'https://github.com/mapbox/tilemill.git', repo_alias)
    work_path = os.path.join(env.fg.workspace, repo_alias)
    setup_node(
        work_path,
        node_version='0.10.26',  # known good version
        proxy_url=proxy_url)

    with cd(work_path):
        run('env/bin/npm install')
    fastprint(green(
        'Tilemill installed. Use the start_tilemill task to run it.'))

@task
def start_tilemill():
    """Start the tilemill service - ensure it is installed first."""
    repo_alias = 'tilemill'
    work_path = os.path.join(env.fg.workspace, repo_alias)
    host_ip = get_ip_address()
    with cd(work_path):
        command = (
            'PATH=$PATH:env/bin nohup index.js '
            '--server=true '
            '--listenHost=0.0.0.0 '
            '--coreUrl=%s:20009 '
            '--tileUrl=%s:20008 &' % (host_ip, host_ip))
        run(command)
    fastprint('Tilemill is running - point your browser at:')
    fastprint('http://%s:20009' % host_ip)
    fastprint('to use it.')
