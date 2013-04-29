import os
from datetime import datetime
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
        env.fg.inasafe_checkout_alias = 'inasafe-fabric'
        env.fg.qgis_checkout_alias = 'qgis-fabric'
        env.fg.inasafe_code_path = os.path.join(
            env.fg.workspace, env.fg.inasafe_checkout_alias)
        env.fg.qgis_code_path = os.path.join(
            env.fg.workspace, env.fg.qgis_checkout_alias)


@task
def show_environment():
    """For diagnostics - show any pertinent info about server."""
    all()
    fastprint('\n-------------------------------------------------\n')
    for key, value in env.fg.iteritems():
        fastprint('Key: %s \t\t Value: %s' % (key, value))
    fastprint('-------------------------------------------------\n')


def add_ubuntugis_ppa():
    """Ensure we have ubuntu-gis repos."""
    fabtools.deb.update_index(quiet=True)
    fabtools.require.deb.ppa(
        'ppa:ubuntugis/ubuntugis-unstable', auto_yes=True)


def clone_qgis(branch='master'):
    """Clone or update QGIS from git.

    :param branch: the name of the branch to build from. Defaults to 'master'
    :type branch: basestring

    :rtype: None
    """
    all()
    fabtools.require.deb.package('git')
    code_base = '%s/dev/cpp' % env.fg.workspace
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
def install_qgis1_8():
    """Install QGIS 1.8 under /usr/local/qgis-1.8."""
    setup_env()
    add_ubuntugis_ppa()
    sudo('apt-get build-dep -y qgis')
    fabtools.require.deb.package('cmake-curses-gui')
    fabtools.require.deb.package('git')
    clone_qgis(branch='release-1_8')
    workspace = '%s/dev/cpp' % env.fg.workspace
    code_path = '%s/Quantum-GIS' % workspace
    build_path = '%s/build-qgis18' % code_path
    build_prefix = '/usr/local/qgis-1.8'
    fabtools.require.directory(build_path)
    with cd(build_path):
        fabtools.require.directory(
            build_prefix,
            use_sudo=True,
            owner=env.fg.user)
        run('cmake .. -DCMAKE_INSTALL_PREFIX=%s' % build_prefix)
        run('make install')


@task
def install_qgis2():
    """Install QGIS 2 under /usr/local/qgis-master.

    TODO: create one function from this and the 1.8 function above for DRY.

    """
    setup_env()
    add_ubuntugis_ppa()
    sudo('apt-get build-dep -y qgis')
    fabtools.require.deb.package('cmake-curses-gui')
    fabtools.require.deb.package('git')
    clone_qgis(branch='master')
    workspace = '%s/dev/cpp' % env.fg.workspace
    code_path = '%s/Quantum-GIS' % workspace
    build_path = '%s/build-master' % code_path
    build_prefix = '/usr/local/qgis-master'
    fabtools.require.directory(build_path)
    with cd(build_path):
        fabtools.require.directory(
            build_prefix,
            use_sudo=True,
            owner=env.fg.user)
        run('cmake .. -DCMAKE_INSTALL_PREFIX=%s' % build_prefix)

        run('make install')


def setup_postgres_user(user):
    #sudo('apt-get upgrade')
    # wsgi user needs pg access to the db
    if not fabtools.postgres.user_exists(user):
        fabtools.postgres.create_user(
            user,
            password='',
            createdb=False,
            createrole=False,
            connection_limit=20)


def setup_postgres_superuser(user):
    if not fabtools.postgres.user_exists(env.user):
        fabtools.postgres.create_user(
            user,
            password='',
            createdb=True,
            createrole=True,
            superuser=True,
            connection_limit=20)


@task
def setup_postgis():
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
    setup_postgis()
    setup_postgres_user(user)
    setup_postgres_superuser(env.user)
    create_user()
    fabtools.require.postgres.database(
        '%s' % dbname, owner='%s' % user, template='template_postgis')

    grant_sql = 'grant all on schema public to %s;' % user
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
def restore_postgres_dump(dbname):
    """Upload dump to host, remove existing db, recreate then restore dump."""
    setup_env()
    show_environment()
    setup_postgres_user()
    create_user()
    date = run('date +%d-%B-%Y')
    my_file = '%s-%s.dmp' % (env.repo_alias, date)
    put('resources/sql/dumps/%s' % my_file, '/tmp/%s' % my_file)
    if fabtools.postgres.database_exists(env.repo_alias):
        run('dropdb %s' % env.repo_alias)
    fabtools.require.postgres.database(
        '%s' % dbname,
        owner='%s' % env.user,
        template='template_postgis',
        encoding='UTF8')
    run('pg_restore /tmp/%s | psql %s' % (my_file, env.repo_alias))


@task
def create_user():
    """Create a user on the remote system matching the user running this task.
    """
    fabtools.require.users.user(env.user)
    fabtools.require.users.sudoer(env.user)


@task
def ssh_copy_id():
    """Copy ssh id from local system to remote."""
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
