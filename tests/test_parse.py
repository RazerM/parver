# coding: utf-8
from __future__ import absolute_import, division, print_function

import pytest
from hypothesis import given

from parver import Version

from .strategies import version_string, whitespace

PACKAGING_VERSIONS = [
    # Implicit epoch of 0
    "1.0.dev456", "1.0a1", "1.0a2.dev456", "1.0a12.dev456", "1.0a12",
    "1.0b1.dev456", "1.0b2", "1.0b2.post345.dev456", "1.0b2.post345",
    "1.0b2-346", "1.0c1.dev456", "1.0c1", "1.0rc2", "1.0c3", "1.0",
    "1.0.post456.dev34", "1.0.post456", "1.1.dev1", "1.2+123abc",
    "1.2+123abc456", "1.2+abc", "1.2+abc123", "1.2+abc123def", "1.2+1234.abc",
    "1.2+123456", "1.2.r32+123456", "1.2.rev33+123456",

    # Explicit epoch of 1
    "1!1.0.dev456", "1!1.0a1", "1!1.0a2.dev456", "1!1.0a12.dev456", "1!1.0a12",
    "1!1.0b1.dev456", "1!1.0b2", "1!1.0b2.post345.dev456", "1!1.0b2.post345",
    "1!1.0b2-346", "1!1.0c1.dev456", "1!1.0c1", "1!1.0rc2", "1!1.0c3", "1!1.0",
    "1!1.0.post456.dev34", "1!1.0.post456", "1!1.1.dev1", "1!1.2+123abc",
    "1!1.2+123abc456", "1!1.2+abc", "1!1.2+abc123", "1!1.2+abc123def",
    "1!1.2+1234.abc", "1!1.2+123456", "1!1.2.r32+123456", "1!1.2.rev33+123456",
]


@pytest.mark.parametrize('version', PACKAGING_VERSIONS)
def test_parse_packaging(version):
    assert str(Version.parse(version)) == version


@given(whitespace, version_string(), whitespace)
def test_parse_permissive_hypothesis(prefix, version, suffix):
    Version.parse(prefix + version + suffix)


@given(whitespace, version_string(strict=True), whitespace)
def test_parse_canonical_hypothesis(prefix, version, suffix):
    Version.parse(prefix + version + suffix, strict=True)


@given(version_string())
def test_roundtrip(version):
    assert str(Version.parse(version)) == version
