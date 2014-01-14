# coding=utf-8
"""
QGIS related build tools.
=========================

"""
import os
from fabric.contrib.files import exists
from fabric.api import run, cd, env, task, sudo, fastprint
from fabric.colors import red, green, blue
from fabtools import require
from fabric.contrib.files import upload_template
import fabtools
from .common import add_ubuntugis_ppa
from .common import setup_env
from .git import update_git_checkout
from .system import setup_ccache
from .gdal import build_gdal
from .postgres import create_postgis_1_5_db


@task
def clone_qgis(branch='master', delete_local_branches=False):
    """Clone or update QGIS from git.

    :param branch: Name of the branch to build from. Defaults to 'master'
    :type branch: str

    :param delete_local_branches: Whether existing local branches should be
        pruned away from git.
    :type delete_local_branches: bool
    """
    setup_env()
    fabtools.require.deb.package('git')
    # Add this to the users git config so that we don't get repeated
    # authentication requests when using ssl
    #run('git config --global credential.helper \'cache --timeout=3600\'')
    #run('git config --global push.default simple')

    code_base = '%s/cpp' % env.fg.workspace
    code_path = '%s/QGIS' % code_base

    update_git_checkout(
        code_base,
        env.fg.qgis_git_url,
        'QGIS',
        branch)
    if exists(code_path):
        with cd(code_path):
            if delete_local_branches:
                run('git branch | grep -v \* | xargs git branch -D')


def compile_qgis(build_path, build_prefix, gdal_from_source=False):
    """Compile QGIS including installation of built tools and dependencies.


    :param build_path: Path to the cmake build dir that should be used. Path
        must point to under the QGIS git checkout dir. e.g.
        QGIS/build-fabgis.
    :type build_path: str

    :param build_prefix: Path where the QGIS binaries should be installed to.
        e.g. /usr/local/qgis-master
    :type build_prefix: str

    :param gdal_from_source: Whether gdal should be built from source.
        Default False.
    :type gdal_from_source: bool
    """

    fabtools.require.deb.package('cmake-curses-gui')
    fabtools.require.deb.package('grass-dev')
    fabtools.require.deb.package('grass')
    fabtools.require.deb.package('git')
    fabtools.require.deb.package('python-gdal')
    fabtools.require.deb.package('libfcgi-dev')
    # Ensure we always have a clean build dir
    if exists(build_path):
        run('rm -rf %s' % build_path)
    fabtools.require.directory(build_path)
    with cd(build_path):
        fabtools.require.directory(
            build_prefix,
            use_sudo=True,
            owner=env.fg.user)
        os_version = run('cat /etc/issue.net')
        os_version = float(os_version.split(' ')[1].split('.')[0])

        if os_version >= 13:
            extra = '-DPYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython2.7.so'
        else:
            extra = ''

        if gdal_from_source:
            build_gdal()  # see that task for ecw and mrsid support
            extra += '-DGDAL_CONFIG=/usr/local/bin/gdal-config '

        cmake = ('cmake .. '
                 '-DCMAKE_INSTALL_PREFIX=%s '
                 '-DCMAKE_CXX_COMPILER:FILEPATH=/usr/local/bin/g++ '
                 '-DQT_QMAKE_EXECUTABLE=/usr/bin/qmake-qt4 '
                 '-DWITH_MAPSERVER=ON '
                 '-DWITH_INTERNAL_SPATIALITE=ON '
                 '-DWITH_GRASS=OFF '
                 '-DCMAKE_BUILD_TYPE=Debug '
                 '%s'
                 % (build_prefix, extra))
        run(cmake)
        processor_count = run('cat /proc/cpuinfo | grep processor | wc -l')
        run('time make -j %s install' % processor_count)


@task
def install_qgis1_8(gdal_from_source=False):
    """
    Install QGIS 1.8 under /usr/local/qgis-1.8.

    :param gdal_from_source: Whether gdal should be built from source.
        Default False.
    :type gdal_from_source: bool


    """
    setup_env()
    add_ubuntugis_ppa()
    setup_ccache()
    sudo('apt-get build-dep -y qgis')
    fabtools.require.deb.package('libspatialindex-dev')
    clone_qgis(branch='release-1_8')
    workspace = '%s/cpp' % env.fg.workspace
    code_path = '%s/QGIS' % workspace
    build_path = '%s/build-qgis18-fabgis' % code_path
    build_prefix = '/usr/local/qgis-1.8'
    compile_qgis(build_path, build_prefix, gdal_from_source)


@task
def install_qgis2(gdal_from_source=False):
    """Install QGIS 2 under /usr/local/qgis-2.0.

    :param gdal_from_source: Whether gdal should be built from source.
        Default False.
    :type gdal_from_source: bool

    TODO: create one function from this and the 1.8 function above for DRY.

    """
    setup_env()
    setup_ccache()
    add_ubuntugis_ppa()
    sudo('apt-get build-dep -y qgis')

    #fabtools.require.deb.package('python-pyspatialite')
    fabtools.require.deb.package('python-psycopg2')
    fabtools.require.deb.package('python-qscintilla2')
    fabtools.require.deb.package('libqscintilla2-dev')
    fabtools.require.deb.package('libspatialindex-dev')

    clone_qgis(branch='release-2_0')
    workspace = '%s/cpp' % env.fg.workspace
    code_path = '%s/QGIS' % workspace
    build_path = '%s/build-qgis2-fabgis' % code_path
    build_prefix = '/usr/local/qgis-2.0'
    compile_qgis(build_path, build_prefix, gdal_from_source)


@task
def install_qgis_master(gdal_from_source=False):
    """Install QGIS master under /usr/local/qgis-master.

    :param gdal_from_source: Whether gdal should be built from source.
        Default False.
    :type gdal_from_source: bool

    TODO: create one function from this and the 1.8 function above for DRY.

    """
    setup_env()
    setup_ccache()
    add_ubuntugis_ppa()
    sudo('apt-get build-dep -y qgis')

    #fabtools.require.deb.package('python-pyspatialite')
    fabtools.require.deb.package('python-psycopg2')
    fabtools.require.deb.package('python-qscintilla2')
    fabtools.require.deb.package('libqscintilla2-dev')
    fabtools.require.deb.package('libspatialindex-dev')

    clone_qgis(branch='master')
    workspace = '%s/cpp' % env.fg.workspace
    code_path = '%s/QGIS' % workspace
    build_path = '%s/build-master-fabgis' % code_path
    build_prefix = '/usr/local/qgis-master'
    compile_qgis(build_path, build_prefix, gdal_from_source)


@task
def setup_qgis2_and_postgis():
    """
    Install qgis2 and postgis 1.5 as a fully working setup
    """
    create_postgis_1_5_db('gis', env.user)
    install_qgis2()


@task
def setup_qgis_server(
        site_name,
        web_root='/home/web/qgis-server',
        qgis_version='2.0',
        server_admin='none@none.com',
        template_dir=None,
        **kwargs):
    """Set up QGIS Server for QGIS.

    We assume your QGIS was built using fabgis into /usr/local/qgis-<version>.

    Place your projects in subdirectories of web root for them to be published.

    :param site_name: Name of the site e.g. qgis.linfiniti.com. Should be a
        single word with only alpha characters and dots in it.
    :type site_name: str

    :param web_root: Directory where the content lives.
    :type web_root: str

    :param qgis_version: The version you wish to server maps with. Currently
        supported values are '1.8', '2.0' and 'master'.
    :type qgis_version: str

    :param server_admin: Email address for the server admin. Defaults to
        none@none.com. This value is placed in the apache config file.
        No validation is performed.
    :type server_admin: str


    :param template_dir: Directory where the template files live. If none
        will default to ``resources/server_config/apache``. Must be a
        relative path to the fabfile you are running.
    :type template_dir: str

    :param kwargs: Any extra keyword arguments that should be appended to the
        token list that will be used when rendering the apache config template.
        Use this to pass in sensitive data such as passwords.
    :type kwargs: dict

    :returns: Path to the apache conf file.
    :rtype: str
    """
    setup_env()
    if qgis_version == '1.8':
        install_qgis1_8()
    elif qgis_version == '2.0':
        install_qgis2()
        pass
    elif qgis_version == 'master':
        install_qgis_master()
    else:
        raise Exception('Invalid QGIS version requested')
    # Clone and replace tokens in apache conf
    if template_dir is None:
        template_dir = os.path.join(
            os.path.dirname(__file__),
            'fabgis_resources', 'server_config', 'apache/')
    filename = 'qgis-server.conf.templ'
    template_path = os.path.join(template_dir, filename)
    fastprint(green('Using %s for template\n' % template_path))
    cgi_path = os.path.join(web_root, 'qgis-%s' % qgis_version)
    qgis_prefix = '/usr/local/qgis-%s' % qgis_version

    require.directory(cgi_path)
    with cd(cgi_path):
        qgis_binary = os.path.join(qgis_prefix, 'bin', 'qgis_mapserv.fcgi')

        if exists('qgis_mapserv.fcgi'):
            run('rm qgis_mapserv.fcgi')

        run('ln -s %s .' % qgis_binary)

    context = {
        'escaped_server_name': site_name.replace('.', '\.'),
        'server_name': site_name,
        'server_admin': server_admin,
        'web_root': web_root,
        'site_name': site_name,
        'cgi_path': cgi_path,
        'qgis_prefix': qgis_prefix}
    context.update(kwargs)  # merge in any params passed in to this function
    destination = '/etc/apache2/sites-available/%s.apache.conf' % site_name
    fastprint(green('Context: %s\n' % context))

    require.deb.packages(['apache2', 'libapache2-mod-fcgid'])

    upload_template(
        template_path,
        destination,
        context=context,
        use_sudo=True)

    sudo('a2dissite 000-default.conf')
    sudo('a2ensite %s.apache.conf' % site_name)
    # Check if apache configs are ok - script will abort if not ok
    sudo('/usr/sbin/apache2ctl configtest')
    require.service.restarted('apache2')
    sudo('chmod o+rX -R %s' % web_root)
    fastprint(green('Now upload your QGIS project file and data to\n'))
    fastprint(green('%s\n' % cgi_path))

    return destination