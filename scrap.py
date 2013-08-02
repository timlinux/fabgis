__author__ = 'timlinux'


import os
from datetime import datetime
from fabric.api import *
from fabric.contrib.files import contains, exists, append, sed
import fabtools
# Don't remove even though its unused
from fabtools.vagrant import vagrant

# Usage fab localhost [command]
#    or fab remote [command]
#  e.g. fab localhost update_qgis_plugin_repo

# Global fabric settings

# Run a task against the localhost server.
#
#    e.g. fab -R local get_postgres_dump
#    e.g. fab -R prod get_postgres_dump
env.roledefs = {
    'test': ['localhost'],
    'dev': ['none@none.com'],
    'staging': ['none@none.com'],
    'production': ['none@none.com']
}
env.env_set = False


def all():
    """Things to do regardless of whether command is local or remote."""
    if env.env_set:
        fastprint('Environment already set!\n')
        return

    fastprint('Setting environment!\n')

    with hide('output'):
        env.user = run('whoami')
        env.hostname = run('hostname')

        env.repo_site_name = repo_site_names[env.hostname]
        env.doc_site_name = doc_site_names[env.hostname]
        env.plugin_repo_path = '/home/web/inasafe-test'
        env.inasafe_docs_path = '/home/web/inasafe-docs'
        env.home = os.path.join('/home/', env.user)
        env.workspace = os.path.join(env.home,
                                     'dev',
                                     'python')
        env.inasafe_git_url = 'git://github.com/AIFDR/inasafe.git'
        env.qgis_git_url = 'git://github.com/qgis/Quantum-GIS.git'
        env.repo_alias = 'inasafe-test'
        env.code_path = os.path.join(env.workspace, env.repo_alias)

    env.env_set = True
    fastprint('env.env_set = %s' % env.env_set)

###############################################################################
# Next section contains helper methods tasks
###############################################################################


def update_qgis_plugin_repo(repo_name='test_repo'):
    """Initialise a QGIS plugin repo where we host test builds."""
    code_path = os.path.join(env.repo_path, env.repo_alias)
    local_path = '%s/scripts/test-build-repo' % code_path

    if not exists(env.plugin_repo_path):
        sudo('mkdir -p %s' % env.plugin_repo_path)
        sudo('chown %s.%s %s' % (env.user, env.user, env.plugin_repo_path))

    env.run('cp %s/plugin* %s' % (local_path, env.plugin_repo_path))
    env.run('cp %s/icon* %s' % (code_path, env.plugin_repo_path))
    env.run('cp %(local_path)s/inasafe-test.conf.templ '
            '%(local_path)s/%s.conf' % {'local_path': local_path,
                                        'repo_name': repo_name})

    sed('%s/%s.conf' % (local_path, repo_name),
        '[SITE_NAME]',
        env.repo_site_name)

    with cd('/etc/apache2/sites-available/'):
        if exists('%s.conf' % repo_name):
            sudo('a2dissite %s.conf' % repo_name)
            fastprint('Removing old apache2 conf', False)
            sudo('rm %s.conf' % repo_name)

        sudo('ln -s %s/%s.conf .' % (local_path, repo_name))

    sudo('a2ensite %.conf' % repo_name)
    sudo('service apache2 reload')


def update_docs_site(site_name):
    """Initialise a docs site where we host test pdf."""
    code_path = os.path.join(env.repo_path, env.repo_alias)
    local_path = '%s/scripts/test-build-repo' % code_path

    if not exists(env.inasafe_docs_path):
        sudo('mkdir -p %s' % env.docs_path)
        sudo('chown %s.%s %s' % (env.user, env.user, env.docs_path))

    env.run('cp %s/plugin* %s' % (local_path, env.plugin_repo_path))
    env.run('cp %s/icon* %s' % (code_path, env.plugin_repo_path))
    env.run(
        'cp %(local_path)s/docs.conf.templ '
        '%(local_path)s/%(site_name)s.conf' % {
        'local_path': local_path,
        'site_name': site_name})

    sed('%s/inasafe-test.conf' % local_path, '[SITE_NAME]', site_name)

    with cd('/etc/apache2/sites-available/'):
        if exists('inasafe-docs.conf'):
            sudo('a2dissite inasafe-docs.conf')
            fastprint('Removing old apache2 conf', False)
            sudo('rm inasafe-docs.conf')

        sudo('ln -s %s/inasafe-docs.conf .' % local_path)

    # Add a hosts entry for local testing - only really useful for localhost
    hosts = '/etc/hosts'
    if not contains(hosts, site_name):
        append(hosts, '127.0.0.1 %s' % site_name, use_sudo=True)

    sudo('a2ensite %s.conf' % site_name)
    sudo('service apache2 reload')


def update_git_checkout(branch='master'):
    """Make sure there is a read only git checkout.

    Args:
        branch: str - a string representing the name of the branch to build
            from. Defaults to 'master'

    To run e.g.::

        fab -H 188.40.123.80:8697 remote update_git_checkout

    """

    if not exists(os.path.join(env.repo_path, env.repo_alias)):
        fastprint('Repo checkout does not exist, creating.')
        env.run('mkdir -p %s' % (env.repo_path))
        with cd(env.repo_path):
            env.run('git clone %s %s' % (
                env.inasafe_git_url, env.repo_alias))
    else:
        fastprint('Repo checkout does exist, updating.')
        with cd(os.path.join(env.repo_path, env.repo_alias)):
            # Get any updates first
            env.run('git fetch')
            # Get rid of any local changes
            env.run('git reset --hard')
            # Get back onto master branch
            env.run('git checkout master')
            # Remove any local changes in master
            env.run('git reset --hard')
            # Delete setup_env local branches
            env.run('git branch | grep -v \* | xargs git branch -D')

    with cd(os.path.join(env.repo_path, env.repo_alias)):
        if branch != 'master':
            env.run('git branch --track %s origin/%s' % (branch, branch))
            env.run('git checkout %s' % branch)
        else:
            env.run('git checkout master')
        env.run('git pull')


def install_latex():
    """Ensure that the target system has a usable latex installation.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """
    clone = env.run('which pdflatex')
    if '' == clone:
        env.run('sudo apt-get install texlive-latex-extra python-sphinx '
                'texinfo dvi2png')


def replace_tokens(conf_file, server_name, site_name):
    env.run(
        'cp %(conf_file)s.templ %(conf_file)s' % {
            'conf_file': conf_file})
    # We need to replace these 3 things in the conf file:
    # [SERVERNAME] - web site base url e.g. foo.com
    # [ESCAPEDSERVERNAME] - the site base url with escaping e.g. foo\.com
    # [SITEBASE] - dir under which the site is deployed e.g. /home/web
    # [SITENAME] - should match env.repo_alias
    # [SITEUSER] - user apache wsgi process should run as
    # [CODEBASE] - concatenation of site base and site name e.g. /home/web/app
    escaped_name = site_name.replace('.', '\\\.')
    fastprint('Escaped server name: %s' % escaped_name)
    sed('%s' % conf_file, '\[SERVERNAME\]', site_name)
    sed('%s' % conf_file, '\[ESCAPEDSERVERNAME\]', escaped_name)
    sed('%s' % conf_file, '\[SITEBASE\]', env.webdir)
    sed('%s' % conf_file, '\[SITENAME\]', env.repo_alias)
    sed('%s' % conf_file, '\[SITEUSER\]', env.wsgi_user)
    sed('%s' % conf_file, '\[CODEBASE\]', env.code_path)


def setup_venv():
    """Initialise or update the virtual environmnet.


    To run e.g.::

        fab -H 188.40.123.80:8697 remote setup_venv

    or if you have configured env.hosts, simply

        fab remote setup_venv
    """

    with cd(env.code_path):
        # Ensure we have a venv set up
        require.python.virtualenv('venv')
        env.run('venv/bin/pip install -r requirements-prod.txt')


def setup_mapserver():
    # Clone and replace tokens in mapserver map file
    conf_dirs = [
        '%s/fabgis_resources/server_config/mapserver/mapfiles/' % (env.code_path),
        '%s/fabgis_resources/server_config/mapserver/apache-include/' % (
            env.code_path)]
    for conf_dir in conf_dirs:
        for myFile in os.listdir(conf_dir):
            myExt = os.path.splitext(myFile)[1]
            conf_file = os.path.join(conf_dir, myFile)

            if myExt == '.templ':
                replace_tokens(conf_file)

    # We also need to append 900913 epsg code to the proj epsg list
    epsg_path = '/usr/share/proj/epsg'
    epsg_code = (
        '<900913> +proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_'
        '0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs')
    epsg_id = '900913'
    if not contains(epsg_path, epsg_id):
        append(epsg_path, epsg_code, use_sudo=True)


def build_test_package(site_name, branch='master'):
    """Create a test package and publish it in our repo.

    Args:
        branch: str - a string representing the name of the branch to build
            from. Defaults to 'master'.

    To run e.g.::

        fab -H 188.40.123.80:8697 remote build_test_package

        or to package up a specific branch (in this case minimum_needs)

        fab -H 88.198.36.154:8697 remote build_test_package:minimum_needs

    .. note:: Using the branch option will not work for branches older than 1.1
    """

    update_git_checkout(branch)
    update_qgis_plugin_repo()

    dir_name = os.path.join(env.repo_path, env.repo_alias)
    with cd(dir_name):
        # Get git version and write it to a text file in case we need to cross
        # reference it for a user ticket.
        sha = env.run('git rev-parse HEAD > git_revision.txt')
        fastprint('Git revision: %s' % sha)

        get('metadata.txt', '/tmp/metadata.txt')
        metadata_file = file('/tmp/metadata.txt', 'rt')
        metadata_text = metadata_file.readlines()
        metadata_file.close()
        for line in metadata_text:
            line = line.rstrip()
            if 'version=' in line:
                plugin_version = line.replace('version=', '')
            if 'status=' in line:
                status = line.replace('status=', '')

        env.run('scripts/release.sh %s' % plugin_version)
        package_name = '%s.%s.zip' % ('inasafe', plugin_version)
        source = '/tmp/%s' % package_name
        fastprint('Source: %s' % source)
        env.run('cp %s %s' % (source, env.plugin_repo_path))

        plugins_xml = os.path.join(env.plugin_repo_path, 'plugins.xml')
        sed(plugins_xml, '\[VERSION\]', plugin_version)
        sed(plugins_xml, '\[FILE_NAME\]', package_name)
        sed(plugins_xml, '\[URL\]', 'http://%s/%s' %
                                    (site_name, package_name))
        sed(plugins_xml, '\[DATE\]', str(datetime.now()))

        fastprint('Add http://%s/plugins.xml to QGIS plugin manager to use.'
                  % site_name)


def build_documentation(branch='master'):
    """Create a pdf and html doc tree and publish them online.

    Args:
        branch: str - a string representing the name of the branch to build
            from. Defaults to 'master'.

    To run e.g.::

        fab -H 188.40.123.80:8697 remote build_documentation

        or to package up a specific branch (in this case minimum_needs)

        fab -H 88.198.36.154:8697 remote build_documentation:version-1_1

    .. note:: Using the branch option will not work for branches older than 1.1
    """

    update_git_checkout(branch)
    install_latex()

    dir_name = os.path.join(env.repo_path, env.repo_alias, 'docs')
    with cd(dir_name):
        # build the tex file
        env.run('make latex')

    dir_name = os.path.join(env.repo_path, env.repo_alias,
                            'docs', 'build', 'latex')
    with cd(dir_name):
        # Now compile it to pdf
        env.run('pdflatex -interaction=nonstopmode InaSAFE.tex')
        # run 2x to ensure indices are generated?
        env.run('pdflatex -interaction=nonstopmode InaSAFE.tex')


def initialise_qgis_plugin_repo(site_name):
    """Initialise a QGIS plugin repo where we host test builds."""
    all()
    fabtools.require.deb.package('libapache2-mod-wsgi')
    code_path = os.path.join(env.repo_path, env.repo_alias)
    local_path = '%s/scripts/test-build-repo' % code_path

    if not exists(env.plugin_repo_path):
        sudo('mkdir -p %s' % env.plugin_repo_path)
        sudo('chown %s.%s %s' % (env.user, env.user, env.plugin_repo_path))

    run('cp %s/plugin* %s' % (local_path, env.plugin_repo_path))
    run('cp %s/icon* %s' % (code_path, env.plugin_repo_path))
    run('cp %(local_path)s/inasafe-test.conf.templ '
        '%(local_path)s/inasafe-test.conf' % {'local_path': local_path})

    sed('%s/%s.conf' % (local_path, site_name),
        'inasafe-test.linfiniti.com',
        site_name)

    with cd('/etc/apache2/sites-available/'):
        if exists('inasafe-test.conf'):
            sudo('a2dissite inasafe-test.conf')
            fastprint('Removing old apache2 conf', False)
            sudo('rm inasafe-test.conf')

        sudo('ln -s %s/inasafe-test.conf .' % local_path)

    # Add a hosts entry for local testing - only really useful for localhost
    hosts = '/etc/hosts'
    if not contains(hosts, 'inasafe-test'):
        append(hosts, '127.0.0.1 %s' % env.repo_site_name, use_sudo=True)

    sudo('a2ensite inasafe-test.conf')
    sudo('service apache2 reload')


def initialise_docs_site():
    """Initialise an InaSAFE docs sote where we host test pdf."""
    all()
    fabtools.require.deb.package('libapache2-mod-wsgi')
    code_path = os.path.join(env.repo_path, env.repo_alias)
    local_path = '%s/scripts/test-build-repo' % code_path

    if not exists(env.inasafe_docs_path):
        sudo('mkdir -p %s' % env.inasafe_docs_path)
        sudo('chown %s.%s %s' % (env.user, env.user, env.inasafe_docs_path))

    run('cp %s/plugin* %s' % (local_path, env.plugin_repo_path))
    run('cp %s/icon* %s' % (code_path, env.plugin_repo_path))
    run('cp %(local_path)s/inasafe-test.conf.templ '
        '%(local_path)s/inasafe-test.conf' % {'local_path': local_path})

    sed('%s/inasafe-test.conf' % local_path,
        'inasafe-test.linfiniti.com',
        env.repo_site_name)

    with cd('/etc/apache2/sites-available/'):
        if exists('inasafe-docs.conf'):
            sudo('a2dissite inasafe-docs.conf')
            fastprint('Removing old apache2 conf', False)
            sudo('rm inasafe-docs.conf')

        sudo('ln -s %s/inasafe-docs.conf .' % local_path)

    # Add a hosts entry for local testing - only really useful for localhost
    hosts = '/etc/hosts'
    if not contains(hosts, 'inasafe-docs'):
        append(hosts, '127.0.0.1 %s' % env.repo_site_name, use_sudo=True)

    sudo('a2ensite inasafe-docs.conf')
    sudo('service apache2 reload')


def update_git_checkout(branch='master'):
    """Make sure there is a read only git checkout.

    Args:
        branch: str - a string representing the name of the branch to build
            from. Defaults to 'master'

    To run e.g.::

        fab -H 188.40.123.80:8697 remote update_git_checkout

    """
    all()
    fabtools.require.deb.package('git')
    if not exists(env.code_path):
        fastprint('Repo checkout does not exist, creating.')
        run('mkdir -p %s' % env.repo_path)
        with cd(env.repo_path):
            run('git clone %s %s' % (env.inasafe_git_url, env.repo_alias))
    else:
        fastprint('Repo checkout does exist, updating.')
        with cd(env.code_path):
            # Get any updates first
            run('git fetch')
            # Get rid of any local changes
            run('git reset --hard')
            # Get back onto master branch
            run('git checkout master')
            # Remove any local changes in master
            run('git reset --hard')
            # Delete setup_env local branches
            run('git branch | grep -v \* | xargs git branch -D')

    with cd(env.code_path):
        if branch != 'master':
            run('git branch --track %s origin/%s' %
                (branch, branch))
            run('git checkout %s' % branch)
        else:
            run('git checkout master')
        run('git pull')


def install_latex():
    """Ensure that the target system has a usable latex installation."""
    all()
    sudo('apt-get update')
    fabtools.require.deb.package('texlive-latex-extra')
    fabtools.require.deb.package('python-sphinx')
    fabtools.require.deb.package('dvi2png')
    fabtools.require.deb.package('texinfo')

def setup_realtime():
    """Set up a working environment for the realtime quake report generator."""
    all()
    install_qgis2()
    update_git_checkout()



@task
def build_test_package(branch='master'):
    """Create a test package and publish it in our repo.

    Args:
        branch: str - a string representing the name of the branch to build
            from. Defaults to 'master'.

    To run e.g.::

        fab -H 188.40.123.80:8697 build_test_package

        or to package up a specific branch (in this case minimum_needs)

        fab -H 88.198.36.154:8697 build_test_package:minimum_needs

    .. note:: Using the branch option will not work for branches older than 1.1
    """
    all()
    update_git_checkout(branch)
    initialise_qgis_plugin_repo()

    fabtools.require.deb.package('make')
    fabtools.require.deb.package('gettext')

    with cd(env.code_path):
        # Get git version and write it to a text file in case we need to cross
        # reference it for a user ticket.
        sha = run('git rev-parse HEAD > git_revision.txt')
        fastprint('Git revision: %s' % sha)

        get('metadata.txt', '/tmp/metadata.txt')
        metadata_file = file('/tmp/metadata.txt', 'rt')
        metadata_text = metadata_file.readlines()
        metadata_file.close()
        for line in metadata_text:
            line = line.rstrip()
            if 'version=' in line:
                plugin_version = line.replace('version=', '')
            if 'status=' in line:
                line.replace('status=', '')

        run('scripts/release.sh %s' % plugin_version)
        package_name = '%s.%s.zip' % ('inasafe', plugin_version)
        source = '/tmp/%s' % package_name
        fastprint('Source: %s' % source)
        run('cp %s %s' % (source, env.plugin_repo_path))

        plugins_xml = os.path.join(env.plugin_repo_path, 'plugins.xml')
        sed(plugins_xml, '\[VERSION\]', plugin_version)
        sed(plugins_xml, '\[FILE_NAME\]', package_name)
        sed(plugins_xml, '\[URL\]', 'http://%s/%s' %
                                    (env.repo_site_name, package_name))
        sed(plugins_xml, '\[DATE\]', str(datetime.now()))

        fastprint('Add http://%s/plugins.xml to QGIS plugin manager to use.'
                  % env.repo_site_name)


@task
def build_documentation(branch='master'):
    """Create a pdf and html doc tree and publish them online.

    Args:
        branch: str - a string representing the name of the branch to build
            from. Defaults to 'master'.

    To run e.g.::

        fab -H 188.40.123.80:8697 build_documentation

        or to package up a specific branch (in this case minimum_needs)

        fab -H 88.198.36.154:8697 build_documentation:version-1_1

    .. note:: Using the branch option will not work for branches older than 1.1
    """
    all()
    update_git_checkout(branch)
    install_latex()

    dir_name = os.path.join(env.repo_path, env.repo_alias, 'docs')
    with cd(dir_name):
        # build the tex file
        run('make latex')

    dir_name = os.path.join(env.repo_path, env.repo_alias,
                            'docs', 'build', 'latex')
    with cd(dir_name):
        # Now compile it to pdf
        run('pdflatex -interaction=nonstopmode InaSAFE.tex')
        # run 2x to ensure indices are generated?
        run('pdflatex -interaction=nonstopmode InaSAFE.tex')
