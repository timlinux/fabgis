# coding=utf-8
"""
Django related tasks.
=====================

"""

import os
from fabric.api import cd, task, sudo, fastprint, run
from fabric.colors import green
from fabric.contrib.files import sed, upload_template
from fabric.contrib.files import exists
from fabtools import require, fabtools
from .common import setup_env
from . import virtualenv


@task
def set_media_permissions(code_path, wsgi_user='wsgi', media_dir=None):
    """Set the django media dir so apache can write to it.

    :param code_path: Path to top level deploy dir.
    :type code_path: str
    :param media_dir: Optional dir underneath code_path if media does not live in
        ``<code_path>/django_project/media``. No trailing slash.
    :type media_dir: str
    :param wsgi_user: User that should receive write permissions to the folder.
        Defaults to 'wsgi'.
    :type wsgi_user: str
    """
    if not media_dir:
        media_path = '%s/django_project/media' % code_path
    else:
        media_path = '%s/%s' % (code_path, media_dir)
    if not exists(media_path):
        sudo('mkdir %s' % media_path)
    sudo('chgrp -R %s %s' % (wsgi_user, media_path))


@task
def setup_apache(
        site_name,
        code_path,
        domain,
        template_dir=None,
        media_dir=None,
        wsgi_user='wsgi',
        **kwargs):
    """Set up the apache server for this site.

    :param site_name: Name of the site e.g. changelogger. Should be a single
        word with only alpha characters in it.
    :type site_name: str

    :param code_path: Directory where the code lives. Will be used to set
        media etc permissions.
    :type code_path: str

    :param domain: Domain name. If none will be set to hostname.
    :type domain: str

    :param template_dir: Directory where the template files live. If none
        will default to ``resources/server_config/apache``. Must be a
        relative path to the fabfile you are running.
    :type template_dir: str
    
    :param media_dir: Optional dir under code_path if media does not live in 
        ``<code_path>/django_project/media``. No trailing slash.
    :type media_dir: str

    :param wsgi_user: Name of user wsgi process should run as. The user will
        be created as needed.
    :type wsgi_user: str

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
    require.deb.package('libapache2-mod-wsgi')

    # Find out if the wsgi user exists and create it if needed e.g.
    require.user(
        wsgi_user,
        create_group=wsgi_user,
        system=True,
        comment='System user for running the wsgi process under')

    # Clone and replace tokens in apache conf
    if template_dir is None:
        template_dir = 'resources/server_config/apache/'
    filename = '%s.apache.conf.templ' % site_name
    template_path = os.path.join(template_dir, filename)
    fastprint(green('Using %s for template' % template_path))

    context = {
        'escaped_server_name': domain.replace('.', '\.'),
        'server_name': domain,
        'site_user': wsgi_user,
        'code_path': code_path,
        'site_name': site_name}
    context.update(kwargs)  # merge in any params passed in to this function
    destination = '/etc/apache2/sites-available/%s.apache.conf' % site_name
    fastprint(context)

    upload_template(
        template_path,
        destination,
        context=context,
        use_sudo=True)

    set_media_permissions(code_path, wsgi_user, media_dir=media_dir)

    sudo('a2ensite %s.apache.conf' % site_name)
    sudo('a2dissite default')
    sudo('a2enmod rewrite')
    # Check if apache configs are ok - script will abort if not ok
    sudo('/usr/sbin/apache2ctl configtest')
    require.service.restarted('apache2')
    return destination


@task
def build_pil(code_path):
    """Build pil with proper support for jpeg etc.

    :param code_path: Directory where the code lives.
    :type code_path: str

    .. note:: Any existing PIL will be uninstalled.

    .. versionchanged:: 0.16.0 - delegate to virtualenv module

    .. deprecated:: 0.16.0
       Use :func:`virtualenv.build_pil` rather.
    """
    virtualenv.build_pil(code_path)


@task
def setup_celery(project_name, user, password, code_path):
    """
    Installs and starts django-celery with rabbitmq server

    Copy celery config files to correct locations and start rabbitmq and
    celery servers
    :param password: Password for rabbitmq server
    :param user: User for rabbitmq server
    :param project_name: Name for rabbitmq server vhost
    :param code_path: Directory where the code lives.
    :type code_path: str

    Note: In a production environment, you will want to daemonize the celery
    worker:

    http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html#
    daemonizing
    """
    fabtools.require.deb.package('rabbitmq-server')
    sudo('rabbitmqctl add_user %s %s' % (user, password))
    sudo('rabbitmqctl add_vhost %s' % project_name)
    sudo('rabbitmqctl set_permissions -p %s %s ".*" ".*" ".*"' % (
        project_name, user))
    sudo('rabbitmqctl delete_user guest')
    venv = os.path.join(code_path, 'venv')
    with cd(venv):
        run('bin/pip install django-celery')
    run('celery -A tasks worker --loglevel=info')
    fabtools.require.service.restarted('celeryd')
    fabtools.require.service.restarted('rabbitmq-server')
