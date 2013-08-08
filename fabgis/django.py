# coding=utf-8
"""Django related tasks."""

import os
from fabric.api import cd, task, sudo, fastprint, run
from fabric.contrib.files import sed
from fabric.contrib.files import exists
from fabtools import require
from .common import setup_env
from .utilities import replace_tokens


@task
def setup_apache(site_name, code_path, wsgi_user='wsgi'):
    """Set up the apache server for this site.

    :param wsgi_user: Name of user wsgi process should run as. The user will
        be created as needed.
    :type wsgi_user: str

    :param site_name: Name of the site e.g. changelogger. Should be a single
        word with only alpha characters in it.
    :type site_name: str

    :param code_path: Directory where the code lives.
    :type code_path: str

    :returns: Path to the apache conf file.
    :rtype: str
    """
    setup_env()
    # Ensure we have a mailserver setup for our domain
    # Note that you may have problems if you intend to run more than one
    # site from the same server
    require.postfix.server(site_name)
    require.deb.package('libapache2-mod-wsgi')

    # Find out if the wsgi user exists and create it if needed e.g.
    require.user(
        wsgi_user,
        create_group=wsgi_user,
        system=True,
        comment='System user for running the wsgi process under')

    # Clone and replace tokens in apache conf

    conf_file = (
        '%s/resources/server_config/apache/%s.apache.conf.templ' % (
            code_path, site_name))

    tokens = {
        'ESCAPEDSERVERNAME': '%s\.linfiniti\.com' % site_name,
        'SERVERNAME': 'changelog.linfiniti.com',
        'SITEUSER': 'wsgi',
        'CODEPATH': code_path.replace('/', '\/'),
        'SITENAME': site_name}
    fastprint(tokens)
    conf_file = replace_tokens(conf_file, tokens)

    with cd('/etc/apache2/sites-available/'):
        if exists('%s.apache.conf' % site_name):
            sudo('a2dissite %s.apache.conf' % site_name)
            fastprint('Removing old apache2 conf', False)
            sudo('rm %s.apache.conf' % site_name)

        sudo('ln -s %s .' % conf_file)

    media_path = '%s/django_project/core/media' % code_path
    if not exists(media_path):
        sudo('mkdir %s' % media_path)
        sudo('chgrp -R %s %s' % (wsgi_user, media_path))

    sudo('a2ensite %s.apache.conf' % site_name)
    sudo('a2dissite default')
    sudo('a2enmod rewrite')
    # Check if apache configs are ok - script will abort if not ok
    sudo('/usr/sbin/apache2ctl configtest')

    require.service.restarted('apache2')
    return conf_file


@task
def build_pil(code_path):
    """Build pil with proper support for jpeg etc.

    :param code_path: Directory where the code lives.
    :type code_path: str

    .. note:: Any existing PIL will be uninstalled.
    """
    require.deb.package('libjpeg-dev')
    require.deb.package('libfreetype6')
    require.deb.package('libfreetype6-dev')

    tcl = 'TCL_ROOT = None'
    jpg = 'JPEG_ROOT = None'
    zlib = 'ZLIB_ROOT = None'
    tiff = 'TIFF_ROOT = None'
    freetype = 'FREETYPE_ROOT = None'

    tcl_value = (
        'TCL_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')
    jpg_value = (
        'JPEG_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')
    zlib_value = (
        'ZLIB_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')
    tiff_value = (
        'TIFF_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')
    freetype_value = (
        'FREETYPE_ROOT = "/usr/lib/x86_64-linux-gnu/", "/usr/include"')

    venv = os.path.join(code_path, 'venv')
    with cd(venv):
        run('bin/pip uninstall pil')
        run('wget -c http://effbot.org/downloads/Imaging-1.1.7.tar.gz')
        run('tar xfz Imaging-1.1.7.tar.gz')
        with cd(os.path.join(venv, 'Imaging-1.1.7')):
            sed('setup.py', tcl, tcl_value)
            sed('setup.py', jpg, jpg_value)
            sed('setup.py', zlib, zlib_value)
            sed('setup.py', tiff, tiff_value)
            sed('setup.py', freetype, freetype_value)
            run('../bin/python setyp.py install')


