# coding: utf-8
from __future__ import absolute_import, division, print_function

import string

from parver import Version

from hypothesis.strategies import (
    composite, integers, just, lists, one_of, sampled_from, text)

num_int = integers(min_value=0)
num_str = num_int.map(str)


def epoch():
    epoch = num_str.map(lambda s: s + '!')
    return one_of(just(''), epoch)


@composite
def release(draw):
    a = draw(num_str)
    parts = [a] + draw(lists(num_str.map(lambda s: '.' + s)))
    return ''.join(parts)


def separator(strict=False, optional=False):
    sep = ['.']

    if optional:
        sep.append('')

    if not strict:
        sep.extend(['-', '_'])

    return sampled_from(sep)


@composite
def pre(draw, strict=False):
    words = ['a', 'b', 'rc']
    if not strict:
        words.extend(['c', 'alpha', 'beta', 'pre', 'preview'])

    sep1 = draw(separator(strict=strict, optional=True))
    if strict:
        sep1 = ''

    word = draw(sampled_from(words))

    if strict:
        sep2 = ''
    else:
        sep2 = draw(separator(strict=strict, optional=True))

    n = draw(num_str)

    if strict:
        num_part = draw(just(sep2 + n))
    else:
        num_part = draw(one_of(just(''), just(sep2 + n)))

    return draw(one_of(just(''), just(sep1 + word + num_part)))


@composite
def post(draw, strict=False):
    words = ['post']
    if not strict:
        words.extend(['r', 'rev'])

    sep1 = draw(separator(strict=strict, optional=not strict))
    word = draw(sampled_from(words))

    sep2 = draw(separator(strict=strict, optional=True))
    if strict:
        sep2 = ''

    n = draw(num_str)

    if strict:
        num_part = draw(just(sep2 + n))
    else:
        num_part = draw(one_of(just(''), just(sep2 + n)))

    post = sep1 + word + num_part

    if strict:
        return post

    post = just(post)
    post_implicit = num_str.map(lambda s: '-' + s)

    return draw(one_of(just(''), post_implicit, post))


@composite
def dev(draw, strict=False):
    sep = draw(separator(strict=strict, optional=not strict))

    if strict:
        num_part = draw(num_str)
    else:
        num_part = draw(one_of(just(''), num_str))

    return draw(one_of(just(''), just(sep + 'dev' + num_part)))


@composite
def local_segment(draw, strict=False):
    if strict:
        sep = just('.')
    else:
        sep = sampled_from('-_.')

    return draw(sep) + draw(text(string.ascii_lowercase + string.digits, min_size=1))


@composite
def local(draw, strict=False):
    start = draw(text(string.ascii_lowercase + string.digits, min_size=1))
    end = ''.join(draw(lists(local_segment(strict=strict))))

    return draw(one_of(just(''), just('+' + start + end)))


whitespace = sampled_from(['', '\t', '\n', '\r', '\f', '\v'])


def vchar(strict=False):
    if strict:
        return just('')
    return sampled_from(['', 'v'])


@composite
def version_string(draw, strict=False):
    return (
        draw(vchar(strict=strict)) +
        draw(epoch()) +
        draw(release()) +
        draw(pre(strict=strict)) +
        draw(post(strict=strict)) +
        draw(dev(strict=strict)) +
        draw(local(strict=strict))
    )


@composite
def version_strategy(draw, strict=False):
    return Version.parse(draw(version_string(strict=strict)))
