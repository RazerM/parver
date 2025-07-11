import pytest
from hypothesis import HealthCheck, given, settings

from parver import Version

from .strategies import version_strategy


def v(*args, **kwargs):
    return args, kwargs


@pytest.mark.parametrize(
    "vargs, s",
    [
        (v(1), "1"),
        (v(release=(1,)), "1"),
        (v(release=(1, 2)), "1.2"),
        # epoch
        (v(release=1, epoch=""), "1"),
        (v(release=1, epoch=0), "0!1"),
        (v(release=1, epoch=1), "1!1"),
        (v(release=1, pre_tag=None), "1"),
        # pre_tag with implicit pre
        (v(release=1, pre="", pre_tag="c"), "1c"),
        (v(release=1, pre="", pre_tag="rc"), "1rc"),
        (v(release=1, pre="", pre_tag="alpha"), "1alpha"),
        (v(release=1, pre="", pre_tag="a"), "1a"),
        (v(release=1, pre="", pre_tag="beta"), "1beta"),
        (v(release=1, pre="", pre_tag="b"), "1b"),
        (v(release=1, pre="", pre_tag="preview"), "1preview"),
        (v(release=1, pre="", pre_tag="pre"), "1pre"),
        # pre_tag with pre
        (v(release=1, pre=0, pre_tag="c"), "1c0"),
        (v(release=1, pre=1, pre_tag="rc"), "1rc1"),
        (v(release=1, pre=2, pre_tag="alpha"), "1alpha2"),
        (v(release=1, pre=3, pre_tag="a"), "1a3"),
        (v(release=1, pre="", pre_tag="beta"), "1beta"),
        (v(release=1, pre=0, pre_tag="b"), "1b0"),
        (v(release=1, pre=0, pre_tag="preview"), "1preview0"),
        (v(release=1, pre=0, pre_tag="pre"), "1pre0"),
        # pre_tag with pre_sep1
        (v(release=1, pre="", pre_sep1=None, pre_tag="b"), "1b"),
        (v(release=1, pre="", pre_sep1=".", pre_tag="b"), "1.b"),
        (v(release=1, pre="", pre_sep1="-", pre_tag="b"), "1-b"),
        (v(release=1, pre="", pre_sep1="_", pre_tag="b"), "1_b"),
        # pre_tag with pre_sep2
        (v(release=2, pre=1, pre_sep2=None, pre_tag="b"), "2b1"),
        (v(release=2, pre=1, pre_sep2=".", pre_tag="b"), "2b.1"),
        (v(release=2, pre=1, pre_sep2="-", pre_tag="b"), "2b-1"),
        (v(release=2, pre=1, pre_sep2="_", pre_tag="b"), "2b_1"),
        # pre_tag with pre_sep1 and pre_sep2
        (v(release=2, pre=1, pre_sep1=".", pre_sep2=None, pre_tag="b"), "2.b1"),
        (v(release=2, pre=1, pre_sep1=".", pre_sep2=".", pre_tag="b"), "2.b.1"),
        (v(release=2, pre=1, pre_sep1=".", pre_sep2="-", pre_tag="b"), "2.b-1"),
        (v(release=2, pre=1, pre_sep1=".", pre_sep2="_", pre_tag="b"), "2.b_1"),
        # post
        (v(release=1, post=""), "1.post"),
        (v(release=1, post=0), "1.post0"),
        (v(release=1, post=1), "1.post1"),
        # post_tag
        (v(release=1, post=0, post_tag=None), "1-0"),
        (v(release=1, post="", post_tag="post"), "1.post"),
        (v(release=1, post="", post_tag="r"), "1.r"),
        (v(release=1, post="", post_tag="rev"), "1.rev"),
        # post with post_sep1
        (v(release=1, post="", post_sep1=None), "1post"),
        (v(release=1, post="", post_sep1="."), "1.post"),
        (v(release=1, post="", post_sep1="-"), "1-post"),
        (v(release=1, post="", post_sep1="_"), "1_post"),
        # post with post_sep2
        (v(release=2, post=1, post_sep2=None), "2.post1"),
        (v(release=2, post=1, post_sep2="."), "2.post.1"),
        (v(release=2, post=1, post_sep2="-"), "2.post-1"),
        (v(release=2, post=1, post_sep2="_"), "2.post_1"),
        # post with post_sep1 and post_sep2
        (v(release=2, post=1, post_sep1=".", post_sep2=None), "2.post1"),
        (v(release=2, post=1, post_sep1=".", post_sep2="."), "2.post.1"),
        (v(release=2, post=1, post_sep1=".", post_sep2="-"), "2.post-1"),
        (v(release=2, post=1, post_sep1=".", post_sep2="_"), "2.post_1"),
        # dev
        (v(release=1, dev=""), "1.dev"),
        (v(release=1, dev=0), "1.dev0"),
        (v(release=1, dev=1), "1.dev1"),
        # local
        (v(release=1, local=None), "1"),
        (v(release=1, local="a"), "1+a"),
        (v(release=1, local="0"), "1+0"),
        (v(release=1, local="a0"), "1+a0"),
        (v(release=1, local="a.0"), "1+a.0"),
        (v(release=1, local="0-0"), "1+0-0"),
        (v(release=1, local="0_a"), "1+0_a"),
    ],
)
def test_init(vargs, s):
    args, kwargs = vargs
    assert str(Version(*args, **kwargs)) == s


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(pre=1),
        dict(pre_sep1="."),
        dict(pre_sep2="."),
        dict(pre_sep1=".", pre_sep2="."),
        dict(post_tag=None),
        dict(post_tag=None, post=""),
        dict(post_tag=None, post_sep1="."),
        dict(post_tag=None, post_sep2="."),
        dict(post_tag=None, post_sep1=".", post_sep2="."),
        dict(pre_tag="a"),
        dict(dev=None, dev_sep1="."),
        dict(dev=None, dev_sep2="."),
        dict(dev=None, post_sep1="."),
        dict(dev=None, post_sep2="."),
    ],
)
def test_invalid(kwargs):
    """Test bad keyword combinations."""
    with pytest.raises(ValueError):
        Version(release=1, **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(release="1"),
        dict(v=3),
        dict(post=True),
        dict(epoch="1"),
        dict(pre_tag="b", pre="2"),
        dict(post="3"),
        dict(dev="3"),
        dict(local=[1, "abc"]),
        dict(local=1),
    ],
)
def test_validation_type(kwargs):
    if "release" not in kwargs:
        kwargs["release"] = 1

    with pytest.raises(TypeError):
        # print so we can see output when test fails
        print(Version(**kwargs))


@pytest.mark.parametrize(
    "release, exc, match",
    [
        ([], ValueError, "'release' cannot be empty"),
        (-1, ValueError, r"'release' must be non-negative \(got -1\)"),
        ([4, -1], ValueError, r"'release' must be non-negative \(got -1\)"),
        ([4, "a"], TypeError, r"'release' must be.*int"),
        ([4, True], TypeError, r"'release' must not be a bool"),
    ],
)
def test_release_validation(release, exc, match):
    with pytest.raises(exc, match=match):
        Version(release=release)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(pre_tag="alph"),
        dict(pre_tag="a", pre_sep1="x"),
        dict(pre_tag="a", pre_sep2="x"),
        dict(post=1, post_sep1="x"),
        dict(post=1, post_sep2="x"),
        dict(dev=4, dev_sep1="y"),
        dict(dev=4, dev_sep2="y"),
        dict(post_tag=None, post=1, post_sep1="."),
        dict(post_tag=None, post=1, post_sep2="."),
        dict(epoch=-1),
        dict(pre_tag="a", pre=-1),
        dict(post=-1),
        dict(dev=-1),
    ],
)
def test_validation_value(kwargs):
    kwargs.setdefault("release", 1)

    with pytest.raises(ValueError):
        # print so we can see output when test fails
        print(Version(**kwargs))


@pytest.mark.parametrize(
    "kwargs, values, version",
    [
        (
            dict(release=1),
            dict(
                release=(1,),
                v=False,
                epoch=0,
                epoch_implicit=True,
                pre_tag=None,
                pre=None,
                pre_implicit=False,
                pre_sep1=None,
                pre_sep2=None,
                post=None,
                post_tag=None,
                post_implicit=False,
                post_sep1=None,
                post_sep2=None,
                dev=None,
                dev_implicit=False,
                dev_sep1=None,
                dev_sep2=None,
                local=None,
            ),
            "1",
        ),
        (
            dict(epoch=0),
            dict(epoch=0, epoch_implicit=False),
            "0!1",
        ),
        (
            dict(pre="", pre_tag="b"),
            dict(
                pre=0,
                pre_tag="b",
                pre_implicit=True,
                pre_sep1=None,
                pre_sep2=None,
            ),
            "1b",
        ),
        (
            dict(pre=0, pre_tag="a"),
            dict(
                pre=0,
                pre_tag="a",
                pre_implicit=False,
                pre_sep1=None,
                pre_sep2=None,
            ),
            "1a0",
        ),
        (
            dict(pre=2, pre_tag="pre", pre_sep1="-", pre_sep2="."),
            dict(
                pre=2,
                pre_tag="pre",
                pre_implicit=False,
                pre_sep1="-",
                pre_sep2=".",
            ),
            "1-pre.2",
        ),
        (
            dict(post=""),
            dict(
                post=0,
                post_tag="post",
                post_implicit=True,
                post_sep1=".",
                post_sep2=None,
            ),
            "1.post",
        ),
        (
            dict(post="", post_sep2="."),
            dict(
                post=0,
                post_tag="post",
                post_implicit=True,
                post_sep1=".",
                post_sep2=".",
            ),
            "1.post.",
        ),
        (
            dict(post=0),
            dict(
                post=0,
                post_tag="post",
                post_implicit=False,
                post_sep1=".",
                post_sep2=None,
            ),
            "1.post0",
        ),
        (
            dict(post=0, post_tag=None),
            dict(
                post=0,
                post_tag=None,
                post_implicit=False,
                post_sep1="-",
                post_sep2=None,
            ),
            "1-0",
        ),
        (
            dict(post=3, post_tag="rev", post_sep1="-", post_sep2="_"),
            dict(
                post=3,
                post_tag="rev",
                post_implicit=False,
                post_sep1="-",
                post_sep2="_",
            ),
            "1-rev_3",
        ),
        (
            dict(dev=""),
            dict(dev=0, dev_implicit=True, dev_sep1="."),
            "1.dev",
        ),
        (
            dict(dev=2),
            dict(dev=2, dev_implicit=False, dev_sep1="."),
            "1.dev2",
        ),
        (
            dict(dev=0, dev_sep1="-"),
            dict(dev=0, dev_implicit=False, dev_sep1="-"),
            "1-dev0",
        ),
        (
            dict(dev=0, dev_sep2="-"),
            dict(dev=0, dev_implicit=False, dev_sep1=".", dev_sep2="-"),
            "1.dev-0",
        ),
        (
            dict(local="a.b"),
            dict(local="a.b"),
            "1+a.b",
        ),
    ],
)
def test_attributes(kwargs, values, version):
    # save us repeating ourselves in test data above
    kwargs.setdefault("release", 1)

    v = Version(**kwargs)
    assert str(v) == version
    for key, value in values.items():
        assert getattr(v, key) == value, key


@given(version_strategy())
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_replace_roundtrip(version):
    """All the logic inside replace() is in converting the attributes to the
    form expected by __init__, so this function tests most of that.
    """
    assert version.replace() == version


@pytest.mark.parametrize(
    "before, kwargs, after",
    [
        (
            "v0!1.2.alpha-3_rev.4_dev5+l.6",
            dict(
                release=(2, 1),
                epoch="",
                v=False,
                pre_tag="a",
                pre_sep1=None,
                pre_sep2=None,
                post_tag="post",
                post_sep1=".",
                post_sep2=None,
                dev_sep1=".",
                dev_sep2=".",
                local=None,
            ),
            "2.1a3.post4.dev.5",
        ),
        (
            "2.1a3.post4.dev5",
            dict(
                release=(1, 2),
                epoch=0,
                v=True,
                pre_tag="alpha",
                pre_sep1=".",
                pre_sep2="-",
                post_tag="rev",
                post_sep1="_",
                post_sep2=".",
                dev_sep1="_",
                dev_sep2="-",
                local="l.6",
            ),
            "v0!1.2.alpha-3_rev.4_dev-5+l.6",
        ),
        (
            "2.post4",
            dict(post_tag=None),
            "2-4",
        ),
        (
            "1.2.alpha-3_rev.4_dev5",
            dict(pre=None, post=None, dev=None),
            "1.2",
        ),
        (
            "1.2.alpha-3_rev.4_dev5",
            dict(pre=None, post=None, dev=None),
            "1.2",
        ),
        (
            "1.2",
            dict(pre=None, post=None, dev=None),
            "1.2",
        ),
        # Verify that the dot between post and dev is parsed as dev_sep1 and
        # not post_sep2
        (
            "1.post.dev",
            dict(post=None),
            "1.dev",
        ),
        # Verify that the dot between pre and dev is parsed as dev_sep1 and
        # not pre_sep2
        (
            "1.pre.dev",
            dict(pre=None),
            "1.dev",
        ),
        # Verify that the dot between pre and post is parsed as post_sep1 and
        # not pre_sep2
        (
            "1.pre.post",
            dict(pre=None),
            "1.post",
        ),
    ],
)
def test_replace(before, kwargs, after):
    """Make sure the keys we expect are passed through."""
    assert str(Version.parse(before).replace(**kwargs)) == after


@pytest.mark.parametrize(
    "before, index, after",
    [
        ("1", 0, "2"),
        ("1", 1, "1.1"),
        ("1", 2, "1.0.1"),
        ("1.1", 0, "2.0"),
        ("1.1", 1, "1.2"),
        ("1.1", 2, "1.1.1"),
        ("1.1", 3, "1.1.0.1"),
        ("4.3.2.1", 2, "4.3.3.0"),
    ],
)
def test_bump_release(before, index, after):
    assert str(Version.parse(before).bump_release(index=index)) == after


@pytest.mark.parametrize(
    "before, index, value, after",
    [
        ("2", 0, 1, "1"),
        ("2", 0, 2, "2"),
        ("2", 0, 3, "3"),
        ("2", 1, 3, "2.3"),
        ("2", 2, 3, "2.0.3"),
        ("2.4", 0, 4, "4.0"),
        ("2.4", 1, 6, "2.6"),
        ("2.4", 2, 6, "2.4.6"),
        ("2.4", 3, 6, "2.4.0.6"),
        ("4.3.2.1", 1, 5, "4.5.0.0"),
        # e.g. CalVer
        ("2017.4", 0, 2018, "2018.0"),
        ("17.5.1", 0, 18, "18.0.0"),
        ("18.0.0", 1, 2, "18.2.0"),
    ],
)
def test_bump_release_to(before, index, value, after):
    v = Version.parse(before).bump_release_to(index=index, value=value)
    assert str(v) == after


@pytest.mark.parametrize(
    "before, index, value, after",
    [
        ("2", 0, 1, "1"),
        ("2", 0, 2, "2"),
        ("2", 0, 3, "3"),
        ("2", 1, 3, "2.3"),
        ("2", 2, 3, "2.0.3"),
        ("2.4", 0, 4, "4.4"),
        ("2.4", 1, 6, "2.6"),
        ("2.4", 2, 6, "2.4.6"),
        ("2.4", 3, 6, "2.4.0.6"),
        ("2.0.4", 1, 3, "2.3.4"),
        ("4.3.2.1", 1, 5, "4.5.2.1"),
    ],
)
def test_set_release(before, index, value, after):
    v = Version.parse(before).set_release(index=index, value=value)
    assert str(v) == after


@pytest.mark.parametrize(
    "index, exc",
    [
        ("1", TypeError),
        (1.1, TypeError),
        (-1, ValueError),
    ],
)
def test_bump_release_error(index, exc):
    with pytest.raises(exc):
        print(Version(release=1).bump_release(index=index))


@pytest.mark.parametrize(
    "by",
    [
        "1",
        1.1,
        None,
    ],
)
def test_bump_by_error(by):
    v = Version(release=1)

    with pytest.raises(TypeError):
        v.bump_epoch(by=by)

    with pytest.raises(TypeError):
        v.bump_dev(by=by)

    with pytest.raises(TypeError):
        v.bump_pre("a", by=by)

    with pytest.raises(TypeError):
        v.bump_post(by=by)


def test_bump_by_value_error():
    v = Version(release=1)

    with pytest.raises(ValueError, match="negative"):
        v.bump_epoch(by=-1)

    with pytest.raises(ValueError, match="negative"):
        v.bump_dev(by=-1)

    with pytest.raises(ValueError, match="negative"):
        v.bump_pre(by=-1)

    with pytest.raises(ValueError, match="negative"):
        v.bump_post(by=-1)


@pytest.mark.parametrize(
    "before, tag, kwargs, after",
    [
        ("1", "a", dict(), "1a0"),
        ("1", "a", dict(by=2), "1a1"),
        ("1a0", None, dict(), "1a1"),
        ("1a", None, dict(), "1a1"),
        ("1a", "a", dict(), "1a1"),
        ("1.b-0", None, dict(), "1.b-1"),
        ("1a1", None, dict(by=-1), "1a0"),
    ],
)
def test_bump_pre(before, tag, kwargs, after):
    assert str(Version.parse(before).bump_pre(tag, **kwargs)) == after


@pytest.mark.parametrize(
    "version, tag",
    [
        ("1.2", None),
        ("1.2a", "b"),
    ],
)
def test_bump_pre_error(version, tag):
    with pytest.raises(ValueError):
        print(Version.parse(version).bump_pre(tag))


@pytest.mark.parametrize(
    "before, kwargs, after",
    [
        ("1", dict(), "1.post0"),
        ("1", dict(by=2), "1.post1"),
        ("1.post0", dict(), "1.post1"),
        ("1rev", dict(), "1rev1"),
        ("1-0", dict(), "1-1"),
        ("1-0", dict(tag="post"), "1.post1"),
        ("1-post_0", dict(tag=None), "1-1"),
        ("1.post1", dict(by=-1), "1.post0"),
    ],
)
def test_bump_post(before, kwargs, after):
    assert str(Version.parse(before).bump_post(**kwargs)) == after


@pytest.mark.parametrize(
    "before, kwargs, after",
    [
        ("1", dict(), "1.dev0"),
        ("1", dict(by=2), "1.dev1"),
        ("1.dev0", dict(), "1.dev1"),
        ("1-dev1", dict(), "1-dev2"),
        ("1-dev1", dict(by=-1), "1-dev0"),
    ],
)
def test_bump_dev(before, kwargs, after):
    assert str(Version.parse(before).bump_dev(**kwargs)) == after


@pytest.mark.parametrize(
    "before, kwargs, after",
    [
        ("2", dict(), "1!2"),
        ("2", dict(by=2), "2!2"),
        ("0!3", dict(), "1!3"),
        ("1!4", dict(), "2!4"),
        ("1!4", dict(by=-1), "0!4"),
        ("1!4", dict(by=2), "3!4"),
    ],
)
def test_bump_epoch(before, kwargs, after):
    assert str(Version.parse(before).bump_epoch(**kwargs)) == after


@pytest.mark.parametrize(
    "arg, expected",
    [
        (1, (1,)),
        ([1], (1,)),
        ((1, 2), (1, 2)),
        ([1, 2], (1, 2)),
        # range is a Sequence
        (range(1, 3), (1, 2)),
        # An iterable that is not also a sequence
        ((x for x in range(1, 3)), (1, 2)),
    ],
)
def test_release_tuple(arg, expected):
    v = Version(release=arg)
    assert isinstance(v.release, tuple)
    assert v.release == expected


@pytest.mark.parametrize(
    "version",
    [
        "1a",
        "1alpha",
        "1a1",
    ],
)
def test_is_alpha(version):
    v = Version.parse(version)
    assert v.is_alpha
    assert not v.is_beta
    assert not v.is_release_candidate


@pytest.mark.parametrize(
    "version",
    [
        "1b",
        "1beta",
        "1b1",
    ],
)
def test_is_beta(version):
    v = Version.parse(version)
    assert not v.is_alpha
    assert v.is_beta
    assert not v.is_release_candidate


@pytest.mark.parametrize(
    "version",
    [
        "1rc",
        "1c",
        "1pre",
        "1preview",
        "1rc1",
    ],
)
def test_is_release_candidate(version):
    v = Version.parse(version)
    assert not v.is_alpha
    assert not v.is_beta
    assert v.is_release_candidate


def test_ambiguous():
    with pytest.raises(ValueError, match="post_tag.*pre"):
        Version(release=1, pre="", pre_tag="rc", post=2, post_tag=None)

    v = Version(release=1, pre="", pre_tag="rc", pre_sep2=".", post=2, post_tag=None)
    assert str(v) == "1rc.-2"
    assert str(v.normalize()) == "1rc0.post2"


@pytest.mark.parametrize(
    "before, after, kwargs",
    [
        ("1.0", "1", dict()),
        ("1.0.0", "1", dict()),
        ("1.0.0", "1.0", dict(min_length=2)),
        ("1", "1.0", dict(min_length=2)),
        ("0.0", "0", dict()),
        ("1.0.2", "1.0.2", dict()),
        ("1.0.2", "1.0.2", dict(min_length=1)),
        ("1.0.2.0", "1.0.2", dict()),
        ("1.2.0", "1.2", dict()),
    ],
)
def test_truncate(before, after, kwargs):
    v = Version.parse(before).truncate(**kwargs)
    assert str(v) == after


def test_truncate_error():
    with pytest.raises(TypeError, match="min_length"):
        Version.parse("1").truncate(min_length="banana")

    with pytest.raises(ValueError, match="min_length"):
        Version.parse("1").truncate(min_length=0)


def test_public_module():
    assert Version.__module__ == "parver"
