# coding: utf-8
from __future__ import absolute_import, division, print_function

import itertools
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
    if not isinstance(n, tuple):
        return n,
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
    dev_sep = attr.ib(default='.', validator=validate_sep)
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

        if self.post_sep1 is UNSET:
            set('post_sep1', '.')
        if self.post_sep2 is UNSET:
            set('post_sep2', None)

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

        if self.dev is UNSET:
            set('dev', None)

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
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)

    def _compare(self, other, method):
        if not isinstance(other, Version):
            return NotImplemented

        return method(self._key, other._key)

    @property
    def public(self):
        return str(self).split('+', 1)[0]

    @property
    def base_version(self):
        parts = []

        # Epoch
        if self.epoch != 0:
            parts.append('{0}!'.format(self.epoch))

        # Release segment
        parts.append('.'.join(str(x) for x in self.release))

        return ''.join(parts)

    @property
    def is_prerelease(self):
        return self.dev is not None or self.pre is not None

    @property
    def is_postrelease(self):
        return self.post is not None

    @property
    def is_devrelease(self):
        return self.dev is not None


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