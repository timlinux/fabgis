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

    We prefer from pip as ubuntu packages are usually old."""
    sudo('pip install sphinx')


@task
def setup_transifex():
    """Install transifex client."""
    sudo('pip install transifex-client')

