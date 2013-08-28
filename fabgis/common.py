# coding=utf-8
"""Common helpers to bootstrap fabric."""
import os
from fabric.api import env, task, fastprint, run, hide
from fabric.utils import _AttributeDict as fdict
import fabtools


#TODO Not really used, but potentially useful
env.roledefs = {
    'test': ['localhost'],
    'dev': ['none@none.com'],
    'staging': ['none@none.com'],
    'production': ['none@none.com']
}

# Use ssh config if present
#if os.path.exists('~/.ssh/config'):
env.use_ssh_config = True
env.fg = None


def show_environment():
    """For diagnostics - show any pertinent info about server."""
    setup_env()
    fastprint('\n-------------------------------------------------\n')
    for key, value in env.fg.iteritems():
        fastprint('Key: %s \t\t Value: %s\n' % (key, value))
    fastprint('-------------------------------------------------\n')


def setup_env():
    """Things to do regardless of whether command is local or remote."""
    if env.fg is not None:
        fastprint('Environment already set!\n')
        return

    fastprint('Setting environment!\n')
    env.fg = fdict()
    with hide('output'):
        env.fg.user = run('whoami')
        # Workaround for
        env.fg.hostname = run('hostname')
        # this which fails in docker - see
        # https://github.com/dotcloud/docker/issues/1301
        #env.fg.hostname = fabtools.system.get_hostname()
        env.fg.home = os.path.join('/home/', env.fg.user)
        env.fg.workspace = os.path.join(env.fg.home, 'dev')
        env.fg.inasafe_git_url = 'git://github.com/AIFDR/inasafe.git'
        env.fg.qgis_git_url = 'git://github.com/qgis/Quantum-GIS.git'
        env.fg.kandan_git_url = 'git://github.com/kandanapp/kandan.git'
        env.fg.gdal_svn_url = 'https://svn.osgeo.org/gdal/trunk/gdal'
        env.fg.tilemill_tarball_url = (
            'http://tilemill.s3.amazonaws.com/latest/install-tilemill.tar.gz')
        env.fg.inasafe_checkout_alias = 'inasafe-fabric'
        env.fg.qgis_checkout_alias = 'qgis-fabric'
        env.fg.inasafe_code_path = os.path.join(
            env.fg.workspace, env.fg.inasafe_checkout_alias)
        env.fg.qgis_code_path = os.path.join(
            env.fg.workspace, env.fg.qgis_checkout_alias)


@task
def add_ubuntugis_ppa():
    """Ensure we have ubuntu-gis repo."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.package('software-properties-common')
    fabtools.require.deb.ppa(
        #'ppa:ubuntugis/ubuntugis-unstable', auto_yes=True)
        'ppa:ubuntugis/ubuntugis-unstable')
