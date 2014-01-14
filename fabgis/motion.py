# coding=utf-8
"""
Motion Web Cam related tasks.
=============================

This module provides tools for setting up the motion web cam daemon.

http://www.lavrsen.dk/foswiki/bin/view/Motion/WebHome

"""
import os
from fabgis.fabgis import sed
from fabric.api import cd, task, sudo, fastprint, run
from fabric.colors import green
from fabric.contrib.files import upload_template
from fabtools import require
from .common import setup_env


@task
def setup_motion(email):
    """Set up the motion web cam daemon.

    :param email: Email address to send motion alerts to.
    :type email: str

    """
    require.deb.package('motion')
    require.deb.package('mpack')
    sed(
        '/etc/default/motion',
        'start_motion_daemon=no',
        'start_motion_daemon=yes',
        use_sudo=True)
    sed(
        '/etc/default/motion',
        '; on_movie_end value',
        ('on_movie_end mpack -s \'[Motion Alert] %%Y-%%m-%%d %%H:%%M:%%S\' '
         '/tmp/motion/%f %s' % email),
        use_sudo=True)
    require.service.restarted('motion')


@task
def setup_apache(
        site_name,
        web_root,
        template_dir=None,
        **kwargs):
    """Set up the apache server for this site.

    :param site_name: Name of the site e.g. cam.linfiniti.com. Should be a
        single word with only alpha characters in it.
    :type site_name: str

    :param web_root: Directory where the content lives.
    :type web_root: str

    :param template_dir: Directory where the template files live. If none
        will default to ``resources/server_config/apache``. Must be a
        relative path to the fabfile you are running.
    :type template_dir: str

    :param kwargs: Any extra keyword arguments that should be appended to the
        token list that will be used when rendering the apache config template.
        Use this to pass in sensitive data such as passwords.
    :type kwargs: dict

    :returns: Path to the apache conf file.
    :rtype: str
    """
    setup_env()
    # Ensure we have a mailserver setup for our domain
    # Note that you may have problems if you intend to run more than one
    # site from the same server
    require.postfix.server(site_name)

    # Clone and replace tokens in apache conf
    if template_dir is None:
        template_dir = 'resources/server_config/apache/'
    filename = '%s.apache.conf.templ' % site_name
    template_path = os.path.join(template_dir, filename)
    fastprint(green('Using %s for template' % template_path))

    context = {
        'escaped_server_name': site_name.replace('.', '\.'),
        'server_name': site_name,
        'web_root': web_root,
        'site_name': site_name}
    context.update(kwargs)  # merge in any params passed in to this function
    destination = '/etc/apache2/sites-available/%s.apache.conf' % site_name
    fastprint(context)

    upload_template(
        template_path,
        destination,
        context=context,
        use_sudo=True)

    require.deb.package('apache2')
    sudo('a2dissite default')
    sudo('a2ensite %s.apache.conf' % site_name)
    # Check if apache configs are ok - script will abort if not ok
    sudo('/usr/sbin/apache2ctl configtest')
    require.service.restarted('apache2')
    return destination
