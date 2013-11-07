
Working with docker
===================

If you are using docker (or a ssh server that is behind another ssh server),
you can still run fabgis scripts against the docker instance (assuming it
has ssh running).

A typical work flow might be:

* log in to your server
* create a new docker container with openssh running
* log out and on your localhost add two ssh entries to your ``.ssh/config``

In ``.ssh/config``::

  Host bastion
    User foo
    Port 1234
    HostName 192.168.1.2
    FallBackToRsh no

  Host container
    User root
    # Next line uses proxy of bastion to get into container directly
    # see http://backdrift.org/transparent-proxy-with-ssh
    ProxyCommand  ssh bastion nc %h %p
    Port 2222
    HostName localhost
    FallBackToRsh no

Now you should be able to use fabric in this way::

  fab -H container:2222 foo

