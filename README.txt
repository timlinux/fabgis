FabGIS
======

'Fabric tasks for the busy FOSSGIS professional'

Welcome to the fabgis project! The purpose of this project is to commodotise
the deployment of FOSSGIS services onto services. By commodotise we mean
'treat servers as expendible and rapidly replaceable entities that can be
deployed either singularly or en masse'.


**Warning** While we try our best to make stable and reliable tasks,
there is the inherant danger that these tasks may break some configuration
on a running server. Before using in any production environment, test,
test and test again in a sandboxed environment. We take NO RESPONSIBILITY
for any bad things that may happen on your system.

**Warning** Yeah I know we are going a bit overboard with our warnings but
please note that these scripts do not harden your server against intrusion
    / maximum security - that is YOUR RESPONSIBILITY.

To achieve this we use the wonderful fabric library (http://fabfile.org). If
you want to get more familiar with fabric, there is a very nice article here:
http://www.linuxjournal.com/content/fabric-system-administrators-best-friend
which contains enough information to get you started.

What kind of services do we commodotise? Here are a few of the kinds of
activities you can do with fabgis:

* Install PostgreSQL and PostGIS (both 1.5 and 2.0). We support 1.5 because
  many DJANGO instances still rely on it.
* Install QGIS (both 1.8 and master), built from source for optimium
  performance.
* Install QGIS Server (both 1.8 and master), again built from source.
* Backup and restore Postgresql databases (pulling a backup off the server
  and pushing a backup up to the server and restoring it).
* Deploying a DJANGO application under apache.
* Deploying a website under apache.
* Deploying a UMN Mapserver instance.

We plan on supporting many other activities (tasks in fabric parlance).

Getting started
---------------

**Note:** All documentation here assumes that your host and target systems
use Ubuntu. The procedures will probably work on other debian derivatives.
Support for other operating systems is not yet available.


To get started, you need to install fabric and fabtools. This command will
take care of that for you::

    sudo pip install -r requirements.txt

We assume you have pip installed and that you are happy to install these as
system packages. If not, consider deploying a venv in the fabgis root
directory and activating it before trying any of the examples listed below.

Testing with Vagrant
--------------------

You need to have a server to deploy to. The simplest use case is to deploy
directly onto localhost. For testing we recommend and support using Vagrant
since the testing will be in a sandbox that you can destroy and recreate from
scratch (which is kinda the whole point of fabgis).

Vagrant will spin up a virtual machine and you can run your vagrant tasks in
the Vagrant instance. A Vagrantfile is provided in this repository so that
you can try out the tools provided by fabgis is a sandbox with no risk of
damaging your production systems.

To start you need to install vagrant on your system::

    wget -c http://files.vagrantup.com/packages/a7853fe7b7f08dbedbc934eb9230d33be6bf746f/vagrant_1.2.1_x86_64.deb
    sudo dpkg -i vagrant_1.2.1_x86_64.deb

The download is around 20mb.

.. note:: Don't use the one in apt - it is old (at the time of writing anyway).


Some examples
-------------

Here is how we might create a new postgis 1.5 instance on the target host::

    fab vagrant create_postgis_1_5_db:dbname=test


