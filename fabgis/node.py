# coding=utf-8
"""
Tools for deployment of node apps.
==================================

We will set up node in python virtual environment nodeenv so that it does not
interfere with other node based installations on the system.
"""

from fabric.api import task, run, cd, prefix
from .virtualenv import setup_venv

@task
def setup_node(work_path, node_version=None, proxy_url=None):
    """Setup node in a nodeenv to avoid conflicts with other node apps.

    See https://pypi.python.org/pypi/nodeenv

    After installation, you will have two subdirectories in the work_path::

        venv     <-- python venv
        env      <-- node env

    :param work_path: Directory into which node should be installed.
    :type work_path: str

    :param node_version: A specific version of node if you need it. Some node
        apps require a specific version of node, so this option will allow you
        to specify which one to install. Example '0.10.26'.
    :type node_version: str

    :param proxy_url: Optional parameters to specify the url to use for your
        network proxy. It should be specified in the form:
        ``http://<host>:<port>``. The same proxy will be used for both http and
        https urls. If ommitted no proxy will be used.
    :type proxy_url: str
    """
    with cd(work_path):
        setup_venv(code_path=work_path)
        with prefix('venv/bin'):
            run('pip install nodeenv')
            if node_version is not None:
                run('nodeenv env --node=%s' % node_version)
            else:
                run('nodeenv env')

        with prefix('env/bin'):
            run('npm install')
            if proxy_url is not None:
                run('npm config set proxy %s' % proxy_url)
                run('npm config set https-proxy %s' % proxy_url)
