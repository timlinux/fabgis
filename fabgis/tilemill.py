# coding=utf-8
"""Tools for deployment of tilemill.

.. note:: Usually you should run tilemill on your local host and prepare your
    mbtiles, then use tilestream (https://github.com/mapbox/tilestream) to
    host the resulting mbtiles output.

.. seealso:: :file:`tilestream.py`

"""
import fabtools
from fabric.api import fastprint, task, sudo, run
from .common import setup_env
from .system import get_ip_address


@task
def add_developmentseed_ppa():
    """Ensure we have development seed ppa (makers of mapbox, tilemill etc.."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.ppa(
        #'ppa:developmentseed/mapbox', auto_yes=True)
        'ppa:developmentseed/mapbox')


@task
def setup_tilemill():
    """Set up tile mill - see http://www.mapbox.com/tilemill/ ."""
    # Note raring seems not to be supported yet...
    setup_env()
    add_developmentseed_ppa()
    fabtools.require.deb.package('tilemill')
    fabtools.require.deb.package('libmapnik')
    # TODO: switch to using nodeenv
    # SEE: https://github.com/ekalinin/nodeenv
    fabtools.require.deb.package('nodejs')
    fastprint('Now you can log in and use tilemill like this:')
    fastprint('vagrant ssh -- -X')
    fastprint('/usr/bin/nodejs /usr/share/tilemill/index.js')
    fastprint('Or use the start tilemill task and open your')
    fastprint('browser at the url provided.')


@task
def start_tilemill():
    """Start the tilemill service - ensure it is installed first."""
    #sudo('start tilemill')
    # Note port forward seems not to work well
    # Using this config on the vhost:
    #{
    #  'listenHost': '0.0.0.0',
    #  'coreUrl': '192.168.1.115:20009',
    #  'tileUrl': '192.168.1.115:20008',
    #  'files': '/usr/share/mapbox',
    #  'server': true
    #}
    # Worked, accessible from http://192.168.1.115:20009/
    # More reliable way (blocking process, ctl-c to kill)
    host_ip = get_ip_address()
    fastprint(host_ip)
    command = (
        '/usr/bin/nodejs /usr/share/tilemill/index.js '
        '--server=true '
        '--listenHost=0.0.0.0 '
        '--coreUrl=%s:20009 '
        '--tileUrl=%s:20008' % (host_ip, host_ip))
    run(command)
    fastprint('Tilemill is running - point your browser at:')
    fastprint('http://%s:20009' % host_ip)
    fastprint('to use it.')
