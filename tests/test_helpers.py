# coding: utf-8
from __future__ import absolute_import, division, print_function

import pytest

from parver._helpers import force_tuple, kwonly_args


@pytest.mark.parametrize('arg, expected', [
    (1, (1,)),
    ([1], (1,)),
    ((1, 2), (1, 2)),
    ([1, 2], (1, 2)),
    # range is a Sequence
    (range(1, 3), (1, 2)),
    # An iterable that is not also a sequence
    ((x for x in range(1, 3)), (1, 2)),
])
def test_force_tuple(arg, expected):
    assert force_tuple(arg) == expected


def fn1(a, **kwargs):
    kwargs, b, c = kwonly_args(kwargs, ('b',), (('c', 5),))
    return a, b, c


def fn2(a, *args, **kwargs):
    kwargs, b = kwonly_args(kwargs, ('b',), leftovers=True)
    return a, b, kwargs


@pytest.mark.parametrize('fn, args, kwargs, result', [
    (fn1, (1,), dict(b=2), (1, 2, 5)),
    (fn1, (1,), dict(b=2, c=3), (1, 2, 3)),
    (fn1, (), dict(b=2), TypeError),
    (fn1, (1, 2), dict(), TypeError),
    (fn1, (1,), dict(c=2), TypeError),
    (fn1, (1,), dict(b=2, d=4), TypeError),
    (fn2, (1,), dict(b=2), (1, 2, {})),
    (fn2, (1,), dict(b=2, c=3), (1, 2, dict(c=3))),
])
def test_kwonly_args(fn, args, kwargs, result):
    """Based on the snippet by Eric Snow
    http://code.activestate.com/recipes/577940

    SPDX-License-Identifier: MIT
    """
    try:
        isexception = issubclass(result, Exception)
    except TypeError:
        isexception = False

    if isexception:
        with pytest.raises(result):
            fn(*args, **kwargs)
    else:
        assert fn(*args, **kwargs) == result
