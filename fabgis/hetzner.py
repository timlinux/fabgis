# coding=utf-8
"""Set up a Hetzner server from scratch."""

from fabric.api import task, run, local


@task
def hetzner_setup(host_name):
    """Provision a hetzner server with software raid.

    :param host_name: The fully qualified domain name to use for the host.
    :type host_name: str

    .. example::

        fab -H mts2 hetzner_setup:host_name=mappingthesacred.org

    If you have an ssh agent running you may be prompted for your password::

        [mts2] Passphrase for private key:

    Enter any text to skip it repeatedly until you get prompted for an
    interactive password.

    Example session output::

        out:                 Hetzner Online AG - installimage
        out:
        out:   Your server will be installed now, this will take some minutes
        out:              You can abort at any time with CTRL+C ...
        out:
        out:          :  Reading configuration               done
        out:    1/14  :  Deleting partitions                 done
        out:    2/14  :  Test partition size                 done
        out:    3/14  :  Creating partitions and /etc/fstab  done
        out:    4/14  :  Creating software RAID level 1      done
        out:    5/14  :  Formatting partitions
        out:          :    formatting /dev/md/0 with ext3    done
        out:          :    formatting /dev/md/1 with ext4    done
        out:    6/14  :  Mounting partitions                 done
        out:    7/14  :  Extracting image (local)            done
        out:    8/14  :  Setting up network for eth0         done
        out:    9/14  :  Executing additional commands
        out:          :    Generating new SSH keys           done
        out:          :    Generating mdadm config           done
        out:          :    Generating ramdisk                done
        out:          :    Generating ntp config             done
        out:          :    Setting hostname                  done
        out:   10/14  :  Setting up miscellaneous files      done
        out:   11/14  :  Setting root password               done
        out:   12/14  :  Installing bootloader grub          done
        out:   13/14  :  Running some ubuntu specific functi done
        out:   14/14  :  Clearing log files                  done
        out:
        out:                   INSTALLATION COMPLETE
        out:    You can now reboot and log in to your new system with
        out:   the same password as you logged in to the rescue system.
        out:
        out:


    """
    options = {
        'install_image_command': '/root/.oldroot/nfs/install/installimage',
        'boot_partition_size': '4G',
        'raid_members': 'sda,sdb',
        'image': 'Ubuntu-1204-precise-64-minimal.tar.gz',
        'host_name': host_name}

    setup_command = (
        '%(install_image_command)s -a -p /boot:ext3:%(boot_partition_size)s,'
        '/:ext4:all -r yes -l 1 -b grub -d %(raid_members)s -i '
        '/root/.oldroot/nfs/install/../images/%(image)s '
        '-n %(host_name)s' % options)

    run(setup_command)
    ip = run('hostname -I')  #
    ip = ip.split(' ')[0]
    run('reboot')
    # Uncache the servers key as it will have changed after re-imaging
    command = 'ssh - keygen - f  "~/.ssh/known_hosts" - R %s' % ip
    local(command)
