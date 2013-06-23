import os
from fabric.api import fastprint, run, cd, env, task, sudo
from fabric.contrib.files import contains, exists, append
import fabtools

from .common import setup_env


def update_git_checkout(code_path, url, repo_alias, branch='master'):
    """Make sure there is a read only git checkout.

    :param code_path: the path to where the repo should be
    :type code_path: str

    :param url: complete http url for cloning/checking out the repo
    :type url: str

    :param repo_alias: alias name under which the repo should be checked out.
    :type repo_alias: str

    :param branch: string representing the name of the branch to build from.
        Defaults to 'master'
    :type branch: str

    To run e.g.::

        fab -H 188.40.123.80:8697 remote update_git_checkout

    """
    setup_env()
    repo_path = os.path.join(code_path, repo_alias)

    fabtools.require.deb.package('git')
    if not exists(repo_path):
        fastprint('Basic Repository does not exist, creating.')
        run('mkdir -p %s' % code_path)
        with cd(code_path):
            run('git clone %s %s' % (url, repo_alias))
    else:
        fastprint('Repo checkout does exist, updating.')
        with cd(repo_path):
            # Get any updates first
            run('git fetch')
            if branch != 'master':
                branches = run('git branch')
                if branch not in branches:
                    print branches
                    run('git branch --track %s origin/%s' % (branch, branch))
                if ('* %s' % branch) not in branches:
                    run('git checkout %s' % branch)
            else:
                run('git checkout master')
            run('git pull')


def append_if_not_present(filename, text, use_sudo=False):
    """Append to a file if an equivalent line is not already there."""
    if not contains(filename, text):
        append(filename, text, use_sudo=use_sudo)


def replace_tokens(conf_file, tokens):
    """Prepare a template config file by replacing its tokens.

    :param conf_file: Either a full path to a conf file name or just the
        file name. In the latter case, it assumes the file is then in the
        current working directory.
    :type conf_file: str

    :param tokens: A dictionary of key-values that should be replaced
        in the conf file.
    :type tokens: dic

    Example tokens::

        my_tokens = {
            'SERVERNAME': env.doc_site_name,  # Web Url e.g. foo.com
            'WEBMASTER': 'werner@linfiniti.com',  # email of web master
            'DOCUMENTROOT': webdir,  # Content root .e.g. /var/www
            'SITENAME': sitename,  # Choosen name of jenkins 'root'
        }

    """

    if '.templ' == conf_file[-6:]:
        templ_file = conf_file
        conf_file = conf_file.replace('.templ', '')
        sudo(
            'cp %(templ_file)s %(conf_file)s' % {
            'templ_file': templ_file,
            'conf_file': conf_file})

    base_path, file_name = os.path.split(conf_file)
    if base_path is not '':
        # The file is not in the current working dir.
        with cd(base_path):
            for key, value in tokens.iteritems():
                sudo('sed -i.bak -r -e "s/\[%s\]/%s/g" %s' % (
                    key, value, file_name))
            sudo('rm %s.bak' % file_name)
    else:
        # filename only, not full path - assumes the current working dir is
        # the same as where the conf file is located
        for key, value in tokens.iteritems():
            sudo('sed -i.bak -r -e "s/\[%s\]/%s/g" %s' % (
                key, value, file_name))
            sudo('rm %s.bak' % file_name)


@task
def setup_venv(requirements_file='requirements.txt'):
    """Initialise or update the virtual environment.


    To run e.g.::

        fab -H 192.168.1.1:2222 setup_venv

    """
    setup_env()
    with cd(env.code_path):
        # Ensure we have a venv set up
        fabtools.require.python.virtualenv('venv')
        run('venv/bin/pip install -r %s' % requirements_file)
