API Documentation
=================

Common
-------

Common functions.

.. automodule:: fabgis.common
   :members:

GDAL
-------

GDAL build and related tools

.. automodule:: fabgis.gdal
   :members:


InaSAFE
-------

Tools for deploying InaSAFE related tasks.

.. automodule:: fabgis.inasafe
   :members:


Jenkins
-------

Tools for deploying Jenkins CI

.. automodule:: fabgis.jenkins
   :members:


PostgreSQL
----------

Tools for deploying PostgreSQL related tasks.

.. automodule:: fabgis.postgres
   :members:


QGIS
----

Tools for deploying QGIS (master and release versions).

.. automodule:: fabgis.qgis
   :members:

Sphinx
------

Tools for deploying sphinx.

.. automodule:: fabgis.sphinx
   :members:


System
-------

System related tools.

.. automodule:: fabgis.system
   :members:


Tilemill
--------

Tools for deploying TileMill.

.. automodule:: fabgis.tilemill
   :members:


Proj4
-----

Tools for deploying proj4.

.. automodule:: fabgis.proj4
   :members:

Hdf
----

Tools for deploying hdf support.

.. automodule:: fabgis.hdf
   :members:

Utilities
---------

Helper utilities.

.. automodule:: fabgis.utilities
   :members:

Dropbox
-------

Tools to help you set up drop box on your server.

Unfortunately we can't run this fully automated due to an issue with fabric
that prevents using ctrl-c on the remove host (needed to halt the initial
dropboxd command needed to set up the dropbox synced account).

So for example you need to do::

    fab vagrant setup_dropbox

Then once your account is linked, press Ctrl-c - which will also
terminate the above fabric job. Then run::

    fab vagrant setup_dropbox_daemon


.. automodule:: fabgis.dropbox
   :members:
