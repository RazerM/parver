# coding: utf-8
from __future__ import absolute_import, division, print_function

import itertools
import operator
import re
from collections import Sequence
from functools import partial

import attr
import six
from attr.validators import in_, instance_of, optional

from ._helpers import UNSET, Infinity
from ._parse import parse
from . import _segments as segment


def force_tuple(n):
    if isinstance(n, six.string_types):
        raise TypeError('Expected tuple or int.')
    if not isinstance(n, Sequence):
        return n,
    if not isinstance(n, tuple):
        return tuple(n)
    return n


POST_TAGS = {'post', 'rev', 'r'}
SEPS = {'.', '-', '_'}
PRE_TAGS = {'c', 'rc', 'alpha', 'a', 'beta', 'b', 'preview', 'pre'}


def unset_or(validator):
    def validate(inst, attr, value):
        if value is UNSET:
            return

        validator(inst, attr, value)
    return validate


validate_post_tag = unset_or(optional(in_(POST_TAGS)))
validate_pre_tag = optional(in_(PRE_TAGS))
validate_sep = optional(in_(SEPS))
validate_sep_or_unset = unset_or(optional(in_(SEPS)))
is_bool = instance_of(bool)
is_int = instance_of(int)
is_str = instance_of(six.string_types)
is_seq = instance_of(Sequence)


@attr.s(frozen=True, repr=False, cmp=False)
class Version(object):
    """

    :param release: Numbers for the release segment.
    :type release: int or tuple[int]

    :param v: Optional preceding v character.
    :type v: bool

    :param epoch: `Version epoch`_. Implicitly zero but hidden by default.
    :type epoch: int

    :param pre_tag: `Pre-release`_ identifier, typically `a`, `b`, or `rc`.
        Required to signify a pre-release.
    :type pre_tag: str

    :param pre: `Pre-release`_ number. May be `None` to signify an
        `implicit pre-release number`_.
    :type pre: int

    :param post: `Post-release`_ number. May be `None` to signify an
        `implicit post release number`_.
    :type post: int

    :param dev: `Developmental release`_ number. May be `None` to signify an
        `implicit development release number`_.
    :type dev: int

    :param local: `Local version`_ segment.
    :type local:

    :param pre_sep1: Specify an alternate separator before the pre-release
        segment. The normal form is `None`.
    :type pre_sep1: str

    :param pre_sep2: Specify an alternate separator between the identifier and
        number. The normal form is ``'.'``.
    :type pre_sep2: str

    :param post_sep1: Specify an alternate separator before the post release
        segment. The normal form is ``'.'``.
    :type post_sep1: str

    :param post_sep2: Specify an alternate separator between the identifier and
        number. The normal form is ``'.'``.
    :type post_sep2: str

    :param dev_sep: Specify an alternate separator before the development
        release segment. The normal form is ``'.'``.
    :type dev_sep: str

    :param post_tag: Specify alternate post release identifier `rev` or `r`.
        May be `None` to signify an `implicit post release`_.
    :type post_tag: str

    .. note:: The attributes below are not equal to the parameters passed to
        the initialiser!

        The main difference is that implicit numbers become `0` and set the
        corresponding `_implicit` attribute:

        .. doctest::

            >>> v = Version(release=1, post=None)
            >>> str(v)
            '1.post'
            >>> v.post
            0
            >>> v.post_implicit
            True

    .. attribute:: release

        A tuple of integers giving the components of the release segment of
        this :class:`Version` instance; that is, the ``1.2.3`` part of the
        version number, including trailing zeroes but not including the epoch
        or any prerelease/development/postrelease suffixes

    .. attribute:: v

        Whether this :class:`Version` instance includes a preceding v character.

    .. attribute:: epoch

        An integer giving the version epoch of this :class:`Version` instance.
        :attr:`epoch_implicit` may be `True` if this number is zero.

    .. attribute:: pre_tag

        If this :class:`Version` instance represents a pre-release, this
        attribute will be the pre-release identifier. One of `a`, `b`, `rc`,
        `c`, `alpha`, `beta`, `preview`, or `pre`.

        **Note:** you should not use this attribute to check or compare
        pre-release identifiers. Use :meth:`is_alpha`, :meth:`is_beta`, and
        :meth:`is_release_candidate` instead.

    .. attribute:: pre

        If this :class:`Version` instance represents a pre-release, this
        attribute will be the pre-release number. If this instance is not a
        pre-release, the attribute will be `None`. :attr:`pre_implicit` may be
        `True` if this number is zero.

    .. attribute:: post

        If this :class:`Version` instance represents a postrelease, this
        attribute will be the postrelease number (an integer); otherwise, it
        will be `None`. :attr:`post_implicit` may be `True` if this number
        is zero.

    .. attribute:: dev

        If this :class:`Version` instance represents a development release,
        this attribute will be the development release number (an integer);
        otherwise, it will be `None`. :attr:`dev_implicit` may be `True` if this
        number is zero.

    .. attribute:: local

        A string representing the local version portion of this :class:`Version`
        instance if it has one, or ``None`` otherwise.

    .. attribute:: pre_sep1

        The separator before the pre-release identifier.

    .. attribute:: pre_sep2

        The seperator between the pre-release identifier and number.

    .. attribute:: post_sep1

        The separator before the post release identifier.

    .. attribute:: post_sep2

        The seperator between the post release identifier and number.

    .. attribute:: dev_sep

        The separator before the develepment release identifier.

    .. attribute:: post_tag

        If this :class:`Version` instance represents a post release, this
        attribute will be the post release identifier. One of `post`, `rev`,
        `r`, or `None` to represent an implicit post release.

    .. _`Version epoch`: https://www.python.org/dev/peps/pep-0440/#version-epochs
    .. _`Pre-release`: https://www.python.org/dev/peps/pep-0440/#pre-releases
    .. _`implicit pre-release number`: https://www.python.org/dev/peps/
        pep-0440/#implicit-pre-release-number
    .. _`Post-release`: https://www.python.org/dev/peps/pep-0440/#post-releases
    .. _`implicit post release number`: https://www.python.org/dev/peps/
        pep-0440/#implicit-post-release-number
    .. _`Developmental release`: https://www.python.org/dev/peps/pep-0440/
        #developmental-releases
    .. _`implicit development release number`: https://www.python.org/dev/peps/
        pep-0440/#implicit-development-release-number
    .. _`Local version`: https://www.python.org/dev/peps/pep-0440/
        #local-version-identifiers
    .. _`implicit post release`: https://www.python.org/dev/peps/pep-0440/
        #implicit-post-releases

    """
    release = attr.ib(converter=force_tuple, validator=is_seq)
    v = attr.ib(default=False, validator=is_bool)
    epoch = attr.ib(default=None, validator=optional(is_int))
    pre_tag = attr.ib(default=None, validator=validate_pre_tag)
    pre = attr.ib(default=None, validator=optional(is_int))
    post = attr.ib(default=UNSET, validator=unset_or(optional(is_int)))
    dev = attr.ib(default=UNSET, validator=unset_or(optional(is_int)))
    local = attr.ib(default=None, validator=optional(is_str))

    pre_sep1 = attr.ib(default=None, validator=validate_sep)
    pre_sep2 = attr.ib(default=None, validator=validate_sep)
    post_sep1 = attr.ib(default=UNSET, validator=validate_sep_or_unset)
    post_sep2 = attr.ib(default=UNSET, validator=validate_sep_or_unset)
    dev_sep = attr.ib(default=UNSET, validator=validate_sep_or_unset)
    post_tag = attr.ib(default=UNSET, validator=validate_post_tag)

    epoch_implicit = attr.ib(default=False, init=False)
    pre_implicit = attr.ib(default=False, init=False)
    post_implicit = attr.ib(default=False, init=False)
    dev_implicit = attr.ib(default=False, init=False)
    _key = attr.ib(init=False)

    def __attrs_post_init__(self):
        set = partial(object.__setattr__, self)

        if self.epoch is None:
            set('epoch', 0)
            set('epoch_implicit', True)

        if self.pre_tag is not None and self.pre is None:
            set('pre', 0)
            set('pre_implicit', True)

        if self.pre is not None and self.pre_tag is None:
            raise ValueError('Must set pre_tag if pre is given.')

        if (self.pre_tag is None and
                (self.pre_sep1 is not None or self.pre_sep2 is not None)):
            raise ValueError('Cannot set pre_sep1 or pre_sep2 without pre_tag.')

        if self.post_tag is None:
            if self.post is UNSET:
                raise ValueError(
                    "Implicit post releases (post_tag=None) require a numerical "
                    "value for 'post' argument.")

            if self.post_sep1 is not UNSET or self.post_sep2 is not UNSET:
                raise ValueError(
                    'post_sep1 and post_sep2 cannot be set for implicit post '
                    'releases (post_tag=None)')

            set('post_sep1', '-')

        if self.post is not UNSET:
            if self.post_tag is UNSET:
                set('post_tag', 'post')
            if self.post is None:
                set('post_implicit', True)
                set('post', 0)

        if self.post_tag is not UNSET and self.post is UNSET:
            set('post_implicit', True)
            set('post', 0)

        if self.dev is None:
            set('dev_implicit', True)
            set('dev', 0)

        if self.post is UNSET:
            set('post', None)

        if self.post_tag is UNSET:
            set('post_tag', None)

        if self.post_sep1 is UNSET:
            set('post_sep1', None if self.post is None else '.')
        if self.post_sep2 is UNSET:
            set('post_sep2', None)

        if self.dev is UNSET:
            set('dev', None)

        if self.dev_sep is UNSET:
            set('dev_sep', None if self.dev is None else '.')

        assert self.post_sep1 is not UNSET
        assert self.post_sep2 is not UNSET

        set('_key', _cmpkey(
            self.epoch,
            self.release,
            _normalize_pre_tag(self.pre_tag),
            self.pre,
            self.post,
            self.dev,
            self.local,
        ))

    @classmethod
    def parse(cls, version, strict=False):
        """
        :param version: Version number as defined in `PEP 440`_.
        :type version: str

        :param strict: Enable strict parsing of the canonical PEP 440 format.
        :type strict: bool

        .. _`PEP 440`: https://www.python.org/dev/peps/pep-0440/

        :raises ParseError: If version is not valid for the given value of
            `strict`.

        .. doctest::
            :options: -IGNORE_EXCEPTION_DETAIL

            >>> Version.parse('1.dev')
            <Version '1.dev'>
            >>> Version.parse('1.dev', strict=True)
            Traceback (most recent call last):
              ...
            parver._parse.ParseError: Expected int at position (1, 6) => '1.dev*'.
        """
        segments = parse(version, strict=strict)

        kwargs = dict()

        for s in segments:
            if isinstance(s, segment.Epoch):
                kwargs['epoch'] = s.value
            elif isinstance(s, segment.Release):
                kwargs['release'] = s.value
            elif isinstance(s, segment.Pre):
                kwargs['pre'] = s.value
                kwargs['pre_tag'] = s.tag
                kwargs['pre_sep1'] = s.sep1
                kwargs['pre_sep2'] = s.sep2
            elif isinstance(s, segment.Post):
                kwargs['post'] = s.value
                kwargs['post_tag'] = s.tag
                kwargs['post_sep1'] = s.sep1
                kwargs['post_sep2'] = s.sep2
            elif isinstance(s, segment.Dev):
                kwargs['dev'] = s.value
                kwargs['dev_sep'] = s.sep
            elif isinstance(s, segment.Local):
                kwargs['local'] = s.value
            elif isinstance(s, segment.V):
                kwargs['v'] = True
            else:
                raise TypeError('Unexpected segment: {}'.format(segment))

        return cls(**kwargs)

    def normalize(self):
        return Version(
            release=self.release,
            epoch=None if self.epoch == 0 else self.epoch,
            pre_tag=_normalize_pre_tag(self.pre_tag),
            pre=self.pre,
            post=UNSET if self.post is None else self.post,
            dev=UNSET if self.dev is None else self.dev,
            local=self.local
        )

    def __str__(self):
        parts = []

        if self.v:
            parts.append('v')

        if not self.epoch_implicit:
            parts.append('{}!'.format(self.epoch))

        parts.append('.'.join(str(x) for x in self.release))

        if self.pre_tag is not None:
            if self.pre_sep1:
                parts.append(self.pre_sep1)
            parts.append(self.pre_tag)
            if self.pre_sep2:
                parts.append(self.pre_sep2)
            if not self.pre_implicit:
                parts.append(str(self.pre))

        if self.post_tag is None and self.post is not None:
            parts.append('-{}'.format(self.post))
        elif self.post_tag is not None:
            if self.post_sep1:
                parts.append(self.post_sep1)
            parts.append(self.post_tag)
            if self.post_sep2:
                parts.append(self.post_sep2)
            if not self.post_implicit:
                parts.append(str(self.post))

        if self.dev is not None:
            if self.dev_sep is not None:
                parts.append(self.dev_sep)
            parts.append('dev')
            if not self.dev_implicit:
                parts.append(str(self.dev))

        if self.local is not None:
            parts.append('+{}'.format(self.local))

        return ''.join(parts)

    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, str(self))

    def __hash__(self):
        return hash(self._key)

    def __lt__(self, other):
        return self._compare(other, operator.lt)

    def __le__(self, other):
        return self._compare(other, operator.le)

    def __eq__(self, other):
        return self._compare(other, operator.eq)

    def __ge__(self, other):
        return self._compare(other, operator.ge)

    def __gt__(self, other):
        return self._compare(other, operator.gt)

    def __ne__(self, other):
        return self._compare(other, operator.ne)

    def _compare(self, other, method):
        if not isinstance(other, Version):
            return NotImplemented

        return method(self._key, other._key)

    @property
    def public(self):
        """A string representing the public version portion of this
        :class:`Version` instance.
        """
        return str(self).split('+', 1)[0]

    def base_version(self):
        """Return a new :class:`Version` instance for the base version of the
        current instance. The base version is the public version of the project
        without any pre or post release markers.

        See also: :meth:`clear` and :meth:`replace`.
        """
        return self.clear(pre=True, post=True, dev=True).replace(local=None)

    @property
    def is_prerelease(self):
        """A boolean value indicating whether this :class:`Version` instance
        represents a pre-release and/or development release.
        """
        return self.dev is not None or self.pre is not None

    @property
    def is_alpha(self):
        """A boolean value indicating whether this :class:`Version` instance
        represents an alpha pre-release.
        """
        return _normalize_pre_tag(self.pre_tag) == 'a'

    @property
    def is_beta(self):
        """A boolean value indicating whether this :class:`Version` instance
        represents a beta pre-release.
        """
        return _normalize_pre_tag(self.pre_tag) == 'b'

    @property
    def is_release_candidate(self):
        """A boolean value indicating whether this :class:`Version` instance
        represents a release candidate pre-release.
        """
        return _normalize_pre_tag(self.pre_tag) == 'rc'

    @property
    def is_postrelease(self):
        """A boolean value indicating whether this :class:`Version` instance
        represents a post-release.
        """
        return self.post is not None

    @property
    def is_devrelease(self):
        """A boolean value indicating whether this :class:`Version` instance
        represents a development release.
        """
        return self.dev is not None

    def _attrs_as_init(self):
        d = attr.asdict(self, filter=lambda attr, _: attr.init)

        if self.epoch_implicit:
            d['epoch'] = None

        if self.pre_implicit:
            d['pre'] = None

        if self.post_implicit:
            d['post'] = None

        if self.dev_implicit:
            d['dev'] = None

        if self.pre is None:
            del d['pre']
            del d['pre_tag']
            del d['pre_sep1']
            del d['pre_sep2']

        if self.post is None:
            del d['post']
            del d['post_tag']
            del d['post_sep1']
            del d['post_sep2']
        elif self.post_tag is None:
            del d['post_sep1']
            del d['post_sep2']

        if self.dev is None:
            del d['dev']
            del d['dev_sep']

        return d

    def clear(self, pre=False, post=False, dev=False):
        """Like :meth:`replace`, but has the ability to **remove** pre-release,
        post release, and development release segments.

        See also: :meth:`base_version`.
        """
        d = self._attrs_as_init()

        if pre:
            d.pop('pre', None)
            d.pop('pre_tag', None)
            d.pop('pre_sep1', None)
            d.pop('pre_sep2', None)

        if post:
            d.pop('post', None)
            d.pop('post_tag', None)
            d.pop('post_sep1', None)
            d.pop('post_sep2', None)

        if dev:
            d.pop('dev', None)
            d.pop('dev_sep', None)

        return Version(**d)

    def replace(self, **kwargs):
        """Return a new :class:`Version` instance with the same attributes,
        except for those given as keyword arguments. Arguments have the same
        meaning as they do when constructing a new :class:`Version` instance
        manually.

        .. warning::

            Be careful! :class:`Version` treats `None` as an implicit zero, so
            pre-release, post release and development releases cannot be
            cleared using this method:

            .. doctest::

                >>> Version.parse('1.3.post0').replace(post=None)
                <Version '1.3.post'>
                >>> Version.parse('1.3').replace(post=None)
                <Version '1.3.post'>

            Use :meth:`clear` instead:

            .. doctest::

                >>> Version.parse('1.3.post0').clear(post=True)
                <Version '1.3'>

        """
        d = self._attrs_as_init()

        if kwargs.get('post_tag', UNSET) is None:
            # ensure we don't carry over separators for new implicit post
            # release. By popping from d, there will still be an error if the
            # user tries to set them in kwargs
            d.pop('post_sep1', None)
            d.pop('post_sep2', None)

        d.update(kwargs)
        return Version(**d)

    def bump_release(self, index):
        """Return a new :class:`Version` instance with the release number
        bumped at the given `index`.

        :param index: Index of the release number tuple to bump. It is not
            limited to the current size of the tuple. Intermediate indices will
            be set to zero.
        :type index: int

        :raises TypeError: `index` is not an integer.
        :raises ValueError: `index` is negative.

        .. doctest::

            >>> v = Version.parse('1.4')
            >>> v.bump_release(0)
            <Version '2.0'>
            >>> v.bump_release(1)
            <Version '1.5'>
            >>> v.bump_release(2)
            <Version '1.4.1'>
            >>> v.bump_release(3)
            <Version '1.4.0.1'>
        """
        if not isinstance(index, int):
            raise TypeError('index must be an integer')

        if index < 0:
            raise ValueError('index cannot be negative')

        release = list(self.release)
        new_len = index + 1

        if len(release) < new_len:
            release.extend(itertools.repeat(0, new_len - len(release)))

        for i, value in enumerate(release):
            if i == index:
                release[i] += 1
            elif i > index:
                release[i] = 0

        return self.replace(release=release)

    def bump_pre(self, tag=None):
        """Return a new :class:`Version` instance with the pre-release number
        bumped.

        :param tag: Pre-release tag. Required if not already set.
        :type tag: str

        :raises ValueError: Trying to call ``bump_pre(tag=None)`` on a
            :class:`Version` instance that is not already a pre-release.
        :raises ValueError: Calling the method with a `tag` not equal to the
            current :attr:`post_tag`. See :meth:`replace` instead.

        .. doctest::

            >>> Version.parse('1.4').bump_pre('a')
            <Version '1.4a0'>
            >>> Version.parse('1.4b1').bump_pre()
            <Version '1.4b2'>
        """
        pre = 0 if self.pre is None else self.pre + 1

        if self.pre_tag is None:
            if tag is None:
                raise ValueError(
                    "Cannot bump without pre_tag. Use .bump_pre('<tag>')")
        else:
            # This is an error because different tags have different meanings
            if tag is not None and self.pre_tag != tag:
                raise ValueError(
                    'Cannot bump with pre_tag mismatch ({0} != {1}). Use '
                    '.replace(pre_tag={1!r})'.format(self.pre_tag, tag))
            tag = self.pre_tag

        return self.replace(pre=pre, pre_tag=tag)

    def bump_post(self, tag=UNSET):
        """Return a new :class:`Version` instance with the post release number
        bumped.

        :param tag: Post release tag. Will preserve the current tag by default,
            or use `post` if the instance is not already a post release.
        :type tag: str

        .. doctest::

            >>> Version.parse('1.4').bump_post()
            <Version '1.4.post0'>
            >>> Version.parse('1.4.post0').bump_post(tag=None)
            <Version '1.4-1'>
            >>> Version.parse('1.4_post-1').bump_post(tag='rev')
            <Version '1.4_rev-2'>
        """
        post = 0 if self.post is None else self.post + 1
        if tag is UNSET and self.post is not None:
            tag = self.post_tag
        return self.replace(post=post, post_tag=tag)

    def bump_dev(self):
        """Return a new :class:`Version` instance with the development release
        number bumped.

        .. doctest::

            >>> Version.parse('1.4').bump_dev()
            <Version '1.4.dev0'>
            >>> Version.parse('1.4_dev1').bump_dev()
            <Version '1.4_dev2'>
        """
        dev = 0 if self.dev is None else self.dev + 1
        return self.replace(dev=dev)


def _normalize_pre_tag(pre_tag):
    if pre_tag is None:
        return None

    if pre_tag == 'alpha':
        pre_tag = 'a'
    elif pre_tag == 'beta':
        pre_tag = 'b'
    elif pre_tag in {'c', 'pre', 'preview'}:
        pre_tag = 'rc'

    return pre_tag


def _cmpkey(epoch, release, pre_tag, pre_num, post, dev, local):
    # When we compare a release version, we want to compare it with all of the
    # trailing zeros removed. So we'll use a reverse the list, drop all the now
    # leading zeros until we come to something non zero, then take the rest
    # re-reverse it back into the correct order and make it a tuple and use
    # that for our sorting key.
    release = tuple(
        reversed(list(
            itertools.dropwhile(
                lambda x: x == 0,
                reversed(release),
            )
        ))
    )

    pre = pre_tag, pre_num

    # We need to "trick" the sorting algorithm to put 1.0.dev0 before 1.0a0.
    # We'll do this by abusing the pre segment, but we _only_ want to do this
    # if there is not a pre or a post segment. If we have one of those then
    # the normal sorting rules will handle this case correctly.
    if pre_num is None and post is None and dev is not None:
        pre = -Infinity
    # Versions without a pre-release (except as noted above) should sort after
    # those with one.
    elif pre_num is None:
        pre = Infinity

    # Versions without a post segment should sort before those with one.
    if post is None:
        post = -Infinity

    # Versions without a development segment should sort after those with one.
    if dev is None:
        dev = Infinity

    if local is None:
        # Versions without a local segment should sort before those with one.
        local = -Infinity
    else:
        # Versions with a local segment need that segment parsed to implement
        # the sorting rules in PEP440.
        # - Alpha numeric segments sort before numeric segments
        # - Alpha numeric segments sort lexicographically
        # - Numeric segments sort numerically
        # - Shorter versions sort before longer versions when the prefixes
        #   match exactly
        local = tuple(
            (i, "") if isinstance(i, int) else (-Infinity, i)
            for i in _parse_local_version(local)
        )

    return epoch, release, pre, post, dev, local


_local_version_separators = re.compile(r"[._-]")


def _parse_local_version(local):
    """
    Takes a string like abc.1.twelve and turns it into ("abc", 1, "twelve").
    """
    if local is not None:
        return tuple(
            part.lower() if not part.isdigit() else int(part)
            for part in _local_version_separators.split(local)
        )
