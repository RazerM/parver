.. image:: https://img.shields.io/badge/docs-read%20now-blue.svg
   :target: https://parver.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://travis-ci.org/RazerM/parver.svg?branch=master
   :target: https://travis-ci.org/RazerM/parver
   :alt: Automated test status

.. image:: https://codecov.io/gh/RazerM/parver/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/RazerM/parver
   :alt: Test coverage

.. image:: https://img.shields.io/github/license/RazerM/parver.svg
   :target: https://raw.githubusercontent.com/RazerM/parver/master/LICENSE.txt
   :alt: MIT License

parver
======

parver allows parsing and manipulation of `PEP 440`_ version numbers.

Example
=======

.. code:: python

    >>> Version.parse('1.3').bump_dev()
    <Version '1.3.dev0'>
    >>> v = Version.parse('v1.2.alpha-3')
    >>> v.is_alpha
    True
    >>> v.pre
    3
    >>> v
    <Version 'v1.2.alpha-3'>
    >>> v.normalize()
    <Version '1.2a3'>

.. _`PEP 440`: https://www.python.org/dev/peps/pep-0440/
