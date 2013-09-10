# coding=utf-8
"""Setup file for distutils / pypi."""
from distutils.core import setup

setup(
    name='fabgis',
    version='0.15.2',
    author='Tim Sutton',
    author_email='tim@linfiniti.com',
    packages=['fabgis', ],
    data_files=[],
    scripts=[],
    url='http://pypi.python.org/pypi/fabgis/',
    license='LICENSE.txt',
    description='Fabric tools for a busy FOSSGIS user.',
    long_description=open('README.txt').read(),
    install_requires=[
        "Fabric == 1.6.0",
        "fabtools >= 0.15.0"
    ],
)
