# coding: utf-8
from __future__ import absolute_import, division, print_function

from io import open

from setuptools import setup, find_packages

about = dict()

# read _version.py as bytes, otherwise exec will complain about
# 'coding: utf-8', which we want there for the normal Python 2 import
with open('src/parver/_about.py', 'rb') as fp:
    about_mod = fp.read()

exec(about_mod, about)

LONG_DESC = open('README.rst', encoding='utf-8').read()

setup(
    name='parver',
    version=about['__version__'],
    description='Parse and manipulate version numbers.',
    url='https://github.com/RazerM/parver',
    long_description=LONG_DESC,
    long_description_content_type='text/x-rst',
    author='Frazer McLean',
    author_email='frazer@frazermclean.co.uk',
    license='MIT',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'arpeggio',
        'attrs >= 17.4',
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    keywords='pep440 version parse',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
