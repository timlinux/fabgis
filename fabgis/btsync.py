# coding=utf-8
"""
BTSync related tasks
=====================

Tools for deployment of btsync on a server.

see http://www.bittorrent.com/sync

Tim Sutton, May 2014"""

import os
from fabric.contrib.files import exists
from fabric.api import run, cd, env, task, sudo, fastprint
from fabric.colors import green
from fabtools import require
import fabtools


@task
def install_btsync():
    """Install btsync from ppa."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.package('software-properties-common')
    fabtools.require.deb.ppa('ppa:tuxpoldo/btsync')
    fabtools.require.deb.package('btsync')
    fastprint(green('BTSync installed'))

