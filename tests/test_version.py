# coding: utf-8
from __future__ import absolute_import, division, print_function

import pytest

from parver import Version

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
