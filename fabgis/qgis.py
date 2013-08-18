# coding=utf-8
"""QGIS related build tools."""
from fabric.contrib.files import exists
from fabric.api import run, cd, env, task, sudo
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
    code_path = '%s/Quantum-GIS' % code_base

    update_git_checkout(
        code_base,
        env.fg.qgis_git_url,
        'Quantum-GIS',
        branch)
    if exists(code_path):
        with cd(code_path):
            if delete_local_branches:
                run('git branch | grep -v \* | xargs git branch -D')


def compile_qgis(build_path, build_prefix, gdal_from_source=False):
    """Compile QGIS including installation of built tools and dependencies.


    :param build_path: Path to the cmake build dir that should be used. Path
        must point to under the QGIS git checkout dir. e.g.
        Quantum-GIS/build-fabgis.
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
        os_version = float(os_version.split(' ')[1])

        if os_version > 13:
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
                 '%s'
                 % (build_prefix, extra))
        run('cmake .. %s' % cmake)
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
    clone_qgis(branch='release-1_8')
    workspace = '%s/cpp' % env.fg.workspace
    code_path = '%s/Quantum-GIS' % workspace
    build_path = '%s/build-qgis18-fabgis' % code_path
    build_prefix = '/usr/local/qgis-1.8'
    compile_qgis(build_path, build_prefix, gdal_from_source)


@task
def install_qgis2(gdal_from_source=False):
    """Install QGIS 2 under /usr/local/qgis-master.

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
    code_path = '%s/Quantum-GIS' % workspace
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
