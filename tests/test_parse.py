# coding: utf-8
from __future__ import absolute_import, division, print_function

from hypothesis import given

from parver import Version

from .strategies import version_string, whitespace


@given(whitespace, version_string(), whitespace)
def test_parse_permissive_hypothesis(prefix, version, suffix):
    Version.parse(prefix + version + suffix)


@given(whitespace, version_string(strict=True), whitespace)
def test_parse_canonical_hypothesis(prefix, version, suffix):
    Version.parse(prefix + version + suffix, strict=True)


@given(version_string())
def test_roundtrip(version):
    assert str(Version.parse(version)) == version
