"""The tests in this file have been adapted from the excellent test suite in
packaging.version. See https://github.com/pypa/packaging

Copyright (c) Donald Stufft and individual contributors.
https://github.com/pypa/packaging/blob/master/LICENSE
"""

import itertools
import operator

import pretend
import pytest

from parver import ParseError, Version

# This list must be in the correct sorting order
VERSIONS = [
    # Implicit epoch of 0
    "1.0.dev456",
    "1.0a1",
    "1.0a2.dev456",
    "1.0a12.dev456",
    "1.0a12",
    "1.0b1.dev456",
    "1.0b2",
    "1.0b2.post345.dev456",
    "1.0b2.post345",
    "1.0b2-346",
    "1.0c1.dev456",
    "1.0c1",
    "1.0rc2",
    "1.0c3",
    "1.0",
    "1.0.post456.dev34",
    "1.0.post456",
    "1.1.dev1",
    "1.2+123abc",
    "1.2+123abc456",
    "1.2+abc",
    "1.2+abc123",
    "1.2+abc123def",
    "1.2+1234.abc",
    "1.2+123456",
    "1.2.r32+123456",
    "1.2.rev33+123456",
    # Explicit epoch of 1
    "1!1.0.dev456",
    "1!1.0a1",
    "1!1.0a2.dev456",
    "1!1.0a12.dev456",
    "1!1.0a12",
    "1!1.0b1.dev456",
    "1!1.0b2",
    "1!1.0b2.post345.dev456",
    "1!1.0b2.post345",
    "1!1.0b2-346",
    "1!1.0c1.dev456",
    "1!1.0c1",
    "1!1.0rc2",
    "1!1.0c3",
    "1!1.0",
    "1!1.0.post456.dev34",
    "1!1.0.post456",
    "1!1.1.dev1",
    "1!1.2+123abc",
    "1!1.2+123abc456",
    "1!1.2+abc",
    "1!1.2+abc123",
    "1!1.2+abc123def",
    "1!1.2+1234.abc",
    "1!1.2+123456",
    "1!1.2.r32+123456",
    "1!1.2.rev33+123456",
]

# Don't want an exception here if VERSIONS cannot be parsed,
# that's what test_valid_versions is for.
try:
    PARSED_VERSIONS = [Version.parse(v) for v in VERSIONS]
except ParseError:  # pragma: no cover
    PARSED_VERSIONS = []


class TestVersion:
    @pytest.mark.parametrize("version", VERSIONS)
    def test_valid_versions(self, version):
        assert str(Version.parse(version)) == version

    @pytest.mark.parametrize(
        "version",
        [
            # Non sensical versions should be invalid
            "french toast",
            # Versions with invalid local versions
            "1.0+a+",
            "1.0++",
            "1.0+_foobar",
            "1.0+foo&asd",
            "1.0+1+1",
        ],
    )
    def test_invalid_versions(self, version):
        with pytest.raises(ParseError):
            Version.parse(version)

    @pytest.mark.parametrize(
        ("version", "normalized"),
        [
            # Various development release incarnations
            ("1.0dev", "1.0.dev0"),
            ("1.0.dev", "1.0.dev0"),
            ("1.0dev1", "1.0.dev1"),
            ("1.0dev", "1.0.dev0"),
            ("1.0-dev", "1.0.dev0"),
            ("1.0-dev1", "1.0.dev1"),
            ("1.0DEV", "1.0.dev0"),
            ("1.0.DEV", "1.0.dev0"),
            ("1.0DEV1", "1.0.dev1"),
            ("1.0DEV", "1.0.dev0"),
            ("1.0.DEV1", "1.0.dev1"),
            ("1.0-DEV", "1.0.dev0"),
            ("1.0-DEV1", "1.0.dev1"),
            # Various alpha incarnations
            ("1.0a", "1.0a0"),
            ("1.0.a", "1.0a0"),
            ("1.0.a1", "1.0a1"),
            ("1.0-a", "1.0a0"),
            ("1.0-a1", "1.0a1"),
            ("1.0alpha", "1.0a0"),
            ("1.0.alpha", "1.0a0"),
            ("1.0.alpha1", "1.0a1"),
            ("1.0-alpha", "1.0a0"),
            ("1.0-alpha1", "1.0a1"),
            ("1.0A", "1.0a0"),
            ("1.0.A", "1.0a0"),
            ("1.0.A1", "1.0a1"),
            ("1.0-A", "1.0a0"),
            ("1.0-A1", "1.0a1"),
            ("1.0ALPHA", "1.0a0"),
            ("1.0.ALPHA", "1.0a0"),
            ("1.0.ALPHA1", "1.0a1"),
            ("1.0-ALPHA", "1.0a0"),
            ("1.0-ALPHA1", "1.0a1"),
            # Various beta incarnations
            ("1.0b", "1.0b0"),
            ("1.0.b", "1.0b0"),
            ("1.0.b1", "1.0b1"),
            ("1.0-b", "1.0b0"),
            ("1.0-b1", "1.0b1"),
            ("1.0beta", "1.0b0"),
            ("1.0.beta", "1.0b0"),
            ("1.0.beta1", "1.0b1"),
            ("1.0-beta", "1.0b0"),
            ("1.0-beta1", "1.0b1"),
            ("1.0B", "1.0b0"),
            ("1.0.B", "1.0b0"),
            ("1.0.B1", "1.0b1"),
            ("1.0-B", "1.0b0"),
            ("1.0-B1", "1.0b1"),
            ("1.0BETA", "1.0b0"),
            ("1.0.BETA", "1.0b0"),
            ("1.0.BETA1", "1.0b1"),
            ("1.0-BETA", "1.0b0"),
            ("1.0-BETA1", "1.0b1"),
            # Various release candidate incarnations
            ("1.0c", "1.0rc0"),
            ("1.0.c", "1.0rc0"),
            ("1.0.c1", "1.0rc1"),
            ("1.0-c", "1.0rc0"),
            ("1.0-c1", "1.0rc1"),
            ("1.0rc", "1.0rc0"),
            ("1.0.rc", "1.0rc0"),
            ("1.0.rc1", "1.0rc1"),
            ("1.0-rc", "1.0rc0"),
            ("1.0-rc1", "1.0rc1"),
            ("1.0C", "1.0rc0"),
            ("1.0.C", "1.0rc0"),
            ("1.0.C1", "1.0rc1"),
            ("1.0-C", "1.0rc0"),
            ("1.0-C1", "1.0rc1"),
            ("1.0RC", "1.0rc0"),
            ("1.0.RC", "1.0rc0"),
            ("1.0.RC1", "1.0rc1"),
            ("1.0-RC", "1.0rc0"),
            ("1.0-RC1", "1.0rc1"),
            # Various post release incarnations
            ("1.0post", "1.0.post0"),
            ("1.0.post", "1.0.post0"),
            ("1.0post1", "1.0.post1"),
            ("1.0post", "1.0.post0"),
            ("1.0-post", "1.0.post0"),
            ("1.0-post1", "1.0.post1"),
            ("1.0POST", "1.0.post0"),
            ("1.0.POST", "1.0.post0"),
            ("1.0POST1", "1.0.post1"),
            ("1.0POST", "1.0.post0"),
            ("1.0r", "1.0.post0"),
            ("1.0rev", "1.0.post0"),
            ("1.0.POST1", "1.0.post1"),
            ("1.0.r1", "1.0.post1"),
            ("1.0.rev1", "1.0.post1"),
            ("1.0-POST", "1.0.post0"),
            ("1.0-POST1", "1.0.post1"),
            ("1.0-5", "1.0.post5"),
            ("1.0-r5", "1.0.post5"),
            ("1.0-rev5", "1.0.post5"),
            # Local version case insensitivity
            ("1.0+AbC", "1.0+abc"),
            # Integer Normalization
            ("1.01", "1.1"),
            ("1.0a05", "1.0a5"),
            ("1.0b07", "1.0b7"),
            ("1.0c056", "1.0rc56"),
            ("1.0rc09", "1.0rc9"),
            ("1.0.post000", "1.0.post0"),
            ("1.1.dev09000", "1.1.dev9000"),
            ("00!1.2", "1.2"),
            ("0100!0.0", "100!0.0"),
            # Various other normalizations
            ("v1.0", "1.0"),
            ("   v1.0\t\n", "1.0"),
        ],
    )
    def test_normalized_versions(self, version, normalized):
        assert str(Version.parse(version).normalize()) == normalized

    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("1.0.dev456", "1.0.dev456"),
            ("1.0a1", "1.0a1"),
            ("1.0a2.dev456", "1.0a2.dev456"),
            ("1.0a12.dev456", "1.0a12.dev456"),
            ("1.0a12", "1.0a12"),
            ("1.0b1.dev456", "1.0b1.dev456"),
            ("1.0b2", "1.0b2"),
            ("1.0b2.post345.dev456", "1.0b2.post345.dev456"),
            ("1.0b2.post345", "1.0b2.post345"),
            ("1.0rc1.dev456", "1.0rc1.dev456"),
            ("1.0rc1", "1.0rc1"),
            ("1.0", "1.0"),
            ("1.0.post456.dev34", "1.0.post456.dev34"),
            ("1.0.post456", "1.0.post456"),
            ("1.0.1", "1.0.1"),
            ("0!1.0.2", "1.0.2"),
            ("1.0.3+7", "1.0.3+7"),
            ("0!1.0.4+8.0", "1.0.4+8.0"),
            ("1.0.5+9.5", "1.0.5+9.5"),
            ("1.2+1234.abc", "1.2+1234.abc"),
            ("1.2+123456", "1.2+123456"),
            ("1.2+123abc", "1.2+123abc"),
            ("1.2+123abc456", "1.2+123abc456"),
            ("1.2+abc", "1.2+abc"),
            ("1.2+abc123", "1.2+abc123"),
            ("1.2+abc123def", "1.2+abc123def"),
            ("1.1.dev1", "1.1.dev1"),
            ("7!1.0.dev456", "7!1.0.dev456"),
            ("7!1.0a1", "7!1.0a1"),
            ("7!1.0a2.dev456", "7!1.0a2.dev456"),
            ("7!1.0a12.dev456", "7!1.0a12.dev456"),
            ("7!1.0a12", "7!1.0a12"),
            ("7!1.0b1.dev456", "7!1.0b1.dev456"),
            ("7!1.0b2", "7!1.0b2"),
            ("7!1.0b2.post345.dev456", "7!1.0b2.post345.dev456"),
            ("7!1.0b2.post345", "7!1.0b2.post345"),
            ("7!1.0rc1.dev456", "7!1.0rc1.dev456"),
            ("7!1.0rc1", "7!1.0rc1"),
            ("7!1.0", "7!1.0"),
            ("7!1.0.post456.dev34", "7!1.0.post456.dev34"),
            ("7!1.0.post456", "7!1.0.post456"),
            ("7!1.0.1", "7!1.0.1"),
            ("7!1.0.2", "7!1.0.2"),
            ("7!1.0.3+7", "7!1.0.3+7"),
            ("7!1.0.4+8.0", "7!1.0.4+8.0"),
            ("7!1.0.5+9.5", "7!1.0.5+9.5"),
            ("7!1.1.dev1", "7!1.1.dev1"),
            ("1+2_3-Four", "1+2.3.four"),
        ],
    )
    def test_version_str_repr(self, version, expected):
        v = Version.parse(version).normalize()
        assert str(v) == expected
        assert repr(v) == f"<Version {expected!r}>"

    def test_version_rc_and_c_equals(self):
        assert Version.parse("1.0rc1") == Version.parse("1.0c1")

    @pytest.mark.parametrize("version", PARSED_VERSIONS)
    def test_version_hash(self, version):
        assert hash(version) == hash(version)

    @pytest.mark.parametrize(
        ("version", "public"),
        [
            ("1.0", "1.0"),
            ("1.0.dev0", "1.0.dev0"),
            ("1.0.dev6", "1.0.dev6"),
            ("1.0a1", "1.0a1"),
            ("1.0a1.post5", "1.0a1.post5"),
            ("1.0a1.post5.dev6", "1.0a1.post5.dev6"),
            ("1.0rc4", "1.0rc4"),
            ("1.0.post5", "1.0.post5"),
            ("1!1.0", "1!1.0"),
            ("1!1.0.dev6", "1!1.0.dev6"),
            ("1!1.0a1", "1!1.0a1"),
            ("1!1.0a1.post5", "1!1.0a1.post5"),
            ("1!1.0a1.post5.dev6", "1!1.0a1.post5.dev6"),
            ("1!1.0rc4", "1!1.0rc4"),
            ("1!1.0.post5", "1!1.0.post5"),
            ("1.0+deadbeef", "1.0"),
            ("1.0.dev6+deadbeef", "1.0.dev6"),
            ("1.0a1+deadbeef", "1.0a1"),
            ("1.0a1.post5+deadbeef", "1.0a1.post5"),
            ("1.0a1.post5.dev6+deadbeef", "1.0a1.post5.dev6"),
            ("1.0rc4+deadbeef", "1.0rc4"),
            ("1.0.post5+deadbeef", "1.0.post5"),
            ("1!1.0+deadbeef", "1!1.0"),
            ("1!1.0.dev6+deadbeef", "1!1.0.dev6"),
            ("1!1.0a1+deadbeef", "1!1.0a1"),
            ("1!1.0a1.post5+deadbeef", "1!1.0a1.post5"),
            ("1!1.0a1.post5.dev6+deadbeef", "1!1.0a1.post5.dev6"),
            ("1!1.0rc4+deadbeef", "1!1.0rc4"),
            ("1!1.0.post5+deadbeef", "1!1.0.post5"),
        ],
    )
    def test_version_public(self, version, public):
        assert Version.parse(version).public == public

    @pytest.mark.parametrize(
        ("version", "base_version"),
        [
            ("1.0", "1.0"),
            ("1.0.dev0", "1.0"),
            ("1.0.dev6", "1.0"),
            ("1.0a1", "1.0"),
            ("1.0a1.post5", "1.0"),
            ("1.0a1.post5.dev6", "1.0"),
            ("1.0rc4", "1.0"),
            ("1.0.post5", "1.0"),
            ("1!1.0", "1!1.0"),
            ("1!1.0.dev6", "1!1.0"),
            ("1!1.0a1", "1!1.0"),
            ("1!1.0a1.post5", "1!1.0"),
            ("1!1.0a1.post5.dev6", "1!1.0"),
            ("1!1.0rc4", "1!1.0"),
            ("1!1.0.post5", "1!1.0"),
            ("1.0+deadbeef", "1.0"),
            ("1.0.dev6+deadbeef", "1.0"),
            ("1.0a1+deadbeef", "1.0"),
            ("1.0a1.post5+deadbeef", "1.0"),
            ("1.0a1.post5.dev6+deadbeef", "1.0"),
            ("1.0rc4+deadbeef", "1.0"),
            ("1.0.post5+deadbeef", "1.0"),
            ("1!1.0+deadbeef", "1!1.0"),
            ("1!1.0.dev6+deadbeef", "1!1.0"),
            ("1!1.0a1+deadbeef", "1!1.0"),
            ("1!1.0a1.post5+deadbeef", "1!1.0"),
            ("1!1.0a1.post5.dev6+deadbeef", "1!1.0"),
            ("1!1.0rc4+deadbeef", "1!1.0"),
            ("1!1.0.post5+deadbeef", "1!1.0"),
        ],
    )
    def test_version_base_version(self, version, base_version):
        assert str(Version.parse(version).base_version()) == base_version

    @pytest.mark.parametrize(
        ("version", "epoch"),
        [
            ("1.0", 0),
            ("1.0.dev0", 0),
            ("1.0.dev6", 0),
            ("1.0a1", 0),
            ("1.0a1.post5", 0),
            ("1.0a1.post5.dev6", 0),
            ("1.0rc4", 0),
            ("1.0.post5", 0),
            ("1!1.0", 1),
            ("1!1.0.dev6", 1),
            ("1!1.0a1", 1),
            ("1!1.0a1.post5", 1),
            ("1!1.0a1.post5.dev6", 1),
            ("1!1.0rc4", 1),
            ("1!1.0.post5", 1),
            ("1.0+deadbeef", 0),
            ("1.0.dev6+deadbeef", 0),
            ("1.0a1+deadbeef", 0),
            ("1.0a1.post5+deadbeef", 0),
            ("1.0a1.post5.dev6+deadbeef", 0),
            ("1.0rc4+deadbeef", 0),
            ("1.0.post5+deadbeef", 0),
            ("1!1.0+deadbeef", 1),
            ("1!1.0.dev6+deadbeef", 1),
            ("1!1.0a1+deadbeef", 1),
            ("1!1.0a1.post5+deadbeef", 1),
            ("1!1.0a1.post5.dev6+deadbeef", 1),
            ("1!1.0rc4+deadbeef", 1),
            ("1!1.0.post5+deadbeef", 1),
        ],
    )
    def test_version_epoch(self, version, epoch):
        assert Version.parse(version).epoch == epoch

    @pytest.mark.parametrize(
        ("version", "release"),
        [
            ("1.0", (1, 0)),
            ("1.0.dev0", (1, 0)),
            ("1.0.dev6", (1, 0)),
            ("1.0a1", (1, 0)),
            ("1.0a1.post5", (1, 0)),
            ("1.0a1.post5.dev6", (1, 0)),
            ("1.0rc4", (1, 0)),
            ("1.0.post5", (1, 0)),
            ("1!1.0", (1, 0)),
            ("1!1.0.dev6", (1, 0)),
            ("1!1.0a1", (1, 0)),
            ("1!1.0a1.post5", (1, 0)),
            ("1!1.0a1.post5.dev6", (1, 0)),
            ("1!1.0rc4", (1, 0)),
            ("1!1.0.post5", (1, 0)),
            ("1.0+deadbeef", (1, 0)),
            ("1.0.dev6+deadbeef", (1, 0)),
            ("1.0a1+deadbeef", (1, 0)),
            ("1.0a1.post5+deadbeef", (1, 0)),
            ("1.0a1.post5.dev6+deadbeef", (1, 0)),
            ("1.0rc4+deadbeef", (1, 0)),
            ("1.0.post5+deadbeef", (1, 0)),
            ("1!1.0+deadbeef", (1, 0)),
            ("1!1.0.dev6+deadbeef", (1, 0)),
            ("1!1.0a1+deadbeef", (1, 0)),
            ("1!1.0a1.post5+deadbeef", (1, 0)),
            ("1!1.0a1.post5.dev6+deadbeef", (1, 0)),
            ("1!1.0rc4+deadbeef", (1, 0)),
            ("1!1.0.post5+deadbeef", (1, 0)),
        ],
    )
    def test_version_release(self, version, release):
        assert Version.parse(version).release == release

    @pytest.mark.parametrize(
        ("version", "local"),
        [
            ("1.0", None),
            ("1.0.dev0", None),
            ("1.0.dev6", None),
            ("1.0a1", None),
            ("1.0a1.post5", None),
            ("1.0a1.post5.dev6", None),
            ("1.0rc4", None),
            ("1.0.post5", None),
            ("1!1.0", None),
            ("1!1.0.dev6", None),
            ("1!1.0a1", None),
            ("1!1.0a1.post5", None),
            ("1!1.0a1.post5.dev6", None),
            ("1!1.0rc4", None),
            ("1!1.0.post5", None),
            ("1.0+deadbeef", "deadbeef"),
            ("1.0.dev6+deadbeef", "deadbeef"),
            ("1.0a1+deadbeef", "deadbeef"),
            ("1.0a1.post5+deadbeef", "deadbeef"),
            ("1.0a1.post5.dev6+deadbeef", "deadbeef"),
            ("1.0rc4+deadbeef", "deadbeef"),
            ("1.0.post5+deadbeef", "deadbeef"),
            ("1!1.0+deadbeef", "deadbeef"),
            ("1!1.0.dev6+deadbeef", "deadbeef"),
            ("1!1.0a1+deadbeef", "deadbeef"),
            ("1!1.0a1.post5+deadbeef", "deadbeef"),
            ("1!1.0a1.post5.dev6+deadbeef", "deadbeef"),
            ("1!1.0rc4+deadbeef", "deadbeef"),
            ("1!1.0.post5+deadbeef", "deadbeef"),
        ],
    )
    def test_version_local(self, version, local):
        assert Version.parse(version).local == local

    @pytest.mark.parametrize(
        ("version", "pre"),
        [
            ("1.0", None),
            ("1.0.dev0", None),
            ("1.0.dev6", None),
            ("1.0a1", ("a", 1)),
            ("1.0a1.post5", ("a", 1)),
            ("1.0a1.post5.dev6", ("a", 1)),
            ("1.0rc4", ("rc", 4)),
            ("1.0.post5", None),
            ("1!1.0", None),
            ("1!1.0.dev6", None),
            ("1!1.0a1", ("a", 1)),
            ("1!1.0a1.post5", ("a", 1)),
            ("1!1.0a1.post5.dev6", ("a", 1)),
            ("1!1.0rc4", ("rc", 4)),
            ("1!1.0.post5", None),
            ("1.0+deadbeef", None),
            ("1.0.dev6+deadbeef", None),
            ("1.0a1+deadbeef", ("a", 1)),
            ("1.0a1.post5+deadbeef", ("a", 1)),
            ("1.0a1.post5.dev6+deadbeef", ("a", 1)),
            ("1.0rc4+deadbeef", ("rc", 4)),
            ("1.0.post5+deadbeef", None),
            ("1!1.0+deadbeef", None),
            ("1!1.0.dev6+deadbeef", None),
            ("1!1.0a1+deadbeef", ("a", 1)),
            ("1!1.0a1.post5+deadbeef", ("a", 1)),
            ("1!1.0a1.post5.dev6+deadbeef", ("a", 1)),
            ("1!1.0rc4+deadbeef", ("rc", 4)),
            ("1!1.0.post5+deadbeef", None),
        ],
    )
    def test_version_pre(self, version, pre):
        v = Version.parse(version)
        if pre is None:
            assert v.pre is None and v.pre_tag is None
            return
        assert v.pre == pre[1]
        assert v.pre_tag == pre[0]

    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("1.0.dev0", True),
            ("1.0.dev1", True),
            ("1.0a1.dev1", True),
            ("1.0b1.dev1", True),
            ("1.0c1.dev1", True),
            ("1.0rc1.dev1", True),
            ("1.0a1", True),
            ("1.0b1", True),
            ("1.0c1", True),
            ("1.0rc1", True),
            ("1.0a1.post1.dev1", True),
            ("1.0b1.post1.dev1", True),
            ("1.0c1.post1.dev1", True),
            ("1.0rc1.post1.dev1", True),
            ("1.0a1.post1", True),
            ("1.0b1.post1", True),
            ("1.0c1.post1", True),
            ("1.0rc1.post1", True),
            ("1.0", False),
            ("1.0+dev", False),
            ("1.0.post1", False),
            ("1.0.post1+dev", False),
        ],
    )
    def test_version_is_prerelease(self, version, expected):
        assert Version.parse(version).is_prerelease is expected

    @pytest.mark.parametrize(
        ("version", "dev"),
        [
            ("1.0", None),
            ("1.0.dev0", 0),
            ("1.0.dev6", 6),
            ("1.0a1", None),
            ("1.0a1.post5", None),
            ("1.0a1.post5.dev6", 6),
            ("1.0rc4", None),
            ("1.0.post5", None),
            ("1!1.0", None),
            ("1!1.0.dev6", 6),
            ("1!1.0a1", None),
            ("1!1.0a1.post5", None),
            ("1!1.0a1.post5.dev6", 6),
            ("1!1.0rc4", None),
            ("1!1.0.post5", None),
            ("1.0+deadbeef", None),
            ("1.0.dev6+deadbeef", 6),
            ("1.0a1+deadbeef", None),
            ("1.0a1.post5+deadbeef", None),
            ("1.0a1.post5.dev6+deadbeef", 6),
            ("1.0rc4+deadbeef", None),
            ("1.0.post5+deadbeef", None),
            ("1!1.0+deadbeef", None),
            ("1!1.0.dev6+deadbeef", 6),
            ("1!1.0a1+deadbeef", None),
            ("1!1.0a1.post5+deadbeef", None),
            ("1!1.0a1.post5.dev6+deadbeef", 6),
            ("1!1.0rc4+deadbeef", None),
            ("1!1.0.post5+deadbeef", None),
        ],
    )
    def test_version_dev(self, version, dev):
        assert Version.parse(version).dev == dev

    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("1.0", False),
            ("1.0.dev0", True),
            ("1.0.dev6", True),
            ("1.0a1", False),
            ("1.0a1.post5", False),
            ("1.0a1.post5.dev6", True),
            ("1.0rc4", False),
            ("1.0.post5", False),
            ("1!1.0", False),
            ("1!1.0.dev6", True),
            ("1!1.0a1", False),
            ("1!1.0a1.post5", False),
            ("1!1.0a1.post5.dev6", True),
            ("1!1.0rc4", False),
            ("1!1.0.post5", False),
            ("1.0+deadbeef", False),
            ("1.0.dev6+deadbeef", True),
            ("1.0a1+deadbeef", False),
            ("1.0a1.post5+deadbeef", False),
            ("1.0a1.post5.dev6+deadbeef", True),
            ("1.0rc4+deadbeef", False),
            ("1.0.post5+deadbeef", False),
            ("1!1.0+deadbeef", False),
            ("1!1.0.dev6+deadbeef", True),
            ("1!1.0a1+deadbeef", False),
            ("1!1.0a1.post5+deadbeef", False),
            ("1!1.0a1.post5.dev6+deadbeef", True),
            ("1!1.0rc4+deadbeef", False),
            ("1!1.0.post5+deadbeef", False),
        ],
    )
    def test_version_is_devrelease(self, version, expected):
        assert Version.parse(version).is_devrelease is expected

    @pytest.mark.parametrize(
        ("version", "post"),
        [
            ("1.0", None),
            ("1.0.dev0", None),
            ("1.0.dev6", None),
            ("1.0a1", None),
            ("1.0a1.post5", 5),
            ("1.0a1.post5.dev6", 5),
            ("1.0rc4", None),
            ("1.0.post5", 5),
            ("1!1.0", None),
            ("1!1.0.dev6", None),
            ("1!1.0a1", None),
            ("1!1.0a1.post5", 5),
            ("1!1.0a1.post5.dev6", 5),
            ("1!1.0rc4", None),
            ("1!1.0.post5", 5),
            ("1.0+deadbeef", None),
            ("1.0.dev6+deadbeef", None),
            ("1.0a1+deadbeef", None),
            ("1.0a1.post5+deadbeef", 5),
            ("1.0a1.post5.dev6+deadbeef", 5),
            ("1.0rc4+deadbeef", None),
            ("1.0.post5+deadbeef", 5),
            ("1!1.0+deadbeef", None),
            ("1!1.0.dev6+deadbeef", None),
            ("1!1.0a1+deadbeef", None),
            ("1!1.0a1.post5+deadbeef", 5),
            ("1!1.0a1.post5.dev6+deadbeef", 5),
            ("1!1.0rc4+deadbeef", None),
            ("1!1.0.post5+deadbeef", 5),
        ],
    )
    def test_version_post(self, version, post):
        assert Version.parse(version).post == post

    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("1.0.dev1", False),
            ("1.0", False),
            ("1.0+foo", False),
            ("1.0.post1.dev1", True),
            ("1.0.post1", True),
        ],
    )
    def test_version_is_postrelease(self, version, expected):
        assert Version.parse(version).is_postrelease is expected

    @pytest.mark.parametrize(
        ("left", "right", "op"),
        # Below we'll generate every possible combination of VERSIONS that
        # should be True for the given operator
        itertools.chain(
            # Verify that the less than (<) operator works correctly
            *[
                [(x, y, operator.lt) for y in PARSED_VERSIONS[i + 1 :]]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
            +
            # Verify that the less than equal (<=) operator works correctly
            [
                [(x, y, operator.le) for y in PARSED_VERSIONS[i:]]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
            +
            # Verify that the equal (==) operator works correctly
            [[(x, x, operator.eq) for x in PARSED_VERSIONS]]
            +
            # Verify that the not equal (!=) operator works correctly
            [
                [(x, y, operator.ne) for j, y in enumerate(PARSED_VERSIONS) if i != j]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
            +
            # Verify that the greater than equal (>=) operator works correctly
            [
                [(x, y, operator.ge) for y in PARSED_VERSIONS[: i + 1]]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
            +
            # Verify that the greater than (>) operator works correctly
            [
                [(x, y, operator.gt) for y in PARSED_VERSIONS[:i]]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
        ),
    )
    def test_comparison_true(self, left, right, op):
        assert op(left, right)

    @pytest.mark.parametrize(
        ("left", "right", "op"),
        # Below we'll generate every possible combination of VERSIONS that
        # should be False for the given operator
        itertools.chain(
            # Verify that the less than (<) operator works correctly
            *[
                [(x, y, operator.lt) for y in PARSED_VERSIONS[: i + 1]]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
            +
            # Verify that the less than equal (<=) operator works correctly
            [
                [(x, y, operator.le) for y in PARSED_VERSIONS[:i]]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
            +
            # Verify that the equal (==) operator works correctly
            [
                [(x, y, operator.eq) for j, y in enumerate(PARSED_VERSIONS) if i != j]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
            +
            # Verify that the not equal (!=) operator works correctly
            [[(x, x, operator.ne) for x in PARSED_VERSIONS]]
            +
            # Verify that the greater than equal (>=) operator works correctly
            [
                [(x, y, operator.ge) for y in PARSED_VERSIONS[i + 1 :]]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
            +
            # Verify that the greater than (>) operator works correctly
            [
                [(x, y, operator.gt) for y in PARSED_VERSIONS[i:]]
                for i, x in enumerate(PARSED_VERSIONS)
            ]
        ),
    )
    def test_comparison_false(self, left, right, op):
        assert not op(left, right)

    @pytest.mark.parametrize(("op", "expected"), [("eq", False), ("ne", True)])
    def test_compare_other(self, op, expected):
        other = pretend.stub(**{f"__{op}__": lambda other: NotImplemented})

        assert getattr(operator, op)(Version.parse("1"), other) is expected
