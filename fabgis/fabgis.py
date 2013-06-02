from fabric.api import env, task
import fabtools


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


@task
def add_ubuntugis_ppa():
    """Ensure we have ubuntu-gis repo."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.ppa(
        #'ppa:ubuntugis/ubuntugis-unstable', auto_yes=True)
        'ppa:ubuntugis/ubuntugis-unstable')


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
