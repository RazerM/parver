import pytest

from parver._helpers import UNSET, Infinity, NegativeInfinity, last


def test_unset_repr():
    assert repr(UNSET) == "UNSET"


def test_infinity_not_equal():
    assert (Infinity != object()) is True
    assert (Infinity != Infinity) is False
    assert (NegativeInfinity != object()) is True
    assert (NegativeInfinity != NegativeInfinity) is False


def test_negative_infinity_negates_to_infinity():
    assert -NegativeInfinity is Infinity


def test_last_without_default_raises_for_empty_iterable():
    with pytest.raises(IndexError):
        last([])
