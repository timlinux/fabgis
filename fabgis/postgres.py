import fabtools
from fabtools.postgres import create_user
from fabric.api import run, cd, env, task, sudo, get, put
from .common import setup_env, show_environment, add_ubuntugis_ppa


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
    if not fabtools.postgres.user_exists(env.user):
        fabtools.postgres.create_user(
            user,
            password=password,
            createdb=True,
            createrole=True,
            superuser=True,
            connection_limit=20)


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
        create_user()
        setup_postgres_superuser(env.user)
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
    """Create a postgis database."""
    setup_postgis_1_5()
    setup_postgres_superuser(env.user)
    require_postgres_user(user)
    create_user()
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
def get_postgres_dump(dbname):
    """Get a dump of the database from teh server."""
    setup_env()
    date = run('date +%d-%B-%Y')
    my_file = '%s-%s.dmp' % (dbname, date)
    run('pg_dump -Fc -f /tmp/%s %s' % (my_file, dbname))
    get('/tmp/%s' % my_file, 'resources/sql/dumps/%s' % my_file)


@task
def restore_postgres_dump(dbname, user=None):
    """Upload dump to host, remove existing db, recreate then restore dump."""
    setup_env()
    if user is None:
        user = env.fg.user
    show_environment()
    require_postgres_user(user)
    create_user()
    date = run('date +%d-%B-%Y')
    my_file = '%s-%s.dmp' % (dbname, date)
    put('resources/sql/dumps/%s' % my_file, '/tmp/%s' % my_file)
    if fabtools.postgres.database_exists(dbname):
        run('dropdb %s' % dbname)
    fabtools.require.postgres.database(
        '%s' % dbname,
        owner='%s' % user,
        template='template_postgis',
        encoding='UTF8')
    run('pg_restore /tmp/%s | psql %s' % (my_file, dbname))
