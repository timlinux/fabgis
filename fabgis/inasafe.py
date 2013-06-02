from fabric.api import task
import fabtools


@task
def setup_inasafe():
    """Setup requirements for InaSAFE."""
    fabtools.require.deb.package('pep8')
    fabtools.require.deb.package('pylint')
    fabtools.require.deb.package('python-nose')
    fabtools.require.deb.package('python-nosexcover')
    fabtools.require.deb.package('python-pip')
    fabtools.require.deb.package('python-numpy')
    fabtools.require.deb.package('python-qt4')
    fabtools.require.deb.package('python-nose')
