# coding: utf-8
from __future__ import absolute_import, division, print_function

import pytest
from hypothesis import given

from parver import Version

from .strategies import version_strategy


def v(*args, **kwargs):
    return args, kwargs


@pytest.mark.parametrize('vargs, s', [
    (v(1), '1'),
    (v(release=(1,)), '1'),
    (v(release=(1, 2)), '1.2'),
    # epoch
    (v(release=1, epoch=None), '1'),
    (v(release=1, epoch=0), '0!1'),
    (v(release=1, epoch=1), '1!1'),
    (v(release=1, pre_tag=None), '1'),
    # pre_tag without pre
    (v(release=1, pre_tag='c'), '1c'),
    (v(release=1, pre_tag='rc'), '1rc'),
    (v(release=1, pre_tag='alpha'), '1alpha'),
    (v(release=1, pre_tag='a'), '1a'),
    (v(release=1, pre_tag='beta'), '1beta'),
    (v(release=1, pre_tag='b'), '1b'),
    (v(release=1, pre_tag='preview'), '1preview'),
    (v(release=1, pre_tag='pre'), '1pre'),
    # pre_tag with pre
    (v(release=1, pre=0, pre_tag='c'), '1c0'),
    (v(release=1, pre=1, pre_tag='rc'), '1rc1'),
    (v(release=1, pre=2, pre_tag='alpha'), '1alpha2'),
    (v(release=1, pre=3, pre_tag='a'), '1a3'),
    (v(release=1, pre=None, pre_tag='beta'), '1beta'),
    (v(release=1, pre=0, pre_tag='b'), '1b0'),
    (v(release=1, pre=0, pre_tag='preview'), '1preview0'),
    (v(release=1, pre=0, pre_tag='pre'), '1pre0'),
    # pre_tag with pre_sep1
    (v(release=1, pre_sep1=None, pre_tag='b'), '1b'),
    (v(release=1, pre_sep1='.', pre_tag='b'), '1.b'),
    (v(release=1, pre_sep1='-', pre_tag='b'), '1-b'),
    (v(release=1, pre_sep1='_', pre_tag='b'), '1_b'),
    # pre_tag with pre_sep2
    (v(release=2, pre=1, pre_sep2=None, pre_tag='b'), '2b1'),
    (v(release=2, pre=1, pre_sep2='.', pre_tag='b'), '2b.1'),
    (v(release=2, pre=1, pre_sep2='-', pre_tag='b'), '2b-1'),
    (v(release=2, pre=1, pre_sep2='_', pre_tag='b'), '2b_1'),
    # pre_tag with pre_sep1 and pre_sep2
    (v(release=2, pre=1, pre_sep1='.', pre_sep2=None, pre_tag='b'), '2.b1'),
    (v(release=2, pre=1, pre_sep1='.', pre_sep2='.', pre_tag='b'), '2.b.1'),
    (v(release=2, pre=1, pre_sep1='.', pre_sep2='-', pre_tag='b'), '2.b-1'),
    (v(release=2, pre=1, pre_sep1='.', pre_sep2='_', pre_tag='b'), '2.b_1'),
    # post
    (v(release=1, post=None), '1.post'),
    (v(release=1, post=0), '1.post0'),
    (v(release=1, post=1), '1.post1'),
    # post_tag
    (v(release=1, post=0, post_tag=None), '1-0'),
    (v(release=1, post=None, post_tag='post'), '1.post'),
    (v(release=1, post=None, post_tag='r'), '1.r'),
    (v(release=1, post=None, post_tag='rev'), '1.rev'),
    (v(release=1, post_tag='post'), '1.post'),
    (v(release=1, post_tag='r'), '1.r'),
    (v(release=1, post_tag='rev'), '1.rev'),
    # post with post_sep1
    (v(release=1, post=None, post_sep1=None), '1post'),
    (v(release=1, post=None, post_sep1='.'), '1.post'),
    (v(release=1, post=None, post_sep1='-'), '1-post'),
    (v(release=1, post=None, post_sep1='_'), '1_post'),
    # post with post_sep2
    (v(release=2, post=1, post_sep2=None), '2.post1'),
    (v(release=2, post=1, post_sep2='.'), '2.post.1'),
    (v(release=2, post=1, post_sep2='-'), '2.post-1'),
    (v(release=2, post=1, post_sep2='_'), '2.post_1'),
    # post with post_sep1 and post_sep2
    (v(release=2, post=1, post_sep1='.', post_sep2=None), '2.post1'),
    (v(release=2, post=1, post_sep1='.', post_sep2='.'), '2.post.1'),
    (v(release=2, post=1, post_sep1='.', post_sep2='-'), '2.post-1'),
    (v(release=2, post=1, post_sep1='.', post_sep2='_'), '2.post_1'),
    # dev
    (v(release=1, dev=None), '1.dev'),
    (v(release=1, dev=0), '1.dev0'),
    (v(release=1, dev=1), '1.dev1'),
    # local
    (v(release=1, local=None), '1'),
    (v(release=1, local='a'), '1+a'),
    (v(release=1, local='0'), '1+0'),
    (v(release=1, local='a0'), '1+a0'),
    (v(release=1, local='a.0'), '1+a.0'),
    (v(release=1, local='0-0'), '1+0-0'),
    (v(release=1, local='0_a'), '1+0_a'),
])
def test_init(vargs, s):
    args, kwargs = vargs
    assert str(Version(*args, **kwargs)) == s


@pytest.mark.parametrize('kwargs', [
    dict(pre=1),
    dict(pre_sep1='.'),
    dict(pre_sep2='.'),
    dict(pre_sep1='.', pre_sep2='.'),
    dict(post_tag=None),
    dict(post_tag=None, post_sep1='.'),
    dict(post_tag=None, post_sep2='.'),
    dict(post_tag=None, post_sep1='.', post_sep2='.'),
])
def test_invalid(kwargs):
    """Test bad keyword combinations."""
    with pytest.raises(ValueError):
        Version(release=1, **kwargs)


@pytest.mark.parametrize('kwargs', [
    dict(release='1'),
    dict(v=3),
    dict(epoch='1'),
    dict(pre_tag='b', pre='2'),
    dict(post='3'),
    dict(dev='3'),
    dict(local=[1, 'abc']),
    dict(local=1),
])
def test_validation_type(kwargs):
    if 'release' not in kwargs:
        kwargs['release'] = 1

    with pytest.raises(TypeError):
        # print so we can see output when test fails
        print(Version(**kwargs))


@pytest.mark.parametrize('kwargs', [
    dict(pre_tag='alph'),
    dict(pre_tag='a', pre_sep1='x'),
    dict(pre_tag='a', pre_sep2='x'),
    dict(post=1, post_sep1='x'),
    dict(post=1, post_sep2='x'),
    dict(dev=4, dev_sep='y'),
    dict(post_tag=None, post=1, post_sep1='.'),
    dict(post_tag=None, post=1, post_sep2='.'),
])
def test_validation_value(kwargs):
    if 'release' not in kwargs:
        kwargs['release'] = 1

    with pytest.raises(ValueError):
        # print so we can see output when test fails
        print(Version(**kwargs))


@pytest.mark.parametrize('kwargs, values, version', [
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
            dev_sep=None,
            local=None,
        ),
        '1',
    ),
    (
        dict(epoch=0),
        dict(epoch=0, epoch_implicit=False),
        '0!1',
    ),
    (
        dict(pre=None, pre_tag='b'),
        dict(
            pre=0,
            pre_tag='b',
            pre_implicit=True,
            pre_sep1=None,
            pre_sep2=None,
        ),
        '1b',
    ),
    (
        dict(pre=0, pre_tag='a'),
        dict(
            pre=0,
            pre_tag='a',
            pre_implicit=False,
            pre_sep1=None,
            pre_sep2=None,
        ),
        '1a0',
    ),
    (
        dict(pre=2, pre_tag='pre', pre_sep1='-', pre_sep2='.'),
        dict(
            pre=2,
            pre_tag='pre',
            pre_implicit=False,
            pre_sep1='-',
            pre_sep2='.',
        ),
        '1-pre.2',
    ),
    (
        dict(post=None),
        dict(
            post=0,
            post_tag='post',
            post_implicit=True,
            post_sep1='.',
            post_sep2=None,
        ),
        '1.post',
    ),
    (
        dict(post=None, post_sep2='.'),
        dict(
            post=0,
            post_tag='post',
            post_implicit=True,
            post_sep1='.',
            post_sep2='.',
        ),
        '1.post.',
    ),
    (
        dict(post=0),
        dict(
            post=0,
            post_tag='post',
            post_implicit=False,
            post_sep1='.',
            post_sep2=None,
        ),
        '1.post0',
    ),
    (
        dict(post=0, post_tag=None),
        dict(
            post=0,
            post_tag=None,
            post_implicit=False,
            post_sep1='-',
            post_sep2=None,
        ),
        '1-0',
    ),
    (
        dict(post=3, post_tag='rev', post_sep1='-', post_sep2='_'),
        dict(
            post=3,
            post_tag='rev',
            post_implicit=False,
            post_sep1='-',
            post_sep2='_',
        ),
        '1-rev_3',
    ),
    (
        dict(dev=None),
        dict(dev=0, dev_implicit=True, dev_sep='.'),
        '1.dev',
    ),
    (
        dict(dev=2),
        dict(dev=2, dev_implicit=False, dev_sep='.'),
        '1.dev2',
    ),
    (
        dict(dev=0, dev_sep='-'),
        dict(dev=0, dev_implicit=False, dev_sep='-'),
        '1-dev0',
    ),
    (
        dict(local='a.b'),
        dict(local='a.b'),
        '1+a.b',
    ),
])
def test_attributes(kwargs, values, version):
    # save us repeating ourselves in test data above
    kwargs.setdefault('release', 1)

    v = Version(**kwargs)
    assert str(v) == version
    for key, value in values.items():
        assert getattr(v, key) == value


@given(version_strategy())
def test_replace_roundtrip(version):
    """All the logic inside replace() is in converting the attributes to the
    form expected by __init__, so this function tests most of that.
    """
    assert version.replace() == version


@pytest.mark.parametrize('before, kwargs, after', [
    (
        'v0!1.2.alpha-3_rev.4_dev5+l.6',
        dict(
            release=(2, 1),
            epoch=None,
            v=False,
            pre_tag='a',
            pre_sep1=None,
            pre_sep2=None,
            post_tag='post',
            post_sep1='.',
            post_sep2=None,
            dev_sep='.',
            local=None
        ),
        '2.1a3.post4.dev5',
    ),
    (
        '2.1a3.post4.dev5',
        dict(
            release=(1, 2),
            epoch=0,
            v=True,
            pre_tag='alpha',
            pre_sep1='.',
            pre_sep2='-',
            post_tag='rev',
            post_sep1='_',
            post_sep2='.',
            dev_sep='_',
            local='l.6'
        ),
        'v0!1.2.alpha-3_rev.4_dev5+l.6',
    ),
    (
        '2.post4',
        dict(post_tag=None),
        '2-4',
    ),
])
def test_replace(before, kwargs, after):
    """Make sure the keys we expect are passed through."""
    assert str(Version.parse(before).replace(**kwargs)) == after


@pytest.mark.parametrize('before, kwargs, after', [
    (
        '1.2.alpha-3_rev.4_dev5',
        dict(pre=True, post=True, dev=True),
        '1.2',
    ),
    (
        '1.2.alpha-3_rev.4_dev5',
        dict(pre=False, post=False, dev=False),
        '1.2.alpha-3_rev.4_dev5',
    ),
    (
        '1.2.alpha-3_rev.4_dev5',
        dict(),
        '1.2.alpha-3_rev.4_dev5',
    ),
    (
        '1.2',
        dict(pre=True, post=True, dev=True),
        '1.2',
    ),
])
def test_clear(before, kwargs, after):
    assert str(Version.parse(before).clear(**kwargs)) == after


@pytest.mark.parametrize('before, index, after', [
    ('1', 0, '2'),
    ('1', 1, '1.1'),
    ('1', 2, '1.0.1'),
    ('1.1', 0, '2.0'),
    ('1.1', 1, '1.2'),
    ('1.1', 2, '1.1.1'),
    ('1.1', 3, '1.1.0.1'),
    ('4.3.2.1', 2, '4.3.3.0'),
])
def test_bump_release(before, index, after):
    assert str(Version.parse(before).bump_release(index)) == after


@pytest.mark.parametrize('index, exc', [
    ('1', TypeError),
    (1.1, TypeError),
    (-1, ValueError),
])
def test_bump_release_error(index, exc):
    with pytest.raises(exc):
        print(Version(release=1).bump_release(index))


@pytest.mark.parametrize('before, tag, after', [
    ('1', 'a', '1a0'),
    ('1a0', None, '1a1'),
    ('1a', None, '1a1'),
    ('1a', 'a', '1a1'),
    ('1.b-0', None, '1.b-1'),
])
def test_bump_pre(before, tag, after):
    assert str(Version.parse(before).bump_pre(tag)) == after


@pytest.mark.parametrize('version, tag', [
    ('1.2', None),
    ('1.2a', 'b'),
])
def test_bump_pre_error(version, tag):
    with pytest.raises(ValueError):
        print(Version.parse(version).bump_pre(tag))


@pytest.mark.parametrize('before, kwargs, after', [
    ('1', dict(), '1.post0'),
    ('1.post0', dict(), '1.post1'),
    ('1rev', dict(), '1rev1'),
    ('1-0', dict(), '1-1'),
    ('1-0', dict(tag='post'), '1.post1'),
    ('1-post_0', dict(tag=None), '1-1'),
])
def test_bump_post(before, kwargs, after):
    assert str(Version.parse(before).bump_post(**kwargs)) == after


@pytest.mark.parametrize('before, after', [
    ('1', '1.dev0'),
    ('1.dev0', '1.dev1'),
    ('1-dev1', '1-dev2'),
])
def test_bump_dev(before, after):
    assert str(Version.parse(before).bump_dev()) == after


def test_release_tuple():
    v = Version(release=[1, 2])
    assert isinstance(v.release, tuple)


@pytest.mark.parametrize('version', [
    '1a',
    '1alpha',
    '1a1',
])
def test_is_alpha(version):
    v = Version.parse(version)
    assert v.is_alpha
    assert not v.is_beta
    assert not v.is_release_candidate


@pytest.mark.parametrize('version', [
    '1b',
    '1beta',
    '1b1',
])
def test_is_beta(version):
    v = Version.parse(version)
    assert not v.is_alpha
    assert v.is_beta
    assert not v.is_release_candidate


@pytest.mark.parametrize('version', [
    '1rc',
    '1c',
    '1pre',
    '1preview',
    '1rc1',
])
def test_is_release_candidate(version):
    v = Version.parse(version)
    assert not v.is_alpha
    assert not v.is_beta
    assert v.is_release_candidate
