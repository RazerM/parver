Changelog
=========

.. towncrier-draft-entries:: |release| (Unreleased Draft)

.. towncrier release notes start

1.0.1 (2026-07-30)
==================

Added
-----

- Support for Python 3.15. (`#96 <https://github.com/RazerM/parver/issues/96>`_)


Fixed
-----

- Removed an outdated documentation note claiming version strings are always converted to lowercase. (`#95 <https://github.com/RazerM/parver/issues/95>`_)
- :exc:`~parver.LeadingZerosError` was not picklable. (`#115 <https://github.com/RazerM/parver/issues/115>`_)
- ``ReleaseInt.__repr__`` dropped leading zeros for numbers with 15 or more digits due to floating-point imprecision. (`#116 <https://github.com/RazerM/parver/issues/116>`_)


1.0 (2026-05-19)
----------------

Added
~~~~~

- New parser which preserves case and leading zeros.

  .. tab:: v1.0

      .. code-block:: python3

          >>> Version.parse("2026.05BETA")
          <Version '2026.05BETA'>

  .. tab:: v0.5

      .. code-block:: python

          >>> Version.parse("2026.05BETA")
          <Version '2026.5beta'>

- Improved error messages.

  .. tab:: v1.0

      .. testsetup::

          from parver import Version

      .. doctest::

          >>> Version.parse("abc")
          Traceback (most recent call last):
          ...
          parver.NoLeadingNumberError: Expected a release number at position 0, found 'a'

          >>> Version.parse("1.2alpha1", strict=True)
          Traceback (most recent call last):
          ...
          parver.StrictPreTagError: Pre-release tag 'alpha' is not allowed in strict mode; use 'a'

          >>> Version.parse("1.2-1", strict=True)
          Traceback (most recent call last):
          ...
          parver.StrictSegmentError: Implicit post-release shorthand '-1' is not allowed
          in strict mode; use '.post1'

          >>> Version.parse("1+ABC", strict=True)
          Traceback (most recent call last):
          ...
          parver.InvalidLocalError: Local version segment 'ABC' is not allowed in strict
          mode: must be lowercase alphanumeric; use 'abc'

  .. tab:: v0.5

      .. code-block:: python

          >>> Version.parse("abc")
          Traceback (most recent call last):
          ...
          parver.ParseError: Expected v or int at position (1, 1) => '*abc'.

          >>> Version.parse("1.2alpha1", strict=True)
          Traceback (most recent call last):
          ...
          parver.ParseError: Expected pre_post_num at position (1, 5) => '1.2a*lpha1'.

          >>> Version.parse("1.2-1", strict=True)
          Traceback (most recent call last):
          ...
          parver.ParseError: Expected dot or 'a' or 'b' or 'rc' or sep or '+' or EOF at
          position (1, 4) => '1.2*-1'.

          >>> Version.parse("1+ABC", strict=True)
          Traceback (most recent call last):
          ...
          parver.ParseError: Expected alpha or int at position (1, 3) => '1+*ABC'.

- The following methods preserve leading zeros, and gain a new ``width`` argument.

  - :meth:`~parver.Version.bump_epoch`
  - :meth:`~parver.Version.bump_release`
  - :meth:`~parver.Version.bump_release_to`
  - :meth:`~parver.Version.set_release`
  - :meth:`~parver.Version.bump_pre`
  - :meth:`~parver.Version.bump_post`
  - :meth:`~parver.Version.bump_dev`

- Support for non-standard development release tags, such as ``DEV``, across:

  - :attr:`~parver.Version.dev_tag`
  - The ``dev_tag`` argument to :class:`~parver.Version`
  - The ``tag`` argument to :meth:`~parver.Version.bump_dev`

- Support for Python 3.13 and 3.14.

Changed
~~~~~~~

- **BREAKING CHANGE**. The :class:`~parver.Version` constructor is now keyword-only.
- **BREAKING CHANGE**. :meth:`Version.parse() <parver.Version.parse>` now requires ``strict`` to be passed
  as a keyword argument.
- **BREAKING CHANGE**. :attr:`Version.v <parver.Version.v>` now stores ``"v"``, ``"V"``, or
  ``None`` instead of ``True`` or ``False``.
- **BREAKING CHANGE**. ``dev_sep`` was renamed to :attr:`~parver.Version.dev_sep1`.

Removed
~~~~~~~

- Support for Python 3.8 and 3.9.

Fixed
~~~~~

- Development releases can now use a separator between ``dev`` and the following
  number as permitted by PEP 440. The separator is exposed as :attr:`~parver.Version.dev_sep2`
  and as a :class:`~parver.Version` keyword argument (`#33 <https://github.com/RazerM/parver/issues/33>`_).

0.5 (2023-10-03)
----------------

Added
~~~~~

- Support for Python 3.12

Removed
~~~~~~~

- Support for Python 3.7


0.4 (2022-11-11)
----------------

Added
~~~~~

- Type hints.

Removed
~~~~~~~

- Support for Python 2.7, 3.5, and 3.6.
- ``__version__``, ``__author__``, and ``__email__`` attributes from `parver`
  module. Use :mod:`importlib.metadata` instead.


0.3.1 (2020-09-28)
------------------

Added
~~~~~

-  Grammar is parsed when first used to improve import time.

Fixed
~~~~~

-  attrs deprecation warning. The minimum attrs version is now 19.2
-  Errors raised for keyword-only argument errors on Python 3 did not
   have the right error message.


0.3 (2020-02-20)
----------------

Added
~~~~~

-  ``Version.truncate`` method to remove trailing zeros from the release
   segment.
-  ``Version`` now validates each item in the release sequence.
-  ``Version.bump_epoch`` method.
-  Add ``by`` keyword argument to ``bump_pre``, ``bump_post``, and
   ``bump_dev`` methods, which e.g. ``.bump_dev(by=-1)``.

Changed
~~~~~~~

-  **BREAKING CHANGE**. The ``Version`` constructor now uses an empty
   string to represent an implicit zero instead of ``None``.

   .. code:: python

      >>> Version(release=1, post='')
      <Version '1.post'>

Removed
~~~~~~~

-  **BREAKING CHANGE**. ``Version.clear`` is no longer necessary. Use
   ``Version.replace(pre=None, post=None, dev=None)`` instead.


Fixed
~~~~~

-  ``Version`` incorrectly allowed an empty release sequence.
-  ``Version`` rejects ``bool`` for numeric components.
-  ``Version`` rejects negative integers for numeric components.
-  The strict parser no longer accepts local versions with ``-`` or
   ``_`` separators, or uppercase letters.
-  The strict parser no longer accepts numbers with leading zeros.
-  The local version was only being converted to lowercase when parsing
   with ``strict=False``. It is now always converted.
-  The local version separators were not being normalized to use ``.``.


0.2.1 (2018-12-31)
------------------

Fixed
~~~~~

-  On Python 2, ``Version`` was incorrectly rejecting ``long`` integer
   values.


0.2 (2018-11-21)
----------------

Added
~~~~~

-  ``Version.bump_release_to`` method for control over the value to bump
   to, e.g. for `CalVer`_.
-  ``Version.set_release`` method for finer control over release values
   without resetting subsequent indices to zero.

.. _CalVer: https://calver.org


Changed
~~~~~~~

-  **BREAKING CHANGE**. The argument to ``Version.bump_release`` is now
   a keyword only argument, e.g. ``Version.bump_release(index=0)``.
-  The ``release`` parameter to ``Version`` now accepts any iterable.


Fixed
~~~~~

-  Deprecation warnings about invalid escape sequences in ``_parse.py``.


0.1.1 (2018-06-19)
------------------

Fixed
~~~~~

-  ``Version`` accepted ``pre=None`` and ``post_tag=None``, which
   produces an ambiguous version number. This is because an implicit
   pre-release number combined with an implicit post-release looks like
   a pre-release with a custom separator:

   .. code:: python

        >>> Version(release=1, pre_tag='a', pre=None, post_tag=None, post=2)
        <Version '1a-2'>
        >>> Version(release=1, pre_tag='a', pre_sep2='-', pre=2)
        <Version '1a-2'>

   The first form now raises a ``ValueError``.

-  Don’t allow ``post=None`` when ``post_tag=None``. Implicit post
   releases cannot have implicit post release numbers.


0.1 (2018-05-20)
----------------

First release.
