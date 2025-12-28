import pickle

import pytest
from hypothesis import HealthCheck, assume, given, settings

from parver import ParseError, Version
from parver._version import (
    ImplicitNumberError,
    InvalidLocalError,
    LeadingZerosError,
    LocalEmptyError,
    NoLeadingNumberError,
    Parser,
    StrictPreTagError,
    StrictSegmentError,
    TrailingDataError,
    UnexpectedInputError,
    VPrefixNotAllowedError,
    _nicepath,
    _normalize_pre_tag,
    _parse_local_version_normalized,
    _ParseDiagnostics,
    is_strict_local_alpha,
    is_strict_number,
)

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
    # The new parser preserves case, so we compare case-insensitively
    assert str(Version.parse(version)).lower() == version.lower()


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


@pytest.mark.parametrize(
    ("pre_tag", "expected"),
    [
        (None, None),
        ("alpha", "a"),
        ("beta", "b"),
        ("pre", "rc"),
        ("preview", "rc"),
        ("c", "rc"),
        ("a", "a"),
        ("b", "b"),
        ("rc", "rc"),
        ("candidate", "candidate"),
    ],
)
def test_normalize_pre_tag(pre_tag, expected):
    assert _normalize_pre_tag(pre_tag) == expected


@pytest.mark.parametrize(
    ("local", "expected"),
    [
        ("ABC.1-twelve", ("abc", 1, "twelve")),
        (None, None),
    ],
)
def test_parse_local_version_normalized(local, expected):
    assert _parse_local_version_normalized(local) == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("release", "release"),
        (("release", 0, "post"), "release[0].post"),
    ],
)
def test_nicepath(path, expected):
    assert _nicepath(path) == expected


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        ("", False),
        ("0", True),
        ("01", False),
        ("12", True),
    ],
)
def test_is_strict_number(number, expected):
    assert is_strict_number(number) is expected


@pytest.mark.parametrize(
    ("local", "expected"),
    [
        ("", False),
        ("abc", True),
        ("123abc", True),
        ("123", False),
        ("abc!", False),
        ("abcé", False),
    ],
)
def test_is_strict_local_alpha(local, expected):
    assert is_strict_local_alpha(local) is expected


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (NoLeadingNumberError(), "Expected a release number"),
        (
            TrailingDataError(version="1", remaining="x"),
            "Expected end of version at position 1, found 'x'",
        ),
        (
            UnexpectedInputError(
                version="1.",
                index=2,
                expected=("a release number",),
            ),
            "Expected a release number at position 2, found end of input",
        ),
        (
            UnexpectedInputError(
                version="1.",
                index=2,
                expected=("a release number", "'dev'"),
            ),
            "Expected a release number or 'dev' at position 2, found end of input",
        ),
        (
            LocalEmptyError(precursor="+"),
            "Expected a local version segment after '+'",
        ),
        (
            VPrefixNotAllowedError(),
            "The 'v' prefix is not allowed in strict mode",
        ),
        (
            LeadingZerosError("01"),
            "Leading zeros in numbers are not allowed in strict mode: '01'; "
            "use '1' in strict mode",
        ),
        (
            LeadingZerosError("01", "release"),
            "Leading zeros in release numbers are not allowed in strict mode: "
            "'01'; use '1' in strict mode",
        ),
        (
            ImplicitNumberError(),
            "Explicit number required for segment in strict mode",
        ),
        (
            ImplicitNumberError("post-release"),
            "Explicit number required for post-release in strict mode",
        ),
        (
            InvalidLocalError("ABC"),
            "Invalid local version in strict mode: 'ABC'",
        ),
        (
            InvalidLocalError("ABC", "must be lowercase"),
            "Invalid local version in strict mode: must be lowercase: 'ABC'",
        ),
        (
            InvalidLocalError(
                "ABC",
                "must be lowercase alphanumeric",
                replacement="abc",
            ),
            "Local version segment 'ABC' is not allowed in strict mode: "
            "must be lowercase alphanumeric; use 'abc' in strict mode",
        ),
    ],
)
def test_parse_error_messages(error, message):
    assert str(error) == message


@pytest.mark.parametrize(
    ("version", "strict", "error_type", "message"),
    [
        (
            "abc",
            False,
            NoLeadingNumberError,
            "Expected a release number at position 0, found 'a'",
        ),
        (
            "1!",
            False,
            NoLeadingNumberError,
            "Expected a release number at position 2, found end of input",
        ),
        (
            "1.",
            False,
            UnexpectedInputError,
            "Expected a release number, a pre-release tag, a post-release tag, "
            "or 'dev' at position 2, found end of input",
        ),
        (
            "1..2",
            False,
            UnexpectedInputError,
            "Expected a release number, a pre-release tag, a post-release tag, "
            "or 'dev' at position 2, found '.'",
        ),
        (
            "1.2.rev1",
            True,
            StrictSegmentError,
            "Post-release tag 'rev' is not allowed in strict mode "
            "at position 4; use 'post' in strict mode",
        ),
        (
            "1+abc-1",
            True,
            StrictSegmentError,
            "Local version separator '-' is not allowed in strict mode "
            "at position 5; use '.' in strict mode",
        ),
        (
            "1.2-a1",
            True,
            StrictSegmentError,
            "Separator '-' before pre-release tag 'a' is not allowed "
            "in strict mode at position 3; omit the separator "
            "in strict mode",
        ),
        (
            "1.2.a1",
            True,
            StrictSegmentError,
            "Separator '.' before pre-release tag 'a' is not allowed "
            "in strict mode at position 3; omit the separator "
            "in strict mode",
        ),
        (
            "1.2-post1",
            True,
            StrictSegmentError,
            "Separator '-' before post-release tag 'post' is not allowed "
            "in strict mode at position 3; use '.' in strict mode",
        ),
        (
            "1.2-dev1",
            True,
            StrictSegmentError,
            "Separator '-' before development release tag 'dev' is not allowed "
            "in strict mode at position 3; use '.' in strict mode",
        ),
        (
            "1.2-1",
            True,
            StrictSegmentError,
            "Implicit post-release shorthand '-1' is not allowed "
            "in strict mode at position 3; use '.post1' in strict mode",
        ),
        (
            "v1",
            True,
            VPrefixNotAllowedError,
            "The 'v' prefix is not allowed in strict mode",
        ),
        (
            "01",
            True,
            LeadingZerosError,
            "Leading zeros in release numbers are not allowed in strict mode: "
            "'01'; use '1' in strict mode",
        ),
        (
            "1+ABC",
            True,
            InvalidLocalError,
            "Local version segment 'ABC' is not allowed in strict mode: "
            "must be lowercase alphanumeric; use 'abc' in strict mode",
        ),
        (
            "1+02",
            True,
            InvalidLocalError,
            "Local version segment '02' is not allowed in strict mode: "
            "leading zeros; use '2' in strict mode",
        ),
        (
            "1.2a.1",
            True,
            StrictSegmentError,
            "Separator '.' before the pre-release number is not allowed "
            "in strict mode at position 4; omit the separator "
            "in strict mode",
        ),
        (
            "1.2.post.1",
            True,
            StrictSegmentError,
            "Separator '.' before the post-release number is not allowed "
            "in strict mode at position 8; omit the separator "
            "in strict mode",
        ),
        (
            "1.2.dev.1",
            True,
            StrictSegmentError,
            "Separator '.' before the development release number is not allowed "
            "in strict mode at position 7; omit the separator "
            "in strict mode",
        ),
        (
            "1.2.dev.x",
            True,
            ImplicitNumberError,
            "Implicit development release numbers are not allowed in strict mode "
            "at position 7; use '0' in strict mode (found '.')",
        ),
        (
            "1.2.DEV1",
            True,
            StrictSegmentError,
            "Development release tag 'DEV' is not allowed in strict mode "
            "at position 4; use 'dev' in strict mode",
        ),
        (
            "1.2pre1",
            True,
            StrictPreTagError,
            "Pre-release tag 'pre' is not allowed in strict mode "
            "at position 3; use 'rc' in strict mode",
        ),
        (
            "1.2.pre1",
            True,
            StrictSegmentError,
            "Separator '.' before pre-release tag 'pre' is not allowed "
            "in strict mode at position 3; omit the separator and "
            "use 'rc' in strict mode",
        ),
        (
            "1.2alpha1",
            True,
            StrictPreTagError,
            "Pre-release tag 'alpha' is not allowed in strict mode "
            "at position 3; use 'a' in strict mode",
        ),
        (
            "1.2a",
            True,
            ImplicitNumberError,
            "Implicit pre-release numbers are not allowed in strict mode "
            "at position 4; use '0' in strict mode (found end of input)",
        ),
        (
            "1.2.postx",
            True,
            ImplicitNumberError,
            "Implicit post-release numbers are not allowed in strict mode "
            "at position 8; use '0' in strict mode (found 'x')",
        ),
        (
            "1.2post1",
            True,
            StrictSegmentError,
            "Post-release tag 'post' without a leading '.' is not allowed "
            "in strict mode at position 3; use '.post' in strict mode",
        ),
        (
            "1.2dev1",
            True,
            StrictSegmentError,
            "Development release tag 'dev' without a leading '.' is not allowed "
            "in strict mode at position 3; use '.dev' in strict mode",
        ),
    ],
)
def test_parse_failure_messages(version, strict, error_type, message):
    with pytest.raises(error_type) as excinfo:
        Version.parse(version, strict=strict)

    assert str(excinfo.value) == message


@pytest.mark.parametrize(
    "error",
    [
        TrailingDataError(version="1", remaining="x"),
        UnexpectedInputError(
            version="1.",
            index=2,
            expected=("a release number",),
        ),
        StrictPreTagError(
            version="1.2pre1",
            index=3,
            tag="pre",
        ),
        ImplicitNumberError(
            "pre-release",
            version="1.2a",
            index=4,
        ),
        NoLeadingNumberError(version="abc", index=0),
        InvalidLocalError("ABC", "must be lowercase", replacement="abc"),
        LocalEmptyError(precursor="+"),
    ],
)
def test_parse_errors_roundtrip_with_pickle(error):
    reloaded = pickle.loads(pickle.dumps(error))
    assert type(reloaded) is type(error)
    assert reloaded.__dict__ == error.__dict__


# Additional tests for case preservation and strict mode


@pytest.mark.parametrize(
    "version,expected",
    [
        ("1", "1"),
        ("1.2", "1.2"),
        ("1.2.3", "1.2.3"),
        ("1.0.0.0", "1.0.0.0"),
        ("v1.2", "v1.2"),
        ("V1.2", "V1.2"),
        ("1!2.3", "1!2.3"),
        ("1.2a1", "1.2a1"),
        ("1.2.alpha1", "1.2.alpha1"),
        ("1.2-beta-2", "1.2-beta-2"),
        ("1.2_rc_3", "1.2_rc_3"),
        ("1.2.post1", "1.2.post1"),
        ("1.2-1", "1.2-1"),
        ("1.2.rev1", "1.2.rev1"),
        ("1.2.r1", "1.2.r1"),
        ("1.2.dev1", "1.2.dev1"),
        ("1.2.DEV1", "1.2.DEV1"),
        ("1.2+local", "1.2+local"),
        ("1.2+local.1.2", "1.2+local.1.2"),
        ("1.2a1.post2.dev3+local", "1.2a1.post2.dev3+local"),
    ],
)
def test_case_preserving_roundtrip(version, expected):
    """Test that version strings with various cases roundtrip correctly."""
    v = Version.parse(version)
    assert str(v) == expected


# Strict mode tests


@given(whitespace, version_string(strict=True), whitespace)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_strict_mode_hypothesis(prefix, version, suffix):
    """Test strict mode with hypothesis-generated valid versions."""
    v = Version.parse(prefix + version + suffix, strict=True)
    assert str(v) == version


@pytest.mark.parametrize(
    "version",
    [
        # Valid strict versions
        "1",
        "1.2",
        "1.2.3",
        "1!2.3",
        "1.2a1",
        "1.2b2",
        "1.2rc3",
        "1.2.post1",
        "1.2.dev1",
        "1.2a1.post2.dev3",
        "1.2+local",
        "1.2+abc.123",
        "1.2+1abc",
    ],
)
def test_strict_mode_valid(version):
    """Test that valid strict versions parse correctly."""
    v = Version.parse(version, strict=True)
    assert str(v) == version


@pytest.mark.parametrize(
    "version,error_type",
    [
        # v prefix not allowed
        ("v1.2", VPrefixNotAllowedError),
        ("V1.2", VPrefixNotAllowedError),
        # Leading zeros not allowed
        ("01.2", LeadingZerosError),
        ("1.02", LeadingZerosError),
        ("1.2a01", LeadingZerosError),
        ("1.2.post01", LeadingZerosError),
        ("1.2.dev01", LeadingZerosError),
        # Non-dot separators not allowed
        ("1.2-a1", TrailingDataError),
        ("1.2_a1", TrailingDataError),
        # Non-strict pre-tags are not allowed in strict mode.
        ("1.2alpha1", StrictPreTagError),
        ("1.2beta1", StrictPreTagError),
        ("1.2pre1", TrailingDataError),
        ("1.2preview1", TrailingDataError),
        ("1.2c1", TrailingDataError),
        ("1!", NoLeadingNumberError),
        # Invalid post-tags
        ("1.2.rev1", TrailingDataError),
        ("1.2.r1", TrailingDataError),
        ("1.2-1", TrailingDataError),
        # Implicit numbers not allowed
        ("1.2a", ImplicitNumberError),
        ("1.2.post", ImplicitNumberError),
        ("1.2.dev", ImplicitNumberError),
        # Local with invalid separator
        ("1+abc-123", TrailingDataError),
        ("1+abc_123", TrailingDataError),
        # Local with uppercase
        ("1+ABC", InvalidLocalError),
        ("1+Abc", InvalidLocalError),
        # Local with leading zeros
        ("1+02", InvalidLocalError),
    ],
)
def test_strict_mode_invalid(version, error_type):
    """Test that invalid strict versions raise the expected errors."""
    with pytest.raises(error_type):
        Version.parse(version, strict=True)


def test_parse_diagnostics_accepts_string_and_combines_expected_at_same_index():
    diagnostics = _ParseDiagnostics()

    diagnostics.expect(1, "a release number")
    diagnostics.expect(1, ("a pre-release tag", "a release number"))
    diagnostics.expect(0, "ignored")

    error = diagnostics.error("1.")
    assert error is not None
    assert error.index == 1
    assert error.expected == ("a release number", "a pre-release tag")


def test_strict_expected_after_release_separator_omits_pre_release_tag():
    parser = Parser("1.", strict=True)

    assert parser.expected_after_release_separator() == (
        "a release number",
        "a post-release tag",
        "'dev'",
    )


def test_non_strict_pre_tag_helpers_return_none_when_not_strict():
    parser = Parser("1a1")
    parser.cursor.index = 1

    assert parser.non_strict_pre_tag_at_cursor() is None
    assert parser.non_strict_pre_tag_at_index(1) is None


def test_non_strict_error_helpers_return_none_when_not_strict():
    parser = Parser("1-dev1")

    assert (
        parser.non_strict_number_separator_error_at_index(
            index=2,
            context="development release",
        )
        is None
    )
    assert parser.non_strict_implicit_post_error_at_index(index=1) is None
    assert (
        parser.non_strict_tag_error_at_index(
            index=2,
            kind="development release",
            tags=("dev",),
            strict_tags=("dev",),
            canonical_tag="dev",
        )
        is None
    )
    assert parser.non_strict_missing_separator_error_at_index(index=1) is None


def test_strict_non_strict_segment_error_falls_through_to_none():
    parser = Parser("1-z1", strict=True)
    parser.cursor.index = 1

    assert (
        parser.non_strict_segment_error_at_cursor(
            after_release_separator=False,
        )
        is None
    )


def test_strict_separator_error_returns_none_for_unknown_tag():
    parser = Parser("1-z1", strict=True)

    assert (
        parser.non_strict_separator_error_at_index(
            index=1,
            separator="-",
            tag_index=2,
        )
        is None
    )


def test_strict_missing_separator_error_returns_none_for_unknown_tag():
    parser = Parser("1foo", strict=True)

    assert parser.non_strict_missing_separator_error_at_index(index=1) is None


def test_strict_finish_raises_unexpected_input_when_no_specific_error_matches():
    with pytest.raises(UnexpectedInputError):
        Version.parse("1foo", strict=True)
