# coding=utf-8
"""Tools for configuration and set up of docker.

.. seealso:: http://www.docker.io/
     and http://docs.docker.io/en/latest/installation/
     ubuntulinux/#ubuntu-precise-12-04-lts-64-bit

As the second article mentions, for ubuntu 12.04 the kernel needs to be
upgraded to 3.8 - which the setup task will do.
"""

from fabric.api import run, sudo, task, fastprint, env, prompt, reboot
from fabric.colors import red, green, blue, yellow
from fabtools.deb import update_index as apt_get_update
from fabtools.require.deb import ppa as require_ppa
from fabtools.require.deb import package as require_package
from fabtools.require.deb import packages as require_packages
from fabtools.deb import is_installed


@task
def setup_docker():
    """Setup docker on the target host."""
    fastprint(yellow('Setting up docker on host: %s' % env.host))
    if is_installed('lxc-docker'):
        fastprint(green(
            'This system already appears to have docker installed on it'))
        return
    version = run('uname -r')
    if '3.2' in version:
        # LTS 3.2 version is too old so we install a backported one
        # see http://docs.docker.io/en/latest/installation/ubuntulinux/
        # #ubuntu-precise-12-04-lts-64-bit
        fastprint(red('Upgrading kernel to 3.8!\n'))
        response = prompt('Do you wish to continue? y/n :')
        if response != 'y':
            fastprint(red('Docker install aborted by user.'))
            return
        fastprint(blue('Ok upgrading kernel.'))
        require_packages([
            'linux-image-generic-lts-raring',
            'linux-headers-generic-lts-raring'])
        fastprint(red('\nWe need to reboot the system now!\n'))
        response = prompt('Do you wish to continue? y/n :')
        if response is not None:
            reboot()
    else:
        require_package('linux-image-extra-%s' % version)
    require_ppa('ppa:dotcloud/lxc-docker')
    apt_get_update()
    require_packages([
        'software-properties-common',
        'lxc-docker'])
    start_docker_daemon()
    run('docker pull base')
    fastprint(green('Installation of oracle java completed ok!'))


@task
def start_docker_daemon():
    """Start the docker daemon."""
    fastprint(yellow('Starting docker on host: %s' % env.host))
    sudo('docker -d &')


@task
def create_docker_container():
    """Create a docker container."""
    run('docker run -i -t base /bin/bash')
