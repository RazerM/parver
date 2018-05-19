*****
Usage
*****

.. py:currentmodule:: parver

``parver`` provides the :class:`Version` class. It is immutable, so methods which
you might expect to mutate instead return a new instance with the requested
modifications:

.. testsetup::

    from parver import Version

.. doctest::

    >>> v = Version.parse('1.3')
    >>> v
    <Version '1.3'>
    >>> v.bump_release(index=0)
    <Version '2.0'>
    >>> v.bump_release(index=1)
    <Version '1.4'>
    >>> assert v == Version(release=(1, 3))

Note here that we used an index to tell ``parver`` which number to bump. You may
typically refer to indices 0, 1, and 2 as major, minor, and patch releases, but
this depends on which versioning convention your project uses.

Development, pre-release, and post releases are also supported:

.. doctest::

    >>> Version.parse('1.3').bump_dev()
    <Version '1.3.dev0'>
    >>> Version.parse('1.3').bump_pre('b')
    <Version '1.3b0'>
    >>> Version.parse('1.3').bump_post()
    <Version '1.3.post0'>

Parsing
=======

``parver`` can parse any `PEP 440`_-compatible version string. Here is one in
canonical form:

.. doctest::

    >>> v = Version.parse('1!2.3a4.post5.dev6+local', strict=True)
    >>> v
    <Version '1!2.3a4.post5.dev6+local'>
    >>> assert v.epoch == 1
    >>> assert v.release == (2, 3)
    >>> assert v.pre_tag == 'a'
    >>> assert v.pre == 4
    >>> assert v.post == 5
    >>> assert v.dev == 6
    >>> assert v.local == 'local'

With ``strict=True``, :meth:`~Version.parse` will raise :exc:`ParseError` if
the version is not in canonical form.

Any version in canonical form will have the same normalized string output:

    >>> assert str(v.normalize()) == str(v)

For version numbers that aren't in canonical form, ``parver`` has no problem
parsing them. In this example, there are a couple of non-standard elements:

* Non-standard separators in the pre-release segment.
* `alpha` rather than `a` for the pre-release identifier.
* An implicit post release number.

.. doctest::

    >>> v = Version.parse('1.2.alpha-3.post')
    >>> v
    <Version '1.2.alpha-3.post'>
    >>> assert v.pre == 3
    >>> assert v.pre_tag == 'alpha'
    >>> assert v.is_alpha
    >>> assert v.post == 0
    >>> assert v.post_implicit
    >>> v.normalize()
    <Version '1.2a3.post0'>
    >>> assert v == v.normalize()
    >>> assert str(v) != str(v.normalize())

Note that normalization **does not** affect equality (or ordering).

Also note that ``parver`` can round-trip [#]_ your version strings; non-standard
parameters are kept as-is, even when you mutate:

.. doctest::

    >>> v = Version.parse('v1.2.alpha-3.post')
    >>> v.clear(post=True).bump_pre()
    <Version 'v1.2.alpha-4'>

.. [#] One exception is that ``parver`` always converts the version string to
       lowercase.

.. _`PEP 440`: https://www.python.org/dev/peps/pep-0440/
