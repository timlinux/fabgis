import os
from datetime import datetime
from fabric.api import *
from fabric.utils import _AttributeDict as fdict
from fabric.contrib.files import contains, exists, append, sed
import fabtools
# Don't remove even though its unused
from fabtools.vagrant import vagrant
env.roledefs = {
    'test': ['localhost'],
    'dev': ['none@none.com'],
    'staging': ['none@none.com'],
    'production': ['none@none.com']
}

env.fg = None


def all():
    """Things to do regardless of whether command is local or remote."""
    if env.fg is not None:
        fastprint('Environment already set!\n')
        return

    fastprint('Setting environment!\n')
    env.fg = fdict()
    with hide('output'):
        env.fg.user = run('whoami')
        env.fg.hostname = run('hostname')
        env.fg.home = os.path.join('/home/', env.fg.user)
        env.fg.workspace = os.path.join(env.fg.home, 'dev')
        env.fg.inasafe_git_url = 'git://github.com/AIFDR/inasafe.git'
        env.fg.qgis_git_url = 'git://github.com/qgis/Quantum-GIS.git'
        env.fg.inasafe_checkout_alias = 'inasafe-fabric'
        env.fg.qgis_checkout_alias = 'qgis-fabric'
        env.fg.inasafe_code_path = os.path.join(
            env.fg.workspace, env.fg.inasafe_checkout_alias)
        env.fg.qgis_code_path = os.path.join(
            env.fg.workspace, env.fg.qgis_checkout_alias)


@task
def show_environment():
    """For diagnostics - show any pertinent info about server."""
    all()
    fastprint('\n-------------------------------------------------\n')
    for key, value in env.fg.iteritems():
        fastprint('Key: %s \t\t Value: %s' % (key, value))
    fastprint('-------------------------------------------------\n')


def add_ubuntugis_ppa():
    """Ensure we have ubuntu-gis repos."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.ppa(
        'ppa:ubuntugis/ubuntugis-unstable', auto_yes=True)


def clone_qgis(branch='master'):
    """Clone or update QGIS from git.

    :param branch: the name of the branch to build from. Defaults to 'master'
    :type branch: basestring

    :rtype: None
    """
    all()
    fabtools.require.deb.package('git')
    code_base = '%s/dev/cpp' % env.fg.workspace
    code_path = '%s/Quantum-GIS' % code_base
    if not exists(code_path):
        fastprint('Repo checkout does not exist, creating.')
        run('mkdir -p %s' % code_base)
        with cd(code_base):
            run('git clone %s' % env.fg.qgis_git_url)
    else:
        fastprint('Repo checkout does exist, updating.')
        with cd(code_path):
            # Get any updates first
            run('git fetch')
            # Get rid of any local changes
            run('git reset --hard')
            # Get back onto master branch
            run('git checkout master')
            # Remove any local changes in master
            run('git reset --hard')
            # Delete all local branches
            run('git branch | grep -v \* | xargs git branch -D')

    with cd(code_path):
        if branch != 'master':
            run('git branch --track %s origin/%s' % (branch, branch))
            run('git checkout %s' % branch)
        else:
            run('git checkout master')
        run('git pull')


@task
def install_qgis1_8():
    """Install QGIS 1.8 under /usr/local/qgis-1.8."""
    all()
    add_ubuntugis_ppa()
    sudo('apt-get build-dep -y qgis')
    fabtools.require.deb.package('cmake-curses-gui')
    fabtools.require.deb.package('git')
    clone_qgis(branch='release-1_8')
    workspace = '%s/dev/cpp' % env.fg.workspace
    code_path = '%s/Quantum-GIS' % workspace
    build_path = '%s/build-qgis18' % code_path
    build_prefix = '/usr/local/qgis-1.8'
    require.directory(build_path)
    with cd(build_path):
        fabtools.require.directory(
            build_prefix,
            use_sudo=True,
            owner=env.fg.user)
        run('cmake .. -DCMAKE_INSTALL_PREFIX=%s' % build_prefix)
        run('make install')


@task
def install_qgis2():
    """Install QGIS 2 under /usr/local/qgis-master.

    TODO: create one function from this and the 1.8 function above for DRY.

    """
    all()
    add_ubuntugis_ppa()
    sudo('apt-get build-dep -y qgis')
    fabtools.require.deb.package('cmake-curses-gui')
    fabtools.require.deb.package('git')
    clone_qgis(branch='master')
    workspace = '%s/dev/cpp' % env.fg.workspace
    code_path = '%s/Quantum-GIS' % workspace
    build_path = '%s/build-master' % code_path
    build_prefix = '/usr/local/qgis-master'
    require.directory(build_path)
    with cd(build_path):
        fabtools.require.directory(
            build_prefix,
            use_sudo=True,
            owner=env.fg.user)
        run('cmake .. -DCMAKE_INSTALL_PREFIX=%s' % build_prefix)

        run('make install')
