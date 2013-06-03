from fabric.contrib.files import exists
import fabtools
from fabric.api import fastprint, run, cd, env, task, sudo
from .utilities import append_if_not_present, update_git_checkout
from .postgres import require_postgres_user
from .common import setup_env


@task
def setup_kandan(
        branch='master',
        user='kandan',
        password='kandan'):
    """Set up the kandan chat server - see https://github.com/kandanapp/kandan.

    .. note:: I recommend setting up kandan in a vagrant instance."""
    setup_env()
    fabtools.require.deb.package('git')
    code_base = '%s/ruby' % env.fg.workspace
    code_path = '%s/kandan' % code_base

    update_git_checkout(code_base, env.fg.kandan_git_url, 'kandan', branch)

    fabtools.require.postgres.server()
    require_postgres_user(
        user=user,
        password=password,
        createdb=True,
    )

    with cd(code_path):
        fabtools.require.deb.package('ruby1.9.1-dev')
        fabtools.require.deb.package('libxslt-dev')
        fabtools.require.deb.package('libxml2-dev')
        fabtools.require.deb.package('libpq-dev')
        fabtools.require.deb.package('libsqlite3-dev')
        fabtools.require.deb.package('nodejs')
        # Newer distros
        #fabtools.require.deb.package('bundler')
        # ub 12.04
        fabtools.require.deb.package('ruby-bundler')
        fabtools.require.deb.package('')
        sudo('gem install execjs')
        append_if_not_present('config/database.yml', 'production:')
        append_if_not_present('config/database.yml', '  adapter: postgresql')
        append_if_not_present('config/database.yml', '  host: localhost')
        append_if_not_present(
            'config/database.yml', '  database: kandan_production')
        append_if_not_present('config/database.yml', '  pool: 5')
        append_if_not_present('config/database.yml', '  timeout: 5000')
        append_if_not_present('config/database.yml', '  username: kandan')
        append_if_not_present(
            'config/database.yml', '  password: %s' % password)
        #run('RUBYLIB=/usr/lib/ruby/1.9.1/rubygems bundle exec rake db:create '
        run('bundle exec rake db:create db:migrate kandan:bootstrap')

    fastprint('Kandan server setup is complete. Use ')
    fastprint('fab <target> fabgis.fabgis.start_kandan')
    fastprint('to start the server.')


@task
def start_kandan():
    """Start the kandan server - it will run on port 3000."""
    setup_env()
    code_base = '%s/ruby' % env.fg.workspace
    code_path = '%s/kandan' % code_base
    if not exists(code_path):
        setup_kandan()
    else:
        with cd(code_path):
            run('bundle exec thin start')
