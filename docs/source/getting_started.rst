
Getting started
===============

.. note:: All documentation here assumes that your host and target systems
    use Ubuntu. The procedures will probably work on other debian derivatives.
    Support for other operating systems is not yet available.


.. warning:: These are examples and you should always test any proposed
    automated deployments thoroughly before trying them on a production server.
    I strongly recommend using vagrant for this kind of sandbox testing.

In this getting started guide we will walk you through the basic workflow of
using FABGIS on your host. The workflow is as follows:

* Create a python virtualenv.
* Install fabric, fabtools and fabgis into the virtual env using a
  requirements file.
* Install vagrant and set up a Vagrantfile (for testing in a local sandbox)
* Create a fabfile and define some tasks.
* Run the fabric tasks against your vagrant vhost.
* Test the services you have deployed.

.. note:: We assume you are using a recent version of ubuntu here,
    though you should be able to replicate everything we do here on a windows
    or OSX machine with minimal effort.

For the lazy: You can get all the files and resources for this tutorial from
here: http://github.com/timlinux/fabgis_tutorial/archive/master.zip (or
clone the tutorial git repo here http://github.com/timlinux/fabgis_tutorial).


Creating a python virtualenv
----------------------------

First lets make a working directory::

    mkdir ~/fabgis_tutorial
    cd ~/fabgis_tutorial

Next ensure that you have virtualenv installed::

    sudo apt-get install python-virtualenv

Next create a python virtual environment::

    virtualenv venv
    source venv/bin/activate

Your prompt should now update itself to show that you are in the virtual
environment. For example, after running the above command, mine looked like
this::

    (venv)timlinux@waterfall:fabgis_tutorial$

.. note:: You will need to reactivate the venv if you exit the shell and then
    want to continue working on your project.


Virtual env requirements
------------------------

Next we will create a simple requirements file. A requirements file is simply
a list of packages (with their version numbers) that you wish to install into
your python virtual environment. Using your preferred text editor,
create a new text file e.g.::

    gedit requirements.txt

Now add the following lines to it and then save and close the file::

    Fabric==1.6.0
    fabtools>=0.13.0
    fabgis==0.12.0

Now install those requirements::

    pip install -r requirements.txt

It may take a few minutes to install depending on your connection speed.


Setting up vagrant
------------------

You need to have a server to deploy to. The simplest use case is to deploy
directly onto localhost (-H localhost). However for testing we recommend and
support using Vagrant since the testing will be in a sandbox that you can
destroy and recreate from scratch (which is kinda the whole point of FABGIS).
Using vagrant, you can try out the tools provided by FABGIS in a sandbox with
no risk of damaging your production systems.


Vagrant will spin up a virtual machine and you can run your vagrant tasks in
the Vagrant instance. To install vagrant, download the latest version from
http://downloads.vagrantup.com/ (use the packages they provide rather than
apt as the ubuntu package is old). The commands below will automate the
installation of Vagrant on ubuntu.::

    wget -c http://files.vagrantup.com/packages/a7853fe7b7f08dbedbc934eb9230d33be6bf746f/vagrant_1.2.1_x86_64.deb
    sudo dpkg -i vagrant_1.2.1_x86_64.deb

The download is around 20mb.

A Vagrantfile is used to define the requirements for your vagrant based
virtual host.  You should refer to the `vagrant <http://vagrantup.com>`_
project documentation for the specifics on how to construct a vagrant file,
but to get you started, lets use the one I provide below. First open your
editor again::

    gedit Vagrantfile

Now paste the following into it::

    # -*- mode: ruby -*-
    # vi: set ft=ruby :

    Vagrant.configure("1") do |config|
      # v1 configs...
      # I cant find the proper way to set up bridged networking in the v2 docs
      config.vm.network :bridged, :bridge => "eth0"
    end

    Vagrant.configure("2") do |config|
      # v2 configs...
      config.vm.box = "Ubuntu precise 64"
      config.vm.hostname = "fabgis"
      config.vm.network :public_network
      # For tilestream
      config.vm.network :forwarded_port, guest: 8888, host: 8888
      # For tilemill
      config.vm.network :forwarded_port, guest: 20008, host: 20008
      # For tilemill
      config.vm.network :forwarded_port, guest: 20009, host: 20009
      config.vm.box_url = "http://files.vagrantup.com/precise64.box"

    end


.. note:: This configuration file uses bridged networking. Comment out the
    line with `bridge` in it if you prefer to use NAT.

This command will initialise your vagrant sandbox.::

    vagrant up

.. note:: When we run the above command, there will be a one-time download
of around 400mb to add the base image to your boxes collection.

After the `vagrant up` command completes, you should have a running ubuntu
virtual machine. You can log into it by doing::

    vagrant ssh

And you can look around using normal bash commands - its a full ubuntu system
in there! However one of the goals of fabgis is that we should never need to
physically log into a machine to manage it. So let's log out again straight
away and we can move on to running commands on it using fabric and FABGIS.::

    exit

.. note:: If you want to bring down the vagrant machine again, simply do
    `vagrant destroy`.


Creating our first fabfile
--------------------------

The fabfile is simply a python module (file) that describes what tasks you
would like to run on your managed host. At its simplest, you can simply import
a few FABGIS commands and you are done! First let's make a file::

    gedit fabfile.py

Now let's add a couple of imports from FABGIS (just paste the content below
directly into the file)::

    # For vagrant support you need to do this:
    from fabtools.vagrant import vagrant
    # Now import some fabgis tasks
    from fabgis.tilestream import setup_tilestream, start_tilestream

These two tasks will help us to install
`tilestream <https://github.com/mapbox/tilestream>`_ into our virtual
environment. Close gedit and from your command prompt do::

    fab help

You should see a nice message like this::

    (venv)timlinux@waterfall:fabgis_tutorial$ fab help

    Warning: Command(s) not found:
        help

    Available commands:

        setup_tilestream  Set up tile stream - see https://github.com/mapbox/tilestream.
        start_tilestream  Start the tilestream service - ensure it is installed first.


You can see that there are two commands available to us by virtue of the
imports we made from fabgis.

.. note:: To understand all the commands you can use, consult the :doc:`api`
    documentation.

Running fabgis commands
-----------------------

Now you are ready to run your first FABGIS task on a remote host. Lets install
tilestream into our vagrant sandbox!::

    fab vagrant setup_tilestream

Now go off and have a cup of tea, when it is done your vagrant box should
have everything set up for tilestream. If you would like to try out your new
tilestream installation you con start the tilestream service::

    fab vagrant start_tilestream

Test it out by pointing your browser at: http://localhost:8888 (we set up our
Vagrantfile to forward localhost requests on 8888 into the virtual machine).

You can kill the tilestream server by pressing :kbd:`ctrl-c` in the console
window.

The above process didn't actually publish any data - we would need to copy
some data into the VM for that. Luckily with vagrant and fabgis it is pretty
simple to do that. Vagrant automatically mounts the host directory where the
Vagrantfile exists into the guest virtual machine (under `/vagrant`). So for
testing in the context of vagrant, simply copy a .mbtiles files into your
working directory (where you created your fabfile and vagrant file). Copy
the fabgis.mbtile file provided at :

http://github.com/timlinux/fabgis_tutorial/archive/master.zip

Next we start the tilestream FABGIS task again, but this time we are going to
tell it to to use `/vagrant` as the tiles dir.::

    fab vagrant start_tilestream:tile_dir=/vagrant

Now point your browser again at http://localhost:8888 and you should see any
tilesets you placed in your host system available in the web ui.

Wrapping up
-----------

This concludes this introductory tutorial. If you want to play around more,
I added a couple more tasks into the fabfile in the tutorial repository that
will let you play with tilemill too::

    fab vagrant setup_tilemill
    fab vagrant start_tilemill

Now point your browser at: http://localhost:20009/

You can find out more about tilemill from their
`website <http://www.mapbox.com/tilemill/>`_.

