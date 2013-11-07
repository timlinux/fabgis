# coding=utf-8
"""Tasks for setting up InaSAFE."""

from fabric.api import task, fastprint
from fabric.colors import blue, green
import fabtools


@task
def setup_inasafe():
    """Setup requirements for InaSAFE."""
    fastprint(blue('Setting up InaSAFE dependencies\n'))
    fabtools.require.deb.package('pep8')
    fabtools.require.deb.package('pylint')
    fabtools.require.deb.package('python-nose')
    fabtools.require.deb.package('python-nosexcover')
    fabtools.require.deb.package('python-pip')
    fabtools.require.deb.package('python-numpy')
    fabtools.require.deb.package('python-qt4')
    fabtools.require.deb.package('python-nose')
    fastprint(green('Setting up InaSAFE dependencies completed.\n'))
