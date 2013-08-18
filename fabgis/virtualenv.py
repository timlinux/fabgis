# coding=utf-8
"""Tools relating tot he use of python virtualenv."""

from fabric.api import fastprint, run, cd, task
from fabric.colors import blue, green
from fabtools.require.deb import packages as require_packages
from fabtools.require.python import virtualenv

from .common import setup_env


@task
def setup_venv(code_path, requirements_file='requirements.txt'):
    """Initialise or update the virtual environment.

    It will also ensure build-essential is installed, though you may need to
    install required dev library using your own script.

    :param code_path: Base directory under which the venv dir should be made.
    :type code_path: str

    :param requirements_file: Name of the requirements file to use in the
        base directory. Defaults to ``requirements.txt``.
    :type requirements_file: str

    To run e.g.::

        fab -H 192.168.1.1:2222 setup_venv

    """
    setup_env()
    fastprint(blue('Setting up virtual env in: \n%s\nusing\n%s' % (
        code_path, requirements_file)))
    require_packages(['python-virtualenv', 'build-essential'])
    with cd(code_path):
        # Ensure we have a venv set up
        virtualenv('venv')
        run('venv/bin/pip install -r %s' % requirements_file)
    fastprint(green('Virtualenv setup completed.'))
