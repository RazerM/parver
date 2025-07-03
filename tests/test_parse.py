import pytest
from hypothesis import HealthCheck, assume, given, settings

from parver import ParseError, Version

from .strategies import version_string, version_string_from_pep440_regex, whitespace


@given(whitespace, version_string(), whitespace)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_parse_hypothesis(prefix, version, suffix):
    Version.parse(prefix + version + suffix)


@given(whitespace, version_string_from_pep440_regex, whitespace)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_parse_pep440_regex_hypothesis(prefix, version, suffix):
    Version.parse(prefix + version + suffix)


@given(whitespace, version_string(strict=True), whitespace)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_parse_strict_hypothesis(prefix, version, suffix):
    Version.parse(prefix + version + suffix, strict=True)


@given(version_string(strict=False))
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_parse_strict_error(version):
    v = Version.parse(version)

    # Exclude already normalized versions
    assume(str(v.normalize()) != version)

    # 0!1 normalizes to '1'
    assume(v.epoch != 0 or v.epoch_implicit)

    with pytest.raises(ParseError):
        Version.parse(version, strict=True)


@given(version_string_from_pep440_regex)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_parse_pep440_regex_strict_error(version):
    v = Version.parse(version)

    # Exclude already normalized versions
    assume(str(v.normalize()) != version)

    # 0!1 normalizes to '1'
    assume(v.epoch != 0 or v.epoch_implicit)

    with pytest.raises(ParseError):
        Version.parse(version, strict=True)


@given(version_string())
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_roundtrip(version):
    assert str(Version.parse(version)) == version


@given(version_string_from_pep440_regex)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_pep440_regex_roundtrip(version):
    assert str(Version.parse(version)) == version.lower()


@pytest.mark.parametrize(
    "version",
    [
        "1+ABC",
        "1+2-3",
        "1+2_3",
        "1+02_3",
    ],
)
def test_parse_local_strict(version):
    with pytest.raises(ParseError):
        Version.parse(version, strict=True)
    Version.parse(version)
