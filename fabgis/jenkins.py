import os
import time
from fabric.contrib.files import contains, exists
from fabric.api import run, cd, env, task, sudo, put
import fabtools
from .utilities import append_if_not_present, replace_tokens
from .common import setup_env
"""
Jenkins related tasks.
======================

"""

@task
def add_jenkins_repository():
    """Add the Jenkins latest repository"""
    jenkins_url = 'http://pkg.jenkins-ci.org/'
    jenkins_key = jenkins_url + 'debian/jenkins-ci.org.key'
    jenkins_repo = jenkins_url + 'debian binary/'
    jenkins_apt_file = '/etc/apt/sources.list.d/jenkins-repository.list'

    run('wget -q -O - %s | sudo apt-key add -' % jenkins_key)

    if not exists(jenkins_apt_file):
        sudo('touch %s' % jenkins_apt_file)
    append_if_not_present(
        jenkins_apt_file, 'deb ' + jenkins_repo, use_sudo=True)


def configure_jenkins(repo):
    """Configure the jenkins json file.

    We have to update the json file if we want to switch between distribution
    provided jenkins and upstream jenkins.

    :param repo: A repository to use.
    :type repo: str
    """
    command1 = 'curl -L http://updates.jenkins-ci.org/update-center.json'
    command2 = 'sed "1d;$d" > /var/lib/jenkins/updates/default.json'
    jenkins = 'jenkins'
    sudo('mkdir -p /var/lib/jenkins/updates', user=jenkins)
    sudo('%s > /var/lib/jenkins/updates/default.json' % command1,
         user=jenkins)
    sudo('%s | %s' % (command1, command2), user=jenkins)
    deploy_jenkins_plugins(repo=repo)


@task
def deploy_jenkins_plugins(repo):
    """Set up jenkins plugins post-installation.

    Deploying plugins with jenkins-cli seems not to be reliable
    For now if the plugins are not getting installed automatically
    we have to go to the webinterface and  install at least github and xvfb
    plugin manually before calling setup_jenkins_jobs.

    :param repo: repository to use
    :type repo: str
    """
    webpath = 'http://updates.jenkins-ci.org'
    distribution = repo
    if distribution == 'upstream':
        command = 'java -jar /var/cache/jenkins/war/WEB-INF/jenkins-cli.jar'

        run('%s -s http://localhost:8080 install-plugin '
            '%s/download/plugins/github/1.5/github.hpi'
            % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin %s/latest/xvfb.hpi'
            % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin '
            '%s/latest/violation-columns.hpi'
            % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin '
            '%s/latest/statusmonitor.hpi'
            % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin %s/latest/sounds.hpi'
            % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin '
            '%s/latest/maven-plugin.hpi'
            % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin '
            '%s/latest/covcomplplot.hpi'
            % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin %s/latest/cobertura.hpi'
            % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin '
            '%s/latest/dashboard-view.hpi'
            % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin %s/latest/sloccount.hpi'
            % (command, webpath))
        sudo('sudo service jenkins restart')
    else:
        command = 'jenkins-cli'
        # selecting a specific version
        run('%s -s http://localhost:8080 install-plugin '
            '%s/download/plugins/github/1.6/github.hpi' % (command, webpath))
        # just install the latest ones with jenkins-cli
        # running jenkins-cli that way not possible with latest jenkins
        run('%s -s http://localhost:8080 install-plugin xvfb' % command)
        run('%s -s http://localhost:8080 install-plugin violations' % command)
        run('%s -s http://localhost:8080 install-plugin statusmonitor' %
            command)
        run('%s -s http://localhost:8080 install-plugin sounds' % command)
        run('%s -s http://localhost:8080 install-plugin %s/maven-plugin/1.480'
            '.3/maven-plugin' % (command, webpath))
        run('%s -s http://localhost:8080 install-plugin covcomplplot' % command)
        run('%s -s http://localhost:8080 install-plugin cobertura' % command)
        run('%s -s http://localhost:8080 install-plugin dashboard-view' %
            command)
        run('%s -s http://localhost:8080 install-plugin sloccount' % command)
        sudo('sudo service jenkins restart')


@task
def install_jenkins(use_upstream_repo=False):
    """Add latest jenkins with adding jenkins project repository.

    .. note:: If you install only the distribution packaged version,
        some of the plugins listed in the configure_jenkins target may not
        install.

    :param use_upstream_repo: Whether to use the official jenkins repo or not.
        In the case of False, the distribution repo version will be used
        instead. Defaults to False.

    Example using the upstream jenkins repo::

        fab -H localhost fabgis.fabgis.install_jenkins:use_upstream_repo=True

    """
    if use_upstream_repo:
        repo = 'upstream'
        if fabtools.deb.is_installed('jenkins'):
            fabtools.deb.uninstall(['jenkins-common',
                                    'jenkins-cli',
                                    'libjenkins-remoting-java'], purge=True)
        add_jenkins_repository()
        fabtools.deb.update_index(quiet=True)
        sudo('apt-get install jenkins')
        #Jenkins needs time to come up
        time.sleep(5)
        configure_jenkins(repo)
    else:
        repo = 'distribution'
        if os.path.exists('/etc/apt/sources.list.d/jenkins-repository.list'):
            sudo('rm /etc/apt/sources.list.d/jenkins-repository.list')
        fabtools.deb.update_index(quiet=True)
        if fabtools.deb.is_installed('jenkins'):
            fabtools.deb.uninstall(['jenkins-common',
                                    'jenkins-cli',
                                    'libjenkins-remoting-java'], purge=True)
        fabtools.require.deb.package('jenkins')
        fabtools.require.deb.package('jenkins-common')
        fabtools.require.deb.package('jenkins-cli')
        #Jenkins needs time to come up
        time.sleep(5)
        configure_jenkins(repo)


@task
def jenkins_deploy_website(site_url=None):
    """
    Initialise jenkins with local proxy if we are not going to use port
    8080

    :param site_url: Name of the web site.
    :type site_url: str
    """
    setup_env()
    fabtools.require.deb.package('apache2')
    site_name = site_url

    if not site_name:
        site_name = 'jenkins'
    else:
        site_name = site_url

    jenkins_apache_conf = ('fabgis.%s.conf' % site_name)
    jenkins_apache_conf_template = 'fabgis.jenkins.conf.templ'

    with cd('/etc/apache2/sites-available/'):
        if not exists(jenkins_apache_conf):
            local_dir = os.path.dirname(__file__)
            local_file = os.path.abspath(os.path.join(
                local_dir,
                '..',
                'fabgis_resources',
                'server_config',
                'apache',
                jenkins_apache_conf_template))
            put(local_file,
                '/etc/apache2/sites-available/%s' %
                jenkins_apache_conf_template,
                use_sudo=True)

        my_tokens = {
            'SERVERNAME': env.fg.hostname,  # Web Url e.g. foo.com
            'WEBMASTER': 'werner@linfiniti.com',  # email of web master
            'SITENAME': site_name,  # Choosen name of jenkins 'root'
        }
        replace_tokens(jenkins_apache_conf_template, my_tokens)

    # Add a hosts entry for local testing - only really useful for localhost
    hosts = '/etc/hosts'
    if not contains(hosts, '%s.%s' % (site_name, env.fg.hostname)):
        append_if_not_present(hosts,
                              '127.0.1.1 %s.%s' % (site_name, env.fg.hostname),
                              use_sudo=True)
        append_if_not_present(hosts,
                              '127.0.0.1 %s.localhost' % env.fg.hostname,
                              use_sudo=True)
        # For doing Reverse Proxy we need to enable 2 apache modules
    sudo('a2enmod proxy')
    sudo('a2enmod proxy_http')
    sudo('a2ensite %s' % jenkins_apache_conf)
    sudo('service apache2 reload')

@task
def setup_jenkins_jobs(jobs, job_directory_path):
    """Setup jenkins to run Continuous Integration Tests.

    :param jobs: A list of job names to create.

    :param job_directory_path: Directory containing jenkins xml job
        definition files.

    """
    #fabgis.fabgis.initialise_jenkins_site()
    xvfb_config = "org.jenkinsci.plugins.xvfb.XvfbBuildWrapper.xml"

    with cd('/var/lib/jenkins/'):
        if not exists(xvfb_config):
            local_file = os.path.abspath(os.path.join(
                job_directory_path,
                'jenkins_jobs',
                xvfb_config))
            put(local_file,
                "/var/lib/jenkins/", use_sudo=True)

    with cd('/var/lib/jenkins/jobs/'):
        for job in jobs:
            if not exists(job):
                local_job_file = os.path.abspath(os.path.join(
                    job_directory_path,
                    '%s.xml' % job))
                sudo('mkdir /var/lib/jenkins/jobs/%s' % job)
                put(local_job_file,
                    "/var/lib/jenkins/jobs/%s/config.xml" % job,
                    use_sudo=True)
        sudo('chown -R jenkins:nogroup InaSAFE*')
    sudo('service jenkins restart')