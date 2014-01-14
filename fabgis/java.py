# coding=utf-8
"""
Tasks for install and setup of java.
====================================

"""

from fabric.api import run, sudo, task, fastprint, env
from fabric.colors import red, green, blue, yellow
from fabtools.deb import update_index as apt_get_update
from fabtools.require.deb import ppa as require_ppa
from fabtools.require.deb import package as require_package


@task
def install_oracle_jdk():
    """Install the official oracle jdk."""
    fastprint(yellow('Setting up oracle java on host: %s' % env.host))
    require_ppa('ppa:webupd8team/java')
    apt_get_update()
    require_package('software-properties-common')
    sudo(
        'echo oracle-java7-installer shared/accepted-oracle-license-v1-1 '
        'select true | debconf-set-selections')
    require_package('oracle-java7-installer')
    fastprint(green('Installation of oracle java completed ok!'))

