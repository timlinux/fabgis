# coding=utf-8
"""
Tasks for setting up InaSAFE.
=============================

"""

import os
from fabric.api import task, fastprint, env
from fabric.colors import blue, green
import fabtools
from .system import setup_qt4_developer_tools, setup_ccache
from .git import update_git_checkout
from .qgis import install_qgis2


@task
def setup_inasafe():
    """Setup requirements for InaSAFE."""
    fastprint(blue('Setting up InaSAFE dependencies\n'))
    setup_qt4_developer_tools()
    setup_ccache()
    install_qgis2()
    fabtools.require.deb.packages([
        'pep8',
        'pylint',
        'python-nose',
        'python-nosexcover',
        'python-pip',
        'python-numpy',
        'python-qt4',
        'python-nose',
        'gdal-bin',
        'rsync',
        'python-coverage',
        'python-gdal',
        'pyqt4-dev-tools',
        'pyflakes',

    ])
    code_path = os.path.join('home', env.user, 'dev', 'python')

    update_git_checkout(
        code_path=code_path,
        url='git://github.com/AIFDR/inasafe.git',
        repo_alias='inasafe-dev',
        branch='master'
    )
    update_git_checkout(
        code_path=code_path,
        url='git://github.com/AIFDR/inasafe_data.git',
        repo_alias='inasafe_data',
        branch='master'
    )
    update_git_checkout(
        code_path=code_path,
        url='git://github.com/AIFDR/inasafe-doc.git',
        repo_alias='inasafe-doc',
        branch='develop'
    )
    fastprint(green('Setting up InaSAFE dependencies completed.\n'))
    fastprint(green('You should now have checkouts of inasafe-dev, \n'))
    fastprint(green('inasafe_data and insafe-doc in your dev/python dir.\n'))
