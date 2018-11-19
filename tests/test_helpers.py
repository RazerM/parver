# coding: utf-8
from __future__ import absolute_import, division, print_function

import pytest

from parver._helpers import force_tuple


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
