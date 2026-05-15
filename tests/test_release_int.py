import pytest

from parver._release_int import ReleaseInt, intwidth


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 1),
        (12, 2),
        (-12, 2),
        ("0012", 4),
        (" +001_2 ", 4),
        ("-0012", 4),
    ],
)
def test_intwidth(value, expected):
    assert intwidth(value) == expected


@pytest.mark.parametrize(
    ("value", "expected_str", "expected_repr"),
    [
        (3, "3", "3"),
        ("003", "003", "ReleaseInt('003')"),
        (ReleaseInt("003"), "003", "ReleaseInt('003')"),
        (-3, "-3", "-3"),
        ("-003", "-003", "ReleaseInt('-003')"),
    ],
)
def test_release_int_construction(value, expected_str, expected_repr):
    release = ReleaseInt(value)

    assert str(release) == expected_str
    assert repr(release) == expected_repr


@pytest.mark.parametrize(
    ("value", "width", "expected"),
    [
        (5, 2, "05"),
        (50, 2, "50"),
        (ReleaseInt("005"), 2, "05"),
    ],
)
def test_release_int_width_override(value, width, expected):
    release = ReleaseInt(value, width=width)

    assert str(release) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (ReleaseInt(3), 0),
        (ReleaseInt("003"), ReleaseInt("000")),
        (ReleaseInt("-003"), ReleaseInt("000")),
    ],
)
def test_release_int_zero_like(value, expected):
    zero = value.zero_like()

    assert isinstance(zero, ReleaseInt)
    assert zero == expected
    assert str(zero) == str(expected)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (ReleaseInt("001"), 2, "003"),
        (ReleaseInt("099"), 1, "100"),
        (ReleaseInt("001"), 999, "1000"),
    ],
)
def test_release_int_add(left, right, expected):
    assert str(left + right) == expected


def test_release_int_radd():
    assert str(2 + ReleaseInt("001")) == "003"


@pytest.mark.parametrize(
    ("value", "other", "expected", "expected_zero"),
    [
        (ReleaseInt("09"), 1, "10", "00"),
        (ReleaseInt("9"), 1, "10", "0"),
    ],
)
def test_release_int_add_preserves_width_preference(
    value, other, expected, expected_zero
):
    result = value + other

    assert str(result) == expected
    assert repr(result) == repr(int(expected))
    assert str(result.zero_like()) == expected_zero


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (ReleaseInt("010"), 1, "009"),
        (ReleaseInt("010"), ReleaseInt("002"), "008"),
        (ReleaseInt("001"), 2, "-001"),
    ],
)
def test_release_int_sub(left, right, expected):
    assert str(left - right) == expected


def test_release_int_sub_preserves_width_preference():
    result = ReleaseInt("010") - 1

    assert str(result) == "009"
    assert repr(result) == "ReleaseInt('009')"
    assert str(result.zero_like()) == "000"


def test_release_int_invalid_type():
    with pytest.raises(TypeError, match=r"Unsupported type: <class 'float'>"):
        ReleaseInt(1.5)


@pytest.mark.parametrize(
    ("width", "error_type", "match"),
    [
        (True, TypeError, "width must be an integer"),
        (1.5, TypeError, "width must be an integer"),
        (0, ValueError, "width must be positive"),
    ],
)
def test_release_int_invalid_width(width, error_type, match):
    with pytest.raises(error_type, match=match):
        ReleaseInt(1, width=width)
