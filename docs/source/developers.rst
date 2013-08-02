Developer Notes
===============

API
---

If you are a developer, please consult the :doc:`api` for more information on
the tasks that have been made available already.

Please note that the API is not yet stable - it may change between releases.
Because of this you should always pin your requirements file to use a
specific version of FABGIS. e.g.::

    fabgis==0.11.0

When the codebase reaches its first stable release we will maintain API
compatibility per major release.

Getting the source code
-----------------------

The source code is available in github::

    git clone git@github.com:timlinux/fabgis.git

After you check out the source code, install the requirements into a venv::

    cd fabgis
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt


Source code organisation
------------------------

The source is provided in a package 'fabgis' which contains a number of
modules. Generally, there is one module per project we support (to a lesser
or greater extent) e.g. :mod:`fabgis.tilemill`. There are also a few general
purpose modules providing tools and utilities to make our lives easier.

Coding Conventions
------------------

We follow pep8 and a strict requirement that any submissions follow our coding
standards. Its easiest to show an example of what we consider a 'perfect'
module, so please take a look at :mod:`fabgis.tilemill`. A few other pointers:

* Class names CamelCase, no abbreviations
* No abbreviations for variables so `exp_outcome` -> `expected_outcome`
* All modules, packages and functions must include docstrings.
* All modules must include an encoding directive.
* Remove any dead code (e.g. commented out trials you made) before submitting a patch.
* Don't include any code that is not yours to contribute.

Submitting patches
------------------

We accept patches via the github pull request mechanism. Simply fork the
repo, make your improvements and then issue a pull request.

Getting help
------------

Please use the project `issue tracker
<https://github.com/timlinux/fabgis/issues>`_ to report any issues or
generally to ask for help.
