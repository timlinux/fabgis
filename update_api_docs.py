#! /usr/bin/env python
# coding=utf-8
"""Update the api docs by adding all modules in fabgis to api.rst."""

import glob
import os

content = '\nAPI Documentation\n'
content += '=================\n'

files = glob.glob('fabgis/*.py')
for filename in files:
    if '__init__' in filename:
        continue
    filename = filename.replace('fabgis/', '').replace('.py', '')
    content += '\n'
    content += '.. automodule:: fabgis.%s\n' % filename
    content += '   :members:\n\n'

path = os.path.join(os.path.dirname(__file__), 'docs', 'source', 'api.rst')
print path
api = file(path, 'wt')
api.write(content)
api.close()
