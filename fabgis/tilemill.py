import fabtools
from fabric.api import fastprint, task, sudo
from .common import setup_env


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
    fabtools.require.deb.package('nodejs')


@task
def start_tilemill():
    """Start the tilemill service - ensure it is installed first."""
    sudo('start tilemill')
    fastprint('You may need to port forward to port 20009 or set up your '
              'vagrant instance to do so....')
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
