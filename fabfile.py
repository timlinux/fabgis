# coding=utf-8
# ~/fabfile.py
"""
This is an example fabfile for the fabgis project.

Warning: These are examples and you should always test any proposed
automated deployments thoroughly before trying them on a production server.
I strongly recommend using vagrant for this kind of sandbox testing.

To use this fabfile, you should first install fabric and fabtools. The
requirements file provided in this directory will let you do this easily by
typing e.g.

sudo pip install requirements.txt

To install vagrant, download the latest version from
http://downloads.vagrantup.com/ (use the packages they provide rather than
apt as the ubuntu package is old).

Assuming you are using a vagrant sandbox, you can use the Vagrantfile
supplied with this repo to create your vagrant box. Note that there is a
one time download of around 400mb to add the base image to your boxes
collection. This command will initialise your vagrant sandbox.

vagrant up

Now you are ready to run your first fabgis task! Lets install QGIS master
and PostgreSQL into our vagrant sandbox!

fab vagrant build_server

Now go off and have a cup of tea, when it is done your vagrant box should
have everything set up. If you would like to try out your new QGIS you
could do something like this:

ssh localhost -p 2222 -X /usr/local/qgis-master/bin/qgis

That will run your newly built QGIS instance and forward the display back
to your local X-xerver.


Tim Sutton, Jan 2013
"""

import os
# lcd = local cd
from fabric.api import task, hosts, cd, run, fastprint, local, lcd
from fabric.contrib.project import rsync_project
from fabric.colors import blue
from fabgis.postgres import (
    setup_postgis_latest, 
    create_postgis_1_5_db,
    get_postgres_dump,
    setup_nightly_backups)
from fabgis.tilemill import setup_tilemill, start_tilemill
from fabgis.tilestream import setup_tilestream, start_tilestream
from fabgis.qgis import install_qgis2, install_qgis1_8, install_qgis_master
from fabgis.proj4 import build_proj4
from fabgis.hdf import build_hdf5
from fabgis.dropbox import (
    setup_dropbox,
    setup_dropbox_daemon,
    dropbox_status,
    start_dropbox,
    stop_dropbox)
from fabgis.system import create_user
from fabgis.docker import (
    setup_docker, setup_docker_image, docker, create_docker_container)
# You can also make generic tasks available at the command line simply by
# importing them. e.g.
#from fabgis.sphinx import setup_sphinx

# For vagrant support you need to do this:
# noinspection PyUnresolvedReferences
from fabtools.vagrant import vagrant


@task
def ls():
    """Simply list the directory on the remote server."""
    run('pwd')
    run('ls')


@task
def build_server():
    """Build a complete functioning FOSSGIS server instance.

    Notes:

    The installed server will have QGIS from master set up on it and postgres
    installed with postgis and a template spatial database created. A default
    database called 'gis' will be created too.

        e.g.

            fab -H root@foo create_user
            fab -H foo build_server

        You need to run the create_user task separately to bootstrap the
        creation of your user on the remote host.
    """
    build_proj4()
    build_hdf5()
    create_postgis_1_5_db('gis')
    install_qgis2(gdal_from_source=True)


@task
@hosts('192.168.1.1:22')
def get_gis_dump():
    """An example of how you can fetch a database dump from a server.

    Notes:

        @task decorator denotes this as a fabric task
        @hosts decorator indicates which hosts this command should run on.
        Its a shortcut to using the -H option on the command line. e.g.

            fab -H 192.168.1.22 get_foo_dump

    """
    get_postgres_dump('gis')


@task
def update_website():
    """Update the website docs for fabgis."""
    with cd('~/dev/python/fabgis/docs'):
        run('git reset --hard origin/master')
        run('git pull')
        run('make clean')
        run('../venv/bin/sphinx-build source build/html')


@task
def sync_docs_to_server(remote_dir='/home/web/fabgis'):
    """Synchronize docs with webserver.

    :param remote_dir: The directory to sync the docs to. After syncing it will
        match the content of your local docs/build/html dir.
    :type remote_dir: str
    """
    base_path = os.path.dirname(__file__)
    docs_path = os.path.join(base_path, 'docs')
    html_path = os.path.join(docs_path, 'build', 'html')
    with lcd(docs_path):
        local('make clean')
        # Make sure to set pythonpath in case there is alread a system
        # installed copy of fabgis overriding our local copy.
        local('PYTHONPATH=%s make html' % base_path)

    rsync_project(remote_dir=remote_dir, local_dir=html_path)
    run('chmod o+rX -R %s' % remote_dir)
    fastprint(blue(
        'Your server docs are now synchronised to your local project\n'))
