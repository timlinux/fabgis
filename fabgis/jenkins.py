import os
import time
from fabric.contrib.files import contains, exists
from fabric.api import run, cd, env, task, sudo, put
import fabtools
from .utilities import append_if_not_present, replace_tokens
from .common import setup_env


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
    """
    We have to update the json file if we want to switch between distribution
    provided jenkins and upstream jenkins
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
    """
    Deploying plugins with jenkins-cli seems not to be reliable
    For now if the plugins are not getting installed automatically
    we have to go to the webinterface and  install at least github and xvfb
    plugin manually before calling setup_jenkins_jobs
    :param repo: repository to use
    :return:
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

    Args:
        use_upstream_repo - bool: (defaults to False). Whether to use the
        official jenkins repo or not. In the case of False,
        the distribution repo version will be used instead.

    Example:
        Using the upstream jenkins repo:
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
def jenkins_deploy_website(site_url=None, use_upstream_repo=False):
    """
    Initialise jenkins with local proxy if we are not going to use port
    8080
    """
    setup_env()
    fabtools.require.deb.package('apache2')
    sitename = site_url

    if not sitename:
        sitename = 'jenkins'
    else:
        sitename = site_url

    jenkins_apache_conf = ('fabgis.%s.conf' % (sitename))
    jenkins_apache_conf_template = 'fabgis.jenkins.conf.templ'

    with cd('/etc/apache2/sites-available/'):
        if not exists(jenkins_apache_conf):
            local_dir = os.path.dirname(__file__)
            local_file = os.path.abspath(os.path.join(
                local_dir,
                '..',
                '../fabgis_resources',
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
            'SITENAME': sitename,  # Choosen name of jenkins 'root'
        }
        replace_tokens(jenkins_apache_conf_template, my_tokens)

    # Add a hosts entry for local testing - only really useful for localhost
    hosts = '/etc/hosts'
    if not contains(hosts, '%s.%s' % (sitename, env.fg.hostname)):
        append_if_not_present(hosts,
                              '127.0.1.1 %s.%s' % (sitename, env.fg.hostname),
                              use_sudo=True)
        append_if_not_present(hosts,
                              '127.0.0.1 %s.localhost' % env.fg.hostname,
                              use_sudo=True)
        # For doing Reverse Proxy we need to enable 2 apache modules
    sudo('a2enmod proxy')
    sudo('a2enmod proxy_http')
    sudo('a2ensite %s' % jenkins_apache_conf)
    sudo('service apache2 reload')
