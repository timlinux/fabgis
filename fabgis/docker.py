# coding=utf-8
"""
Docker Related Tasks.
=====================

Tools for configuration and set up of docker.

.. seealso:: http://www.docker.io/
     and http://docs.docker.io/en/latest/installation/
     ubuntulinux/#ubuntu-precise-12-04-lts-64-bit

As the second article mentions, for ubuntu 12.04 the kernel needs to be
upgraded to 3.8 - which the setup task will do.


Example usage:

In your fabfile.py you might do the initial setup of docker (assuming it isn't
already installed on your system), create a base image with a root password
of your choosing and then bring up a container like this::

    setup_docker()

Once it is set up, you might create a new container for your project::

    setup_docker_image()  # called by setup docker case of first install
    create_docker_container()
    id = current_docker_container()
    ssh_port = get_docker_port_mappings(id)[22]

A control file called `fabgis.container.id` will be written to the current
working directory - it will contain the id of the created container.

After this you can treat the docker container as any other host and run
fabric tasks against it e.g.::

    fab -H root@localhost:<ssh_port> <command>

"""

from fabric.api import run, sudo, task, fastprint, env, prompt, reboot, abort
from fabric.colors import red, green, blue, yellow
from fabric.contrib.files import exists, contains, sed
from fabtools.deb import update_index as apt_get_update, is_installed
from fabtools.require.deb import ppa as require_ppa
from fabtools.require.deb import package as require_package
from fabtools.require.deb import packages as require_packages


@task
def docker():
    """Convenience function that operates in a similar way to fabtools vagrant.

    Example usage - first add this to your fabfile.py

        from fabgis.docker import docker

    Then use docker instead of a -H hostname directive e.g.::

        fab docker setup_qgis2

    This command makes no attempt to create the docker container, so will fail
    if there is not a fabgis.container.id file in the current working
    directory that contains the id of a valid container.


    .. todo:: Behaviour when more than one host is passed to fabric is still
        not defined or tested.
    """
    host_name = run('hostname')
    fastprint(green(
        'Connected on %s preparing ssh tunnel though this gateway\n' %
        host_name))
    container_id_file = 'fabgis.container.id'
    if exists(container_id_file):
        container_id = run('cat %s' % container_id_file)
    else:
        abort(red('Docker fabgis.container.id file not found.\n'))

    mappings = get_docker_port_mappings(container_id)

    ssh_port = mappings[22]
    env.port = ssh_port
    env.user = 'root'
    fastprint(env)
    host_name = run('hostname')
    fastprint(green(
        'Connected on %s via ssh tunnel though this gateway\n' % host_name))


@task
def setup_docker(force=False):
    """Setup docker on the target host.

    :param force: Whether to continue with installation even if
        docker already appears to be installed. Defaults to False.
    :type force: bool
    """
    fastprint(yellow('Setting up docker on host: %s\n' % env.host))
    if is_installed('lxc-docker'):
        fastprint(green(
            'This system already appears to have docker installed on it\n'))
    else:
        version = run('uname -r')
        if '3.2' in version:
            # LTS 3.2 version is too old so we install a backported one
            # see http://docs.docker.io/en/latest/installation/ubuntulinux/
            # #ubuntu-precise-12-04-lts-64-bit
            fastprint(red('Upgrading kernel to 3.8!\n'))
            response = prompt('Do you wish to continue? y/n :')
            if response != 'y':
                fastprint(red('Docker install aborted by user.\n'))
                return
            fastprint(blue('Ok upgrading kernel.'))
            require_packages([
                'linux-image-generic-lts-raring',
                'linux-headers-generic-lts-raring'])
            fastprint(red('\nWe need to reboot the system now!\n'))
            response = prompt('Do you wish to continue? y/n :')
            if response is not None:
                reboot()
        else:
            require_package('linux-image-extra-%s' % version)
        require_ppa('ppa:dotcloud/lxc-docker')
        apt_get_update()
        require_packages([
            'software-properties-common',
            'lxc-docker'])
    # Ensure ufw forwards traffic.
    # http://docs.docker.io/en/latest/installation/ubuntulinux/#ufw
    sed(
        '/etc/default/ufw',
        'DEFAULT_FORWARD_POLICY="DROP"',
        'DEFAULT_FORWARD_POLICY="ACCEPT"',
        use_sudo=False)
    setup_docker_image()
    setup_docker_user()


@task
def setup_docker_group():
    """Setup the docker group so that any docker group members dont need sudo.

    Once a user is in the docker group they can issue docker commands without
    being a sudo user.
    """
    if not contains('/etc/group', 'docker'):
        sudo('groupadd docker')
        sudo('service docker restart')


@task
def setup_docker_user(user=None):
    """Setup a user with rights to run docker after their next relogin.

    :param user: The user that should be granted docker rights. If none,
        env.user will be assumed.
    :type user: str
    """
    setup_docker_group()
    if user is None:
        user = env.user
    sudo('usermod -a -G docker %s' % user)
    fastprint(red(
        'User %s will be able to run docker without sudo on their '
        'next log in.' % user))


@task
def setup_docker_image():
    """Set up the default docker image to be used in fabgis deployments.

    We base our container on dhrp/sshd image.

    After running this task you will have an image called fabgis/sshd with
    a root password of your choosing.

    On first installation we need to set the root password that will be
    used as default for this base image.
    """

    fastprint(blue(
        'Downloading the dhrp/sshd base image - may take a while.\n'))

    container_id = create_docker_container('dhrp/sshd')

    fastprint(blue(
        'setting the password in the container\n'))
    fastprint(green(
        'Enter the password "screencast" for the first root prompt below.\n'))
    fastprint(green(
        'Enter a password of YOUR OWN CHOOSING at the second prompt below.\n'))
    fastprint(green(
        'Then re-enter your own password at the confirmation prompt.\n'))
    fastprint(red(
        'Note that the password will be echoed to the console in the clear'
        '.\n'))

    mappings = get_docker_port_mappings(container_id)
    run('ssh root@localhost -p %i passwd' % mappings[22])

    fastprint(green(
        'Committing the change to a new default container fabgis/sshd\n'))

    sudo('sudo docker commit %s fabgis/sshd' % container_id)

    fastprint(red(
        'Deleting the temporary container we started during setup.\n'))

    sudo('docker kill %s' % container_id)

    fastprint(green('Installation of docker completed ok!\n'))


@task
def get_docker_port_mappings(container_id):
    """Given the id of a container, get the ports mapped for that container.

    This is basically a wrapper for docker ps that parses the output and
    returns the ports that are mapped as a dict where the keys are the
    container internal ports and the values are the container external ports.

    :param container_id: ID for the container to obtain port mappings for.
    :type container_id: str

    e.g. for this container::

        d3caf337bfc1     dhrp/sshd:latest    /usr/sbin/sshd -D   8 minutes \
        ago       Up 8 minutes        49171->22, 49172->8000

    The following dictionary would be returned::

        {
            22: 49171,
            8000, 49172
        }
    """
    ports = sudo(
        'docker ps | grep %s | awk '
        '\'{ s = ""; for (i = 11; i <= NF; i++) s = s $i " "; print s }\''
        % container_id)

    #fastprint('Ports: %s\n' % str(ports))

    if ', ' in ports:
        tokens = ports.split(', ')
    else:
        tokens = [ports]

    mappings = {}

    #fastprint('Tokens: %s\n' % str(tokens))
    for token in tokens:
        parts = token.split('->')
        #fastprint('Parts: %s\n' % str(parts))
        host_port = int(parts[0])
        container_port = int(parts[1])
        mappings[container_port] = host_port

    fastprint('Mappings: %s\n' % str(mappings))
    return mappings


@task
def create_docker_container(image='fabgis/sshd'):
    """Create a docker container using the provided base image.

    :param image: The image name to be used as a basis for this container.
    :type image: str

    :returns: The id of the created container.
    :rtype: str
    """
    # Id of container will be written to fabgis.container.id

    container_id_file = 'fabgis.container.id'
    if exists(container_id_file):
        sudo('rm %s' % container_id_file)

    sudo(
        'docker run -cidfile=%s -d -p 22 -p 80 %s /usr/sbin/sshd -D' %
        (container_id_file, image))

    # now get the id back - this is more reliable than reading from stdout
    container_id = run('cat %s' % container_id_file)

    return container_id


@task
def current_docker_container():
    """Return the current docker container id as stored in fabgis.container.id.

    :returns: The value in fabgis.container.id. If the container does not exist
        None is returned.
    :rtype: str, None
    """
    container_id_file = 'fabgis.container.id'
    if exists(container_id_file):
        return run('cat %s' % container_id_file)
    else:
        return None


@task
def allow_docker_through_ufw():
    """Allow docker networking to communicate out through UFW.


         TODO Implement this task fully


        http://stackoverflow.com/questions/17394241/my-firewall-is-blocking
        -network-connections-from-the-docker-container-to-outside
    """
    before_rules = """
    # docker rules to enable external network access from the container
    # forward traffic accross the bridge
    -A ufw - before - forward - i  docker0 - j  ACCEPT
    -A ufw - before - forward - i  testbr0 - j  ACCEPT
    -A ufw - before - forward - m  state - -state
    RELATED, ESTABLISHED - j ACCEPT"""

    after_rules = """
    *nat
    :POSTROUTING ACCEPT [0:0]
    -A POSTROUTING -s 172.16.42.0/8 -o eth0 -j MASQUERADE
    # don't delete the 'COMMIT' line or these rules won't be processed
    COMMIT
    """
