# coding: utf-8
from __future__ import absolute_import, division, print_function

import pytest
from hypothesis import assume, given

from parver import ParseError, Version

from .strategies import version_string, whitespace


@given(whitespace, version_string(), whitespace)
def test_parse_hypothesis(prefix, version, suffix):
    Version.parse(prefix + version + suffix)


@given(whitespace, version_string(strict=True), whitespace)
def test_parse_strict_hypothesis(prefix, version, suffix):
    Version.parse(prefix + version + suffix, strict=True)


@given(version_string(strict=False))
def test_parse_strict_error(version):
    v = Version.parse(version)

    # Exclude already normalized versions
    assume(str(v.normalize()) != version)

    # 0!1 normalizes to '1'
    assume(v.epoch != 0 or v.epoch_implicit)

    with pytest.raises(ParseError):
        Version.parse(version, strict=True)


@given(version_string())
def test_roundtrip(version):
    assert str(Version.parse(version)) == version
