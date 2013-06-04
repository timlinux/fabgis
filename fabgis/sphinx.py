import fabtools
from fabric.api import task, sudo


@task
def setup_latex():
    """Install latex and friends needed to generate sphinx PDFs."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.package('texlive-latex-extra')
    fabtools.require.deb.package('texinfo')
    fabtools.require.deb.package('texlive-fonts-recommended')


@task
def setup_sphinx():
    """Install sphinx from pip.

    We prefer packages from pip as ubuntu packages are usually old.
    To build the Documentation we also need to check and update the
    subjacent docutils installation"""
    if fabtools.is_installed(docutils-common):
        sudo('apt-get remove docutils-common')
    if fabtools.is_installed(docutils-doc):
        sudo('apt-get remove docutils-doc')
    if fabtools.is_installed(python-docutils):
        sudo('apt-get remove python-docutils')
    sudo('pip install --upgrade docutils==0.10')
    sudo('pip install sphinx')


@task
def setup_transifex():
    """Install transifex client."""
    sudo('pip install transifex-client')
