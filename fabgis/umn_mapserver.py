# coding=utf-8
"""
Mapserver related tasks.
========================

"""

import os
from fabric.api import task, fastprint
from fabric.colors import cyan
from fabric.contrib.files import contains, append
from fabtools import fabtools


@task
def setup_mapserver():
    """Install UMN Mapserver from apt and add 900913 CRS to proj epsg file."""
    fastprint(cyan('Setting up UMN Mapserver\n'))
    # Clone and replace tokens in mapserver map file
    # Clone and replace tokens in mapserver conf
    fabtools.require.deb.package('cgi-mapserver')
    # We also need to append 900913 epsg code to the proj epsg list
    epsg_path = '/usr/share/proj/epsg'
    epsg_code = (
        '<900913> +proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_'
        '0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs')
    epsg_id = '900913'
    if not contains(epsg_path, epsg_id):
        append(epsg_path, epsg_code, use_sudo=True)
