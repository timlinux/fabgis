# coding=utf-8
"""
System related tasks.
=====================

Tools for setting up and hardening a system."""

from getpass import getpass

from fabric.api import cd, fastprint, prompt
from fabric.contrib.files import contains, exists, append, sed
from fabric.colors import red
from fabric.api import env, task, sudo, local, reboot
import fabtools
from .utilities import append_if_not_present


@task
def setup_qt4_developer_tools():
    """Install various useful tools needed for developers."""
    fabtools.require.deb.package('qtcreator')
    fabtools.require.deb.package('qt4-designer')
    fabtools.require.deb.package('qt4-linguist-tools')


@task
def setup_ccache():
    """Setup ccache."""
    fabtools.require.deb.package('ccache')
    sudo('ln -fs /usr/bin/ccache /usr/local/bin/gcc')
    sudo('ln -fs /usr/bin/ccache /usr/local/bin/g++')
    sudo('ln -fs /usr/bin/ccache /usr/local/bin/cc')


@task
def install_modxsend():
    """
    Download, compile and activate mod_xsendfile
    """
    fabtools.require.deb.package('apache2-threaded-dev')
    with cd('/tmp'):
        sudo('wget https://tn123.org/mod_xsendfile/mod_xsendfile.c')
        sudo('apxs2 -cia mod_xsendfile.c')
    fabtools.require.service.restarted('apache2')


@task
def install_elasticsearch():
    """
    Download and unpack elasticsearch
    """
    sudo(
        'wget https://download.elasticsearch.org/elasticsearch/'
        'elasticsearch/elasticsearch-0.90.2.deb')
    sudo('sudo dpkg -i elasticsearch-0.90.2.deb')
    fabtools.require.service.restarted('elasticsearch')


@task
def create_user(user, password=None):
    """Create a user on the remote system matching the user running this task.

    :param user: User name for the new user.
    :type user: str

    :param password: Password for new user - will prompt interactively if None.
    :type password: str
    """
    if password is None:
        fastprint(red('Please enter a password for the new web user.\n'))
        password = getpass()
    fabtools.require.users.user(user, password=password)
    fabtools.require.users.sudoer(user)


@task
def ssh_copy_id():
    """Copy ssh id from local system to remote.
    .. note:: Does not work on OSX!
    """
    command = 'ssh-copy-id %s' % env.host
    local(command)


@task
def setup_mosh():
    """ Install mosh as a nice and always working kind of replacement to ssh
    """
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


def get_ip_address():
    """Get the ip address of the remote host.

    :returns: Ip address of the remote host.
    :rtype: str
    """
    host_ip = sudo(
        "ifconfig eth0 | grep 'inet addr:'| "
        "cut -d: -f2 | awk '{print $1}'")
    return host_ip


@task
def harden(ssh_port=22):
    """Harden the server a little.

    :param ssh_port:

    Warning: We make no claim that this makes your server intruder proof. You
    should always check any system yourself and make sure that it is
    adequately secured.

    .. todo:: Make this work more gracefully if harden has been run previously.

    """
    # Create a user name because after we are done remote login as root will
    # be disabled. Username will match your local user.

    user = prompt('Choose a user name')
    password = prompt('Choose a password for the new user')

    create_user(user, password)
    ssh_copy_id()  # this does not work on OSX
    if not contains('/etc/group', 'admin'):
        sudo('groupadd admin')
    sudo('usermod -a -G admin %s' % user)
    sudo('dpkg-statoverride --update --add root admin 4750 /bin/su')

    fabtools.deb.update_index(quiet=True)

    # Set up ufw and mosh
    fabtools.require.deb.package('ufw')
    setup_mosh()

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

    append_if_not_present(
        '/etc/ssh/sshd_config', 'Banner /etc/issue.net', use_sudo=True)

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
    # Must come before mailutils
    fabtools.require.postfix.server(env.host)
    fabtools.require.deb.package('mailutils')
    fabtools.require.deb.package('byobu')
    fabtools.service.restart('ssh')

    # Some hints and tips from:
    # http://www.thefanclub.co
    # .za/how-to/how-secure-ubuntu-1204-lts-server-part-1-basics
    secure_tmp = (
        'tmpfs     /dev/shm     tmpfs     defaults,noexec,'
        'nosuid     0     0')
    append_if_not_present('/etc/fstab', secure_tmp, use_sudo=True)

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
    reboot()

    print 'You need to log in and install mailutils yourself as automated ' \
          'installation causes interactive prompting.'
    print 'sudo apt-get install mailutils'


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


@task
def masquerade():
    """Set up masquerading so that a box with two NICs can act as a router.
    """
    # Set up masquerade so that one host can act as a NAT gateway for a network
    # of hosts.
    #http://forums.fedoraforum.org/archive/index.php/t-178224.html
    rc_file = '/etc/rc.local'
    rule_1 = '/sbin/iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE'
    rule_2 = 'echo 1 > /proc/sys/net/ipv4/ip_forward'
    if not contains(rc_file, rule_1):
        sed(rc_file, '^exit 0', '#exit 0', use_sudo=True)
        append(rc_file, rule_1, use_sudo=True)
        append(rc_file, rule_2, use_sudo=True)
