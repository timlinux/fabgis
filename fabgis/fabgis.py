import os
from fabric.api import *
from fabric.utils import _AttributeDict as fdict
from fabric.contrib.files import contains, exists, append, sed
import fabtools
# Don't remove even though its unused
from fabtools.vagrant import vagrant
env.roledefs = {
    'test': ['localhost'],
    'dev': ['none@none.com'],
    'staging': ['none@none.com'],
    'production': ['none@none.com']
}

env.fg = None


def setup_env():
    """Things to do regardless of whether command is local or remote."""
    if env.fg is not None:
        fastprint('Environment already set!\n')
        return

    fastprint('Setting environment!\n')
    env.fg = fdict()
    with hide('output'):
        env.fg.user = run('whoami')
        env.fg.hostname = fabtools.system.get_hostname()
        env.fg.home = os.path.join('/home/', env.fg.user)
        env.fg.workspace = os.path.join(env.fg.home, 'dev')
        env.fg.inasafe_git_url = 'git://github.com/AIFDR/inasafe.git'
        env.fg.qgis_git_url = 'git://github.com/qgis/Quantum-GIS.git'
        env.fg.kandan_git_url = 'git://github.com/kandanapp/kandan.git'
        env.fg.inasafe_checkout_alias = 'inasafe-fabric'
        env.fg.qgis_checkout_alias = 'qgis-fabric'
        env.fg.inasafe_code_path = os.path.join(
            env.fg.workspace, env.fg.inasafe_checkout_alias)
        env.fg.qgis_code_path = os.path.join(
            env.fg.workspace, env.fg.qgis_checkout_alias)


@task
def setup_venv(requirements_file='requirements.txt'):
    """Initialise or update the virtual environmnet.


    To run e.g.::

        fab -H 192.168.1.1:2222 remote setup_venv

    or if you have configured env.hosts, simply

        fab remote setup_venv
    """
    setup_env()
    with cd(env.code_path):
        # Ensure we have a venv set up
        fabtools.require.python.virtualenv('venv')
        run('venv/bin/pip install -r %s' % requirements_file)


@task
def show_environment():
    """For diagnostics - show any pertinent info about server."""
    setup_env()
    fastprint('\n-------------------------------------------------\n')
    for key, value in env.fg.iteritems():
        fastprint('Key: %s \t\t Value: %s' % (key, value))
    fastprint('-------------------------------------------------\n')


@task
def add_ubuntugis_ppa():
    """Ensure we have ubuntu-gis repos."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.ppa(
        #'ppa:ubuntugis/ubuntugis-unstable', auto_yes=True)
        'ppa:ubuntugis/ubuntugis-unstable')


@task
def setup_latex():
    """Install latex and friends needed to generate sphinx pdfs."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.package('texlive-latex-extra')
    fabtools.require.deb.package('texinfo')
    fabtools.require.deb.package('texlive-fonts-recommended')


@task
def setup_sphinx():
    """Install sphinx from pip.

    We prefer from pip as ubuntu packages are usually old."""
    sudo('pip install sphinx')


@task
def setup_transifex():
    """Install transifex client."""
    sudo('pip install transifex-client')


@task
def setup_devtools():
    """Install various useful tools needed for developers."""
    fabtools.require.deb.package('qtcreator')
    fabtools.require.deb.package('qt4-designer')
    fabtools.require.deb.package('qt4-linguist-tools')


@task
def clone_qgis(branch='master'):
    """Clone or update QGIS from git.

    :param branch: the name of the branch to build from. Defaults to 'master'
    :type branch: basestring

    :rtype: None
    """
    setup_env()
    fabtools.require.deb.package('git')
    # Add this to the users git config so that we don't get repeated
    # authentication requests when using ssl
    run('git config --global credential.helper \'cache --timeout=3600\'')
    run('git config --global push.default simple')

    code_base = '%s/cpp' % env.fg.workspace
    code_path = '%s/Quantum-GIS' % code_base
    if not exists(code_path):
        fastprint('Repo checkout does not exist, creating.')
        run('mkdir -p %s' % code_base)
        with cd(code_base):
            run('git clone %s' % env.fg.qgis_git_url)
    else:
        fastprint('Repo checkout does exist, updating.')
        with cd(code_path):
            # Get any updates first
            run('git fetch')
            # Get rid of any local changes
            run('git reset --hard')
            # Get back onto master branch
            run('git checkout master')
            # Remove any local changes in master
            run('git reset --hard')
            # Delete all local branches
            run('git branch | grep -v \* | xargs git branch -D')

    with cd(code_path):
        if branch != 'master':
            run('git branch --track %s origin/%s' % (branch, branch))
            run('git checkout %s' % branch)
        else:
            run('git checkout master')
        run('git pull')


@task
def setup_ccache():
    """Setup ccache."""
    fabtools.require.deb.package('ccache')
    sudo('ln -fs /usr/bin/ccache /usr/local/bin/gcc')
    sudo('ln -fs /usr/bin/ccache /usr/local/bin/g++')
    sudo('ln -fs /usr/bin/ccache /usr/local/bin/cc')


@task
def setup_inasafe():
    """Setup requirements for InaSAFE."""
    fabtools.require.deb.package('pep8')
    fabtools.require.deb.package('pylint')
    fabtools.require.deb.package('python-nose')
    fabtools.require.deb.package('python-nosexcover')


def compile_qgis(build_path, build_prefix):
    fabtools.require.deb.package('python-gdal')
    fabtools.require.deb.package('cmake-curses-gui')
    fabtools.require.deb.package('git')
    fabtools.require.directory(build_path)
    with cd(build_path):
        fabtools.require.directory(
            build_prefix,
            use_sudo=True,
            owner=env.fg.user)
        os_version = run('cat /etc/issue.net')
        os_version == float(os_version.split(' ')[1])
        if os_version > 13:
            extra = '-DPYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython2.7.so'
        else:
            extra = ''
        cmake = ('cmake .. '
                 '-DCMAKE_INSTALL_PREFIX=%s '
                 '-DCMAKE_CXX_COMPILER:FILEPATH=/usr/local/bin/g++ '
                 '-DQT_QMAKE_EXECUTABLE=/usr/bin/qmake-qt4 '
                 '-DWITH_MAPSERVER=ON '
                 '-DWITH_INTERNAL_SPATIALITE=ON '
                 '%s'
                 % (build_prefix, extra))
        run('cmake .. %s' % cmake)
        processor_count = run('cat /proc/cpuinfo | grep processor | wc -l')
        run('time make -j %s install' % processor_count)


@task
def install_qgis1_8():
    """Install QGIS 1.8 under /usr/local/qgis-1.8."""
    setup_env()
    add_ubuntugis_ppa()
    setup_ccache()
    sudo('apt-get build-dep -y qgis')
    clone_qgis(branch='release-1_8')
    workspace = '%s/cpp' % env.fg.workspace
    code_path = '%s/Quantum-GIS' % workspace
    build_path = '%s/build-qgis18' % code_path
    build_prefix = '/usr/local/qgis-1.8'
    compile_qgis(build_path, build_prefix)


@task
def install_qgis2():
    """Install QGIS 2 under /usr/local/qgis-master.

    TODO: create one function from this and the 1.8 function above for DRY.

    """
    setup_env()
    setup_ccache()
    add_ubuntugis_ppa()
    sudo('apt-get build-dep -y qgis')

    fabtools.require.deb.package('python-pyspatialite')
    fabtools.require.deb.package('python-psycopg2')
    fabtools.require.deb.package('python-qscintilla2')
    fabtools.require.deb.package('libqscintilla2-dev')
    fabtools.require.deb.package('libspatialindex-dev')

    clone_qgis(branch='master')
    workspace = '%s/cpp' % env.fg.workspace
    code_path = '%s/Quantum-GIS' % workspace
    build_path = '%s/build-master' % code_path
    build_prefix = '/usr/local/qgis-master'
    compile_qgis(build_path, build_prefix)


@task
def setup_qgis2_and_postgis():
    create_postgis_1_5_db('gis', env.user)
    install_qgis2()


@task
def require_postgres_user(user, password='', createdb=False):
    #sudo('apt-get upgrade')
    # wsgi user needs pg access to the db
    if not fabtools.postgres.user_exists(user):
        fabtools.postgres.create_user(
            name=user,
            password=password,
            superuser=False,
            createdb=True,
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


@task
def create_user():
    """Create a user on the remote system matching the user running this task.
    """
    fabtools.require.users.user(env.user)
    fabtools.require.users.sudoer(env.user)


@task
def setup_kandan(branch='master', user='kandan', password='kandan'):
    """Set up the kandan chat server - see https://github.com/kandanapp/kandan.

    .. note:: I recommend setting up kandan in a vagrant instance."""
    setup_env()
    fabtools.require.deb.package('git')
    code_base = '%s/ruby' % env.fg.workspace
    code_path = '%s/kandan' % code_base
    if not exists(code_path):
        fastprint('Repo checkout does not exist, creating.')
        run('mkdir -p %s' % code_base)
        with cd(code_base):
            run('git clone %s' % env.fg.kandan_git_url)
    else:
        fastprint('Repo checkout does exist, updating.')
        with cd(code_path):
            # Get any updates first
            run('git fetch')
            # Get rid of any local changes
            run('git reset --hard')
            # Get back onto master branch
            run('git checkout master')
            # Remove any local changes in master
            run('git reset --hard')
            # Delete all local branches
            run('git branch | grep -v \* | xargs git branch -D')

    with cd(code_path):
        if branch != 'master':
            run('git branch --track %s origin/%s' % (branch, branch))
            run('git checkout %s' % branch)
        else:
            run('git checkout master')
        run('git pull')

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
        append('config/database.yml', 'production:')
        append('config/database.yml', 'adapter: postgresql')
        append('config/database.yml', 'host: localhost')
        append('config/database.yml', 'database: kandan_production')
        append('config/database.yml', 'pool: 5')
        append('config/database.yml', 'timeout: 5000')
        append('config/database.yml', 'username: kandan')
        append('config/database.yml', 'password: %s' % password)
        run('RUBYLIB=/usr/lib/ruby/1.9.1/rubygems bundle exec rake db:create '
            'db:migrate kandan:bootstrap')

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
        with code_path:
            run('bundle exec thin start')


@task
def ssh_copy_id():
    """Copy ssh id from local system to remote.
    .. note:: Does not work on OSX!
    """
    command = 'ssh-copy-id %s' % env.host
    local(command)


@task
def harden(ssh_port=22):
    """Harden the server a little.

    Warning: We make no claim that this makes your server intruder proof. You
    should always check any system yourself and make sure that it is
    adequately secured.

    """
    fabtools.deb.update_index(quiet=True)
    #print fabtools.system.get_hostname()
    #ssh_copy_id()

    # Set up ufw and mosh
    fabtools.require.deb.package('ufw')
    mosh_file = '/etc/ufw/applications.d/mosh'
    if not exists(mosh_file):
        sudo('touch %s' % mosh_file)

        append(mosh_file, '[mosh]', use_sudo=True)
        append(mosh_file, ('title=Mobile shell that supports roaming and '
                           'intelligent local echo.'), use_sudo=True)
        append(mosh_file, ('description=The mosh provides alternative remote '
                           'shell that supports roaming and intelligent local '
                           'echo.'), use_sudo=True)
        append(mosh_file, 'ports=60000:61000/udp', use_sudo=True)
    fabtools.require.deb.package('mosh')

    sudo('ufw default deny incoming')
    sudo('ufw default allow outgoing')
    sudo('ufw allow 8697')
    sudo('ufw allow http')
    sudo('ufw allow ssh')
    sudo('ufw allow mosh')
    sudo('ufw allow 25')  # mail
    #Irc freenode
    sudo('ufw allow from 127.0.0.1/32 to 78.40.125.4 port 6667')
    sudo('ufw allow from 127.0.0.1/32 to any port 22')
    sudo('ufw allow 443')
    sudo('ufw allow 53/udp')  # dns
    sudo('ufw allow 53/tcp')
    sudo('ufw allow 1053')  # dns client

    sed('/etc/ssh/sshd_config', 'Port 22', 'Port 8697', use_sudo=True)
    sed('/etc/ssh/sshd_config', 'PermitRootLogin yes',
        'PermitRootLogin no', use_sudo=True)
    sed('/etc/ssh/sshd_config', '#PasswordAuthentication yes',
        'PasswordAuthentication no', use_sudo=True)
    sed('/etc/ssh/sshd_config', 'X11Forwarding yes',
        'X11Forwarding no', use_sudo=True)
    sudo('ufw enable')

    append('/etc/ssh/sshd_config', 'Banner /etc/issue.net', use_sudo=True)

    append_if_not_present(
        '/etc/sysctl.conf',
        'net.ipv4.conf.default.rp_filter=1', use_sudo=True)
    append_if_not_present(
        '/etc/sysctl.conf',
        'net.ipv4.conf.setup_env.rp_filter=1', use_sudo=True)
    append_if_not_present(
        '/etc/sysctl.conf',
        'net.ipv4.conf.setup_env.accept_redirects = 0', use_sudo=True)
    append_if_not_present(
        '/etc/sysctl.conf',
        'net.ipv4.conf.setup_env.send_redirects = 0', use_sudo=True)
    append_if_not_present(
        '/etc/sysctl.conf',
        'net.ipv4.conf.setup_env.accept_source_route = 0', use_sudo=True)
    append_if_not_present(
        '/etc/sysctl.conf',
        'net.ipv4.icmp_echo_ignore_broadcasts = 1', use_sudo=True)
    append_if_not_present(
        '/etc/sysctl.conf',
        'net.ipv4.icmp_ignore_bogus_error_responses = 1', use_sudo=True)

    fabtools.require.deb.package('denyhosts')
    fabtools.require.deb.package('mailutils')
    fabtools.require.deb.package('byobu')
    fabtools.service.restart('ssh')

    # Some hints and tips from:
    # http://www.thefanclub.co
    # .za/how-to/how-secure-ubuntu-1204-lts-server-part-1-basics
    secure_tmp = (
        'tmpfs     /dev/shm     tmpfs     defaults,noexec,'
        'nosuid     0     0')
    append('/etc/fstab', secure_tmp, use_sudo=True)

    if not contains('/etc/group', 'admin'):
        sudo('groupadd admin')
    sudo('usermod -a -G admin %s' % env.user)
    sudo('dpkg-statoverride --update --add root admin 4750 /bin/su')

    sysctl = '/etc/sysctl.conf'

    append_if_not_present(
        sysctl, '# IP Spoofing protection', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.conf.setup_env.rp_filter = 1', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.conf.default.rp_filter = 1', use_sudo=True)

    append_if_not_present(
        sysctl, '# Ignore ICMP broadcast requests', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.icmp_echo_ignore_broadcasts = 1', use_sudo=True)

    append_if_not_present(
        sysctl, '# Disable source packet routing', use_sudo=True)
    append_if_not_present(
        sysctl,
        'net.ipv4.conf.setup_env.accept_source_route = 0', use_sudo=True)
    append_if_not_present(
        sysctl,
        'net.ipv6.conf.setup_env.accept_source_route = 0', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.conf.default.accept_source_route = 0', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv6.conf.default.accept_source_route = 0', use_sudo=True)

    append_if_not_present(
        sysctl, '# Ignore send redirects', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.conf.setup_env.send_redirects = 0', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.conf.default.send_redirects = 0', use_sudo=True)

    append_if_not_present(
        sysctl, '# Block SYN attacks', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.tcp_syncookies = 1', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.tcp_max_syn_backlog = 2048', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.tcp_synack_retries = 2', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.tcp_syn_retries = 5', use_sudo=True)

    append_if_not_present(
        sysctl, '# Log Martians', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.conf.setup_env.log_martians = 1', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.icmp_ignore_bogus_error_responses = 1', use_sudo=True)

    append_if_not_present(
        sysctl, '# Ignore ICMP redirects', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.conf.setup_env.accept_redirects = 0', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv6.conf.setup_env.accept_redirects = 0', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.conf.default.accept_redirects = 0', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv6.conf.default.accept_redirects = 0', use_sudo=True)

    append_if_not_present(
        sysctl, '# Ignore Directed pings', use_sudo=True)
    append_if_not_present(
        sysctl, 'net.ipv4.icmp_echo_ignore_all = 1', use_sudo=True)

    sudo('sysctl -p')


def append_if_not_present(filename, text, use_sudo=False):
    """Append to a file if an equivalent line is not already there."""
    if not contains(filename, text):
        append(filename, text, use_sudo=use_sudo)


@task
def masquerade():
    """Set up masquerading so that a box with two nics can act as a router.
    """
    # Set up masquerade so that one host can act as a NAT gateway for a network
    # of hosts.
    #http://forums.fedoraforum.org/archive/index.php/t-178224.html
    rc_file = '/etc/rc.local'
    masq1 = '/sbin/iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE'
    masq2 = 'echo 1 > /proc/sys/net/ipv4/ip_forward'
    if not contains(rc_file, masq1):
        sed(rc_file, '^exit 0', '#exit 0', use_sudo=True)
        append(rc_file, masq1, use_sudo=True)
        append(rc_file, masq2, use_sudo=True)


@task
def setup_bridge():
    """Setup a network bridge for a machine with two nics."""
    interfaces_file = '/etc/network/interfaces'
    if not contains(interfaces_file, 'eth0 inet static'):
        sed(interfaces_file, 'iface eth0 inet dhcp',
            '#iface eth0 inet dhcp', use_sudo=True)
        append(interfaces_file, 'auto eth0', use_sudo=True)
        append(interfaces_file, 'iface eth0 inet static', use_sudo=True)
        append(interfaces_file, 'address 192.168.2.1', use_sudo=True)
        append(interfaces_file, 'netmask 255.255.255.0', use_sudo=True)
        append(interfaces_file, 'network 192.168.2.0', use_sudo=True)
        append(interfaces_file, 'broadcast 192.168.2.255', use_sudo=True)
        append(interfaces_file, 'gateway 192.168.2.1', use_sudo=True)
        sudo('ifdown eth0')
        sudo('ifup eth0')

    fabtools.require.deb.package('dhcp3-server')
