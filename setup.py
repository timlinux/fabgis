from distutils.core import setup

setup(
    name='fabgis',
    version='0.9.1',
    author='Tim Sutton',
    author_email='tim@linfiniti.com',
    packages=['fabgis', ],
    scripts=[],
    url='http://pypi.python.org/pypi/fabgis/',
    license='LICENSE.txt',
    description='Fabric tools for a busy FOSSGIS user.',
    long_description=open('README.txt').read(),
    install_requires=[
        "Fabric == 1.6.0",
        "fabtools >= 0.13.0"
    ],
)
