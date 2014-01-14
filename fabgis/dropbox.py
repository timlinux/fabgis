# coding=utf-8
"""
Dropbox related tasks.
======================

Helpers for dropbox so that you can easily move gis data to the server."""

import os

from fabric.contrib.files import exists
from fabtools import require

from fabric.api import run, cd, env, task, sudo, put
from .common import setup_env
from .utilities import replace_tokens
from .utilities import append_if_not_present


@task
def setup_dropbox():
    """Setup a headless dropbox installation."""
    setup_env()
    dropbox_url = 'https://www.dropbox.com/download?plat=lnx.x86_64'
    dropbox_cli_url = 'https://www.dropbox.com/download?dl=packages/dropbox.py'

    with cd('~'):
        require.directory('bin')
        with cd('bin'):
            if not exists('dropbox.py'):
                run('wget -O dropbox.py "%s"' % dropbox_cli_url)
                run('chmod +x dropbox.py')
        if not exists('.dropbox-dist'):
            command = 'wget -O - "%s" | tar xzf -' % dropbox_url
            run(command)
        # After you have pasted the link and confirmed the machine account
        # you need to press Ctrl-c which unfortunately also terminates the
        # fabric session. capture=False is an attempt to remedy that.
        run('~/.dropbox-dist/dropboxd')


@task
def setup_dropbox_daemon():
    """Set up dropbox to run on init.d.

    Unfortunately we can't run this as part of initial setup due to the
    control-c issue that prevents us from halting the initial dropboxd
    command needed to set up the dropbox synced account.

    So for example you need to do::

        fab vagrant setup_dropbox

    Then once your account is linked, press Ctrl-c - which will also
    terminate the above fabric job. Then run::

        fab vagrant setup_dropbox_daemon

    """
    setup_env()
    with cd('/etc/init.d/'):
        if not exists('dropbox'):
            local_dir = os.path.dirname(__file__)
            local_file = os.path.abspath(os.path.join(
                local_dir,
                '..',
                'fabgis_resources',
                'server_config',
                'dropbox',
                'dropbox.templ'))
            put(local_file,
                '/etc/init.d/dropbox',
                use_sudo=True)

        my_tokens = {'USER': env.fg.user, }
        replace_tokens('/etc/init.d/dropbox', my_tokens)

    sudo('chmod +x /etc/init.d/dropbox')
    sudo('update-rc.d dropbox defaults')
    start_dropbox()
    dropbox_status()


@task
def start_dropbox():
    """Start the dropbox service."""
    sudo('service dropbox start')


@task
def stop_dropbox():
    """Stop the dropbox service."""
    sudo('service dropbox stop')


@task
def dropbox_status():
    """Check the status of dropbox."""
    run('~/bin/dropbox.py status')
