# ~/fabfile.py
# A Fabric file for carrying out various administrative tasks with InaSAFE.
# Tim Sutton, Jan 2013
from fabric import *
from fabric.api import *
from fabric.contrib.files import contains, exists, append, sed
import fabtools
import fabgis.fabgis
from fabgis.fabgis import *
###############################################################################
# Next section contains actual tasks
###############################################################################


@task
@hosts('192.168.1.1:22')
def get_foo_dump():
    """This is an example of how you can wrap fabgis tasks in your fabfile."""
    fabgis.get_postgres_dump('foodb')


@task
def build_server():
    """Build a complete functioning fossgis server instance.

        e.g.

            fab -H root@foo create_user
            fab -H foo build_server

        You need to run the create_user task separately to bootstrap the
        creation of your user on the remote host.
    """
    # does not work on osx
    # ssh_copy_id()
    fabgis.harden()
    fabgis.create_postgis_1_5_db('gis')
    fabgis.install_qgis2()
