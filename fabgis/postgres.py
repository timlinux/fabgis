# coding=utf-8
"""
Postgres related fabric tasks.
==============================

"""
import os
import fabtools
from fabric.contrib.files import exists
from fabtools.postgres import create_user
from fabric.colors import red, green, blue
from fabric.api import run, cd, env, task, sudo, get, put, fastprint
from .common import setup_env, show_environment, add_ubuntugis_ppa
from .utilities import replace_tokens


@task
def require_postgres_user(user, password='', createdb=False):
    """ Require a postgres username to create a database
    :param user: username
    :param password: password
    :param createdb:  (default=False)
    :return:
    """
    #sudo('apt-get upgrade')
    # wsgi user needs pg access to the db
    if not fabtools.postgres.user_exists(user):
        # noinspection PyArgumentEqualDefault
        fabtools.postgres.create_user(
            name=user,
            password=password,
            superuser=False,
            createdb=createdb,
            createrole=False,
            inherit=True,
            login=True,
            connection_limit=None,
            encrypted_password=False)


def setup_postgres_superuser(user, password=''):
    """Create a super user for postgresql.

    :param user: User name for new super user.
    :param password:  Password for new user.
    """
    if not fabtools.postgres.user_exists(user):
        fabtools.postgres.create_user(
            user,
            password=password,
            createdb=True,
            createrole=True,
            superuser=True,
            connection_limit=20)


@task
def create_postgis_2_template():
    """Create the postgis 2 template db."""
    if not fabtools.postgres.database_exists('template_postgis'):
        setup_postgres_superuser(env.user)
        # noinspection PyArgumentEqualDefault
        fabtools.require.postgres.database(
            'template_postgis',
            owner='%s' % env.user,
            encoding='UTF8',
            locale='en_US.UTF-8')
        pg_path = '/usr/share/postgresql'
        pg_version = run('ls %s | head -1' % pg_path)
        pg_path = '%s/%s' % (pg_path, pg_version)

        postgis_version = run('ls %s/contrib/ | grep postgis' % pg_path)
        postgis_path = '%s/contrib/%s/' % (pg_path, postgis_version)

        fastprint(green('Creating template database for:\n'))
        fastprint(green('%s\n' % postgis_path))
        sql = ('UPDATE pg_database SET datistemplate = TRUE WHERE datname = '
               '\'template_postgis\';')
        run('psql template1 -c "%s"' % sql)

        run('psql template_postgis -f %s/postgis.sql' % postgis_path)
        run('psql template_postgis -f %s/spatial_ref_sys.sql' % postgis_path)
        grant_sql = 'GRANT ALL ON geometry_columns TO PUBLIC;'
        run('psql template_postgis -c "%s"' % grant_sql)
        grant_sql = 'GRANT ALL ON geography_columns TO PUBLIC;'
        run('psql template_postgis -c "%s"' % grant_sql)
        grant_sql = 'GRANT ALL ON spatial_ref_sys TO PUBLIC;'
        run('psql template_postgis -c "%s"' % grant_sql)
    else:
        fastprint(red('template_postgis already exists!\n'))


@task
def setup_postgis_2(from_source=False):
    """Set up postgis 2.0 from packages in ubuntugis or from source.

    :param from_source: Whether postgis should be built from source.
    :type from_source: bool

    .. versionadded:: 0.17.0
        from_source parameter added
    """
    if from_source:
        setup_postgis_latest()
    else:
        add_ubuntugis_ppa()
        fabtools.require.deb.package('build-essential')
        fabtools.require.deb.package('postgresql-9.1-postgis-2.0')
        fabtools.require.deb.package('postgresql-9.1-postgis-2.0-scripts')
        fabtools.require.deb.package('postgresql-server-dev-all')
        create_postgis_2_template()


@task
def setup_postgis_latest():
    """Set up postgis latest package from source..

    You can call this multiple times without it actually installing all over
    again each time since it checks for the presence of pgis first.

    We build from source because we want the latest build

    I'm using this together with the postgresql repo here:

    deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main

    which provides pg 9.3 at time of writing this.

    .. versionadded:: 0.17.0
    """
    setup_env()

    pg_file = '/usr/share/postgresql/9.3/contrib/postgis-2/postgis.sql'
    if not fabtools.files.is_file(pg_file):
        add_ubuntugis_ppa()
        fabtools.require.deb.package('postgresql-server-dev-9.3')
        fabtools.require.deb.package('build-essential')

        # Note - no postgis installation from package as we want to build 1.5
        # from source
        fabtools.require.postgres.server()

        # Now get and install postgis 1.5 if needed

        fabtools.require.deb.package('libxml2-dev')
        fabtools.require.deb.package('libgeos-dev')
        fabtools.require.deb.package('libgdal1-dev')
        fabtools.require.deb.package('libproj-dev')
        source_url = ('http://download.osgeo.org/postgis/source/'
                      'postgis-2.1.1.tar.gz')
        source = 'postgis-2.1.1'
        if not fabtools.files.is_file('%s.tar.gz' % source):
            run('wget %s' % source_url)
            run('tar xfz %s.tar.gz' % source)
        with cd(source):
            run('./configure')
            run('make')
            sudo('make install')

    create_postgis_2_template()


@task
def setup_postgis_1_5():
    """Set up postgis.

    You can call this multiple times without it actually installing all over
    again each time since it checks for the presence of pgis first.

    We build from source because we want 1.5"""
    setup_env()

    pg_file = '/usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql'
    if not fabtools.files.is_file(pg_file):
        add_ubuntugis_ppa()
        fabtools.require.deb.package('postgresql-server-dev-all')
        fabtools.require.deb.package('build-essential')

        # Note - no postgis installation from package as we want to build 1.5
        # from source
        fabtools.require.postgres.server()

        # Now get and install postgis 1.5 if needed

        fabtools.require.deb.package('libxml2-dev')
        fabtools.require.deb.package('libgeos-dev')
        fabtools.require.deb.package('libgdal1-dev')
        fabtools.require.deb.package('libproj-dev')
        source_url = ('http://download.osgeo.org/postgis/source/'
                      'postgis-1.5.8.tar.gz')
        source = 'postgis-1.5.8'
        if not fabtools.files.is_file('%s.tar.gz' % source):
            run('wget %s' % source_url)
            run('tar xfz %s.tar.gz' % source)
        with cd(source):
            run('./configure')
            run('make')
            sudo('make install')

    create_postgis_1_5_template()


@task
def create_postgis_1_5_template():
    """Create the postgis template db."""
    if not fabtools.postgres.database_exists('template_postgis'):
        setup_postgres_superuser(env.user)
        # noinspection PyArgumentEqualDefault
        fabtools.require.postgres.database(
            'template_postgis',
            owner='%s' % env.user,
            encoding='UTF8')
        sql = ('UPDATE pg_database SET datistemplate = TRUE WHERE datname = '
               '\'template_postgis\';')
        run('psql template1 -c "%s"' % sql)
        run('psql template_postgis -f /usr/share/postgresql/'
            '9.1/contrib/postgis-1.5/postgis.sql')
        run('psql template_postgis -f /usr/share/postgresql/9'
            '.1/contrib/postgis-1.5/spatial_ref_sys.sql')
        grant_sql = 'GRANT ALL ON geometry_columns TO PUBLIC;'
        run('psql template_postgis -c "%s"' % grant_sql)
        grant_sql = 'GRANT ALL ON geography_columns TO PUBLIC;'
        run('psql template_postgis -c "%s"' % grant_sql)
        grant_sql = 'GRANT ALL ON spatial_ref_sys TO PUBLIC;'
        run('psql template_postgis -c "%s"' % grant_sql)


@task
def create_postgis_1_5_db(dbname, user):
    """Create a postgis database.
    :param dbname: Name of database to create.
    :param user: User who should own the created db
    """
    setup_postgis_1_5()
    setup_postgres_superuser(env.user)
    require_postgres_user(user)
    fabtools.require.postgres.database(
        '%s' % dbname, owner='%s' % user, template='template_postgis')

    grant_sql = 'GRANT ALL ON schema public to %s;' % user
    # assumption is env.repo_alias is also database name
    run('psql %s -c "%s"' % (dbname, grant_sql))
    grant_sql = (
        'GRANT ALL ON ALL TABLES IN schema public to %s;' % user)
    # assumption is env.repo_alias is also database name
    run('psql %s -c "%s"' % (dbname, grant_sql))
    grant_sql = (
        'GRANT ALL ON ALL SEQUENCES IN schema public to %s;' % user)
    run('psql %s -c "%s"' % (dbname, grant_sql))


@task
def get_postgres_dump(dbname, ignore_permissions=False, file_name=None):
    """Get a dump of the database from the server.

    :param dbname: name of the database to restore the dump into.
    :type dbname: str

    :param ignore_permissions: whether permissions in the created dump
        should be preserved.
    :type ignore_permissions: bool (default False)

    :param file_name: optional file name for the dump. The file name should
        exclude any path. If file_name is ommitted, the dump will be written to
        fabgis_resources/sql/dumps/<dbname>->date>.dmp
        where date is in the form dd-mm-yyyy. This is the default naming
        convention used by the :func:`restore_postgres_dump` function below.
    :type file_name: str
    """
    setup_env()

    if file_name is None or file_name == '':
        date = run('date +%d-%B-%Y')
        my_file = '%s-%s.dmp' % (dbname, date)
    else:
        my_file = os.path.split(file_name)[1]
        put(file_name, '/tmp/%s' % my_file)

    if not ignore_permissions:
        extra_args = ''
    else:
        extra_args = '-x -O'

    run('pg_dump %s -Fc -f /tmp/%s %s' % (extra_args, my_file, dbname))
    get('/tmp/%s' % my_file, 'fabgis_resources/sql/dumps/%s' % my_file)


@task
def restore_postgres_dump(
        dbname,
        user=None,
        password='',
        ignore_permissions=False,
        file_name=None):
    """Upload dump to host, remove existing db, recreate then restore dump.

    :param dbname: name of the database to restore the dump into.
    :type dbname: str

    :param user: user that the db should be restored for. The db user
        will be used when restoring the db and the user will be created first
        if needed.
    :type user: str

    :param password: password to use for db connection - defaults to ''
    :type password: str

    :param ignore_permissions: whether permissions in the restored dump
        should be retained.
    :type ignore_permissions: bool (default False)

    :param file_name: optional file name for the dump. If ommitted,
        the dump will be assumed to exist in
        fabgis_resources/sql/dumps/<dbname>->date>.dmp
        where date is in the form dd-mm-yyyy. This is the default naming
        convention used by the :func:`get_postgres_dump` function above.
    :type file_name: str
    """
    setup_env()
    fastprint(green('Restoring to database: %s\n' % dbname))

    if user is None:
        user = env.fg.user
    show_environment()
    fastprint(green('Checking user exists\n'))
    require_postgres_user(user, password=password)
    if file_name is None or file_name == '':
        date = run('date +%d-%B-%Y')
        my_file = '%s-%s.dmp' % (dbname, date)
        put('fabgis_resources/sql/dumps/%s' % my_file, '/tmp/%s' % my_file)
    else:
        my_file = os.path.split(file_name)[1]
        put(file_name, '/tmp/%s' % my_file)
    fastprint(green('Restoring from file: %s\n' % file_name))

    if fabtools.postgres.database_exists(dbname):
        fastprint(red('Dropping existing db: %s\n' % dbname))
        run('dropdb %s' % dbname)

    fastprint(green('Creating database: %s\n' % dbname))
    # noinspection PyArgumentEqualDefault
    fabtools.require.postgres.database(
        '%s' % dbname,
        owner='%s' % user,
        template='template_postgis',
        encoding='UTF8')

    if not ignore_permissions:
        extra_args = ''
    else:
        fastprint(blue('Ignoring permissions\n'))
        extra_args = '-x -O'

    fastprint(green('Starting restore...\n'))
    run('pg_restore %s /tmp/%s | psql %s' % (extra_args, my_file, dbname))
    fastprint(green('Restore completed.\n'))


@task
def compile_osm2pgsql():
    """From-source compile of osm2pgsql.

    We build from source so we can use recent postgresql packages.

    See: http://wiki.openstreetmap.org/wiki/Osm2pgsql#From_source
    """
    add_ubuntugis_ppa()
    fabtools.require.deb.packages([
        'build-essential',
        'libxml2-dev',
        'libgeos++-dev',
        'libpq-dev',
        'libbz2-dev',
        'libproj-dev',
        'libtool',
        'automake',
        'subversion',
        'libprotobuf-c0-dev',
        'protobuf-c-compiler',
        'lua5.2',
        'liblua5.2-0',
        'liblua5.2-dev',
        'liblua5.1-0',
    ])
    with cd('/tmp'):
        if not exists('osm2pgsql'):
            run('git clone https://github.com/openstreetmap/osm2pgsql.git')

    with cd('/tmp/osm2pgsql'):
        run('./autogen.sh')
        run('./configure')
        run('make -j4')
        sudo('make install')


@task
def setup_nightly_backups():
    """Setup nightly backups for all postgresql databases.

    The template script :file:`fabgis_resources/server_config/cron/pg_backups`
    will place the last 21 days of backups in the remote user's Dropbox
    directory and will maintain 6 months of backups in their home directory.

    .. seealso:: fabgis.dropbox for help on setting up dropbox on your server.
    """
    setup_env()
    setup_postgres_superuser(env.fg.user)
    with cd('/etc/cron.daily/'):
        if exists('pg_backups'):
            sudo('rm pg_backups')

        local_dir = os.path.dirname(__file__)
        local_file = os.path.abspath(os.path.join(
            local_dir,
            '..',
            'fabgis_resources',
            'server_config',
            'cron',
            'pg_backups.templ'))
        put(local_file,
            '/etc/cron.daily/pg_backups',
            use_sudo=True)

        my_tokens = {'USER': env.fg.user, }
        replace_tokens('/etc/cron.daily/pg_backups', my_tokens)

    sudo('chmod +x /etc/cron.daily/pg_backups')
    # Run once to verify it works
    sudo('/etc/cron.daily/pg_backups')
