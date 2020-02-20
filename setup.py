# coding: utf-8
from __future__ import absolute_import, division, print_function

from io import open

from setuptools import find_packages, setup

about = dict()

# read _version.py as bytes, otherwise exec will complain about
# 'coding: utf-8', which we want there for the normal Python 2 import
with open('src/parver/_about.py', 'rb') as fp:
    about_mod = fp.read()

exec(about_mod, about)

LONG_DESC = open('README.rst', encoding='utf-8').read()

extras_require = {
    'test': [
        'pytest',
        'hypothesis',
        'pretend',
    ],
    'docstest': [
        'doc8',
        'sphinx',
        'sphinx_rtd_theme',
    ],
    'pep8test': [
        'flake8',
        'pep8-naming',
    ],
}

setup(
    name='parver',
    version=about['__version__'],
    description=about['__description__'],
    url='https://github.com/RazerM/parver',
    project_urls={
        "Documentation": "https://parver.readthedocs.io",
    },
    long_description=LONG_DESC,
    long_description_content_type='text/x-rst',
    author=about['__author__'],
    author_email=about['__email__'],
    license=about['__license__'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'arpeggio ~= 1.7',
        'attrs >= 17.4.0',
        'six ~= 1.13',
    ],
    extras_require=extras_require,
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
