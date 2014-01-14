# coding=utf-8
"""
General utilities.
==================

"""
import os
from fabric.api import cd, sudo
from fabric.contrib.files import contains, append


def append_if_not_present(filename, text, use_sudo=False):
    """Append to a file if an equivalent line is not already there.
    :param filename: Name of file to append to.
    :type filename: str

    :param text: Text to append.
    :type text: str

    :param use_sudo: Run the command as sudo
    :type use_sudo: bool
    """
    if not contains(filename, text):
        append(filename, text, use_sudo=use_sudo)


def replace_tokens(conf_file, tokens):
    """Deprecated: prepare a template config file by replacing its tokens.

    :param conf_file: Either a full path to a conf file name or just the
        file name. In the latter case, it assumes the file is then in the
        current working directory. It the file name ends in '.templ',
        a copy will be made and the takens replaced in the copy. Otherwise
        the original file will be manipulated.
    :type conf_file: str

    :param tokens: A dictionary of key-values that should be replaced
        in the conf file.
    :type tokens: dic

    :returns: Path to the replaced file.
    :rtype: str

    Example tokens::

        my_tokens = {
            'SERVERNAME': env.doc_site_name,  # Web Url e.g. foo.com
            'WEBMASTER': 'werner@linfiniti.com',  # email of web master
            'DOCUMENTROOT': webdir,  # Content root .e.g. /var/www
            'SITENAME': sitename,  # Choosen name of jenkins 'root'
        }

    .. deprecated:: You should use fabric.contrib.files.upload_template rather.
    """

    if '.templ' == conf_file[-6:]:
        templ_file = conf_file
        conf_file = conf_file.replace('.templ', '')
        sudo(
            'cp %(templ_file)s %(conf_file)s' % {
            'templ_file': templ_file,
            'conf_file': conf_file})

    base_path, file_name = os.path.split(conf_file)
    if base_path is not '':
        # The file is not in the current working dir.
        with cd(base_path):
            for key, value in tokens.iteritems():
                sudo('sed -i.bak -r -e "s/\[%s\]/%s/g" %s' % (
                    key, value, file_name))
            sudo('rm %s.bak' % file_name)
    else:
        # filename only, not full path - assumes the current working dir is
        # the same as where the conf file is located
        for key, value in tokens.iteritems():
            sudo('sed -i.bak -r -e "s/\[%s\]/%s/g" %s' % (
                key, value, file_name))
            sudo('rm %s.bak' % file_name)
    return conf_file
