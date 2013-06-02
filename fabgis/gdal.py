from .system import setup_ccache
import fabtools
from fabric.contrib.files import exists, append
from common import add_ubuntugis_ppa, setup_env
from fabric.api import fastprint, run, cd, env, task, sudo, settings


@task
def build_gdal(with_ecw=False, with_mrsid=False):
    """Clone or update GDAL from svn then build it.

    :rtype: None
    """
    setup_env()
    add_ubuntugis_ppa()
    fabtools.require.deb.package('subversion')
    fabtools.require.deb.package('build-essential')
    setup_ccache()
    fabtools.require.deb.package('libhdf5-serial-dev')
    fabtools.require.deb.package('libhdf5-7')
    fabtools.require.deb.package('libhdf4g-dev')
    fabtools.require.deb.package('libjpeg62-dev')
    fabtools.require.deb.package('libtiff4-dev')
    fabtools.require.deb.package('python-dev')

    code_base = '%s/cpp' % env.fg.workspace
    code_path = '%s/gdal' % code_base
    if not exists(code_path):
        fastprint('Repo checkout does not exist, creating.')
        run('mkdir -p %s' % code_base)
        with cd(code_base):
            run('svn co %s gdal' % env.fg.gdal_svn_url)
    else:
        fastprint('Repo checkout does exist, updating.')
        with cd(code_path):
            # Get any updates first
            run('svn update')

    flags = (
        '--with-libtiff=internal '
        '--with-geotiff=internal '
        '--with-python '
        '--without-jp2mrs '
        '--with-spatialite '
        '--without-libtool')

    processor_count = run('cat /proc/cpuinfo | grep processor | wc -l')

    # Currently you need to have downloaded the MRSID sdk to remote home dir
    if with_mrsid:
        mrsid_dir = '/usr/local/GeoExpressSDK'
        if not exists(mrsid_dir):
            sudo('tar xfz /home/%s/Geo_DSDK-7.0.0.2167.linux.x86-64.gcc41.'
                 'tar.gz -C /tmp' % env.user)
            sudo('mv /tmp/Geo_DSDK-7.0.0.2167 %s' % mrsid_dir)
        flags += ' --with-mrsid=%s' % mrsid_dir

    # Currently you need to have downloaded the ECW sdk to remote home dir
    if with_ecw:
        ecw_dir = '%s/ecw/libecwj2-3.3' % code_base
        ecw_archive = 'ecw.tar.bz2'
        if not exists(ecw_dir):
            with cd(code_base):
                run('tar xfj ~/%s' % ecw_archive)
        if not exists('/usr/local/include/ECW.h'):
            with cd(ecw_dir):
                run('./configure')
                run('make -j %s' % processor_count)
                sudo('make install')
        flags += ' --with-ecw=/usr/local'

    with cd(code_path):
        # Dont fail if make clean does not work
        with settings(warn_only=True):
            run('make clean')
        run('CXXFLAGS=-fPIC ./configure %s' % flags)
        run('make -j %s' % processor_count)
        sudo('make install')
    # Write to ld path too so libs are loaded nicely
    ld_file = '/etc/ld.so.conf.d/usr_local_lib.conf'
    with settings(warn_only=True):
        sudo('rm %s' % ld_file)
    append(ld_file, '/usr/local/lib', use_sudo=True)
    sudo('ldconfig')
