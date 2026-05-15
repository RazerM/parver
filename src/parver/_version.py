from __future__ import annotations

import itertools
import operator
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Literal, TypeAlias, TypeVar, cast, overload

from ._helpers import IMPLICIT_ZERO, UNSET, Infinity, UnsetType, last
from ._release_int import ReleaseInt
from ._typing import ImplicitZero, NormalizedPreTag, Separator

if sys.version_info >= (3, 11):
    from typing import Unpack
else:
    from typing_extensions import Unpack

PRE_TAG: tuple[str, ...] = ("alpha", "beta", "preview", "pre", "rc", "a", "b", "c")
PRE_TAG_STRICT: tuple[str, ...] = ("a", "b", "rc")
POST_TAG: tuple[str, ...] = ("post", "rev", "r")
POST_TAG_STRICT: tuple[str, ...] = ("post",)
DEV_TAG: tuple[str, ...] = ("dev",)
SEPARATOR: tuple[Separator, ...] = (".", "-", "_")
SEPARATOR_STRICT: tuple[Separator, ...] = (".",)

T = TypeVar("T")

_local_version_separators = re.compile(r"[._-]")


def check_by(by: int, current: int | None) -> None:
    """Validate the 'by' parameter for bump methods."""
    if not isinstance(by, int):
        raise TypeError("by must be an integer")

    if current is None and by < 0:
        raise ValueError("Cannot bump by negative amount when current value is unset.")


def _normalize_pre_tag(pre_tag: str | None) -> NormalizedPreTag | None:
    """Normalize a pre-release tag to its canonical form."""
    if pre_tag is None:
        return None

    pre_tag_lower = pre_tag.lower()
    if pre_tag_lower == "alpha":
        return "a"
    elif pre_tag_lower == "beta":
        return "b"
    elif pre_tag_lower in {"c", "pre", "preview"}:
        return "rc"
    elif pre_tag_lower in {"a", "b", "rc"}:
        return cast(NormalizedPreTag, pre_tag_lower)

    # Unknown tag - shouldn't happen with valid versions
    return cast(NormalizedPreTag, pre_tag_lower)


@overload
def _parse_local_version_normalized(local: str) -> tuple[str | int, ...]: ...


@overload
def _parse_local_version_normalized(local: None) -> None: ...


def _parse_local_version_normalized(local: str | None) -> tuple[str | int, ...] | None:
    """
    Takes a string like abc.1.twelve and turns it into ("abc", 1, "twelve").
    """
    if local is not None:
        return tuple(
            part.lower() if not part.isdigit() else int(part)
            for part in _local_version_separators.split(local)
        )

    return None


def _normalize_local(local: str | None) -> str | None:
    """Normalize a local version string."""
    if local is None:
        return None

    return ".".join(map(str, _parse_local_version_normalized(local)))


def _cmpkey(
    epoch: int,
    release: tuple[int, ...],
    pre_tag: NormalizedPreTag | None,
    pre_num: int | None,
    post: int | None,
    dev: int | None,
    local: str | None,
) -> Any:
    """Create a comparison key for version ordering."""
    # When we compare a release version, we want to compare it with all of the
    # trailing zeros removed. So we'll use a reverse the list, drop all the now
    # leading zeros until we come to something non zero, then take the rest
    # re-reverse it back into the correct order and make it a tuple and use
    # that for our sorting key.
    release = tuple(
        reversed(
            list(
                itertools.dropwhile(
                    lambda x: x == 0,
                    reversed(release),
                )
            )
        )
    )

    pre: Any = pre_tag, pre_num

    # We need to "trick" the sorting algorithm to put 1.0.dev0 before 1.0a0.
    # We'll do this by abusing the pre segment, but we _only_ want to do this
    # if there is not a pre or a post segment. If we have one of those then
    # the normal sorting rules will handle this case correctly.
    if pre_num is None and post is None and dev is not None:
        pre = -Infinity
    # Versions without a pre-release (except as noted above) should sort after
    # those with one.
    elif pre_num is None:
        pre = Infinity

    # Versions without a post segment should sort before those with one.
    post_key: Any = post
    if post is None:
        post_key = -Infinity

    # Versions without a development segment should sort after those with one.
    dev_key: Any = dev
    if dev is None:
        dev_key = Infinity

    local_key: Any
    if local is None:
        # Versions without a local segment should sort before those with one.
        local_key = -Infinity
    else:
        # Versions with a local segment need that segment parsed to implement
        # the sorting rules in PEP440.
        # - Alpha numeric segments sort before numeric segments
        # - Alpha numeric segments sort lexicographically
        # - Numeric segments sort numerically
        # - Shorter versions sort before longer versions when the prefixes
        #   match exactly
        local_key = tuple(
            (i, "") if isinstance(i, int) else (-Infinity, i)
            for i in _parse_local_version_normalized(local)
        )

    return epoch, release, pre, post_key, dev_key, local_key


class ParseError(ValueError):
    """Raised when parsing an invalid version number."""


def _format_expected(expected: Iterable[str]) -> str:
    expected = _dedupe_ordered(expected)
    if len(expected) == 1:
        return expected[0]
    if len(expected) == 2:
        return f"{expected[0]} or {expected[1]}"
    return f"{', '.join(expected[:-1])}, or {expected[-1]}"


def _dedupe_ordered(items: Iterable[str]) -> tuple[str, ...]:
    """Return unique strings while preserving their first-seen order."""
    return tuple(dict.fromkeys(items))


def _format_found(version: str, index: int) -> str:
    if index >= len(version):
        return "end of input"
    return repr(version[index])


class NoLeadingNumberError(ParseError):
    def __init__(self, *, version: str | None = None, index: int = 0):
        super().__init__()
        self.version = version
        self.index = index

    def __str__(self) -> str:
        if self.version is not None:
            found = _format_found(self.version, self.index)
            return f"Expected a release number at position {self.index}, found {found}"
        return "Expected a release number"

    def __reduce__(self) -> tuple[Any, ...]:
        cls = type(self)
        return cls.__new__, (cls, *self.args), self.__dict__


class TrailingDataError(ParseError):
    version: str
    remaining: str

    def __init__(self, *, version: str, remaining: str):
        super().__init__()
        self.version = version
        self.remaining = remaining

    def __str__(self) -> str:
        return (
            f"Expected end of version at position {len(self.version)}, "
            f"found {self.remaining!r}"
        )

    def __reduce__(self) -> tuple[Any, ...]:
        cls = type(self)
        return cls.__new__, (cls, *self.args), self.__dict__


class UnexpectedInputError(TrailingDataError):
    full_version: str
    index: int
    expected: tuple[str, ...]

    def __init__(self, *, version: str, index: int, expected: Iterable[str]):
        super().__init__(version=version[:index], remaining=version[index:])
        self.full_version = version
        self.index = index
        self.expected = _dedupe_ordered(expected)

    def __str__(self) -> str:
        expected = _format_expected(self.expected)
        found = _format_found(self.full_version, self.index)
        return f"Expected {expected} at position {self.index}, found {found}"


class LocalEmptyError(ParseError):
    def __init__(self, *, precursor: str):
        super().__init__()
        self.precursor = precursor

    def __str__(self) -> str:
        return f"Expected a local version segment after {self.precursor!r}"

    def __reduce__(self) -> tuple[Any, ...]:
        cls = type(self)
        return cls.__new__, (cls, *self.args), self.__dict__


class StrictParseError(ParseError):
    """Base class for strict mode parse errors."""


class StrictPreTagError(UnexpectedInputError, StrictParseError):
    tag: str
    normalized_tag: str

    def __init__(self, *, version: str, index: int, tag: str):
        super().__init__(
            version=version,
            index=index,
            expected=("a strict pre-release tag",),
        )
        self.tag = tag
        normalized_tag = _normalize_pre_tag(tag)
        assert normalized_tag is not None
        self.normalized_tag = normalized_tag

    def __str__(self) -> str:
        return (
            f"Pre-release tag {self.tag!r} is not allowed in strict mode "
            f"at position {self.index}; use {self.normalized_tag!r} in strict mode"
        )


class StrictSegmentError(UnexpectedInputError, StrictParseError):
    message: str

    def __init__(self, *, version: str, index: int, message: str):
        super().__init__(
            version=version,
            index=index,
            expected=("strict version syntax",),
        )
        self.message = message

    def __str__(self) -> str:
        return self.message


class VPrefixNotAllowedError(StrictParseError):
    """Raised when 'v' prefix is used in strict mode."""

    def __str__(self) -> str:
        return "The 'v' prefix is not allowed in strict mode"


class LeadingZerosError(StrictParseError):
    """Raised when a number has leading zeros in strict mode."""

    def __init__(self, number: str, context: str | None = None):
        super().__init__()
        self.number = number
        self.context = context

    def __str__(self) -> str:
        subject = f"{self.context} number" if self.context else "number"
        return (
            f"Leading zeros in {subject}s are not allowed in strict mode: "
            f"{self.number!r}; use {str(int(self.number))!r} in strict mode"
        )


class ImplicitNumberError(StrictParseError):
    """Raised when an implicit number is used where explicit is required in strict mode."""

    def __init__(
        self,
        context: str | None = None,
        *,
        version: str | None = None,
        index: int = 0,
    ):
        super().__init__()
        self.context = context
        self.version = version
        self.index = index

    def __str__(self) -> str:
        ctx = self.context or "segment"
        if self.version is not None:
            found = _format_found(self.version, self.index)
            return (
                f"Implicit {ctx} numbers are not allowed in strict mode "
                f"at position {self.index}; use '0' in strict mode "
                f"(found {found})"
            )
        return f"Explicit number required for {ctx} in strict mode"

    def __reduce__(self) -> tuple[Any, ...]:
        cls = type(self)
        return cls.__new__, (cls, *self.args), self.__dict__


class InvalidLocalError(StrictParseError):
    """Raised when local version contains invalid characters in strict mode."""

    def __init__(
        self,
        local: str,
        reason: str | None = None,
        *,
        replacement: str | None = None,
    ):
        super().__init__()
        self.local = local
        self.reason = reason
        self.replacement = replacement

    def __str__(self) -> str:
        if self.replacement is not None:
            return (
                f"Local version segment {self.local!r} is not allowed in "
                f"strict mode: {self.reason}; use {self.replacement!r} "
                "in strict mode"
            )
        reason_str = f": {self.reason}" if self.reason else ""
        return f"Invalid local version in strict mode{reason_str}: {self.local!r}"

    def __reduce__(self) -> tuple[Any, ...]:
        cls = type(self)
        return cls.__new__, (cls, *self.args), self.__dict__


KeyPath: TypeAlias = str | tuple[str, Unpack[tuple[str | int, ...]]]
NonEmptyTuple: TypeAlias = tuple[T, Unpack[tuple[T, ...]]]


def _nicepath(path: KeyPath) -> str:
    if isinstance(path, str):
        return path
    assert isinstance(path[0], str)
    parts = [path[0]]
    for part in path[1:]:
        if isinstance(part, str):
            parts.append(f".{part}")
        else:
            parts.append(f"[{part}]")
    return "".join(parts)


def _validate_numeric_component(
    path: KeyPath,
    value: Any,
    *,
    allow_implicit: bool = False,
) -> None:
    if allow_implicit and value == IMPLICIT_ZERO:
        return
    # For release validation, use 'release' in error messages
    name = (
        "'release'"
        if (isinstance(path, tuple) and path[0] == "release")
        else _nicepath(path)
    )
    if isinstance(value, bool):
        raise TypeError(f"{name} must not be a bool (got {value!r})")
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer (got {value!r})")
    if value < 0:
        raise ValueError(f"{name} must be non-negative (got {value!r})")


def _validate_separator(name: str, value: Any) -> None:
    if value not in SEPARATOR:
        raise ValueError(f"{name} must be one of {SEPARATOR!r} (got {value!r})")


def _validate_tag(name: str, value: str, allowed: tuple[str, ...]) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string (got {value!r})")
    if value.lower() not in allowed:
        raise ValueError(f"{name} must be one of {allowed!r} (got {value!r})")


def _validate_pre_tag(value: str) -> None:
    _validate_tag("pre_tag", value, PRE_TAG)


def _validate_post_tag(value: str) -> None:
    _validate_tag("post_tag", value, POST_TAG)


def _validate_dev_tag(value: str) -> None:
    _validate_tag("dev_tag", value, DEV_TAG)


def _release_target_part(
    current: int,
    *,
    value: int | None = None,
    width: int | None = None,
) -> int:
    if value is None:
        updated = current + 1
        if width is not None:
            return ReleaseInt(updated, width=width)
        return updated

    if width is not None:
        return ReleaseInt(value, width=width)
    if isinstance(current, ReleaseInt):
        return ReleaseInt(value, width=current.minimum_width)
    return value


class Version:
    """
    A PEP 440 version number.

    :param release: Numbers for the release segment.

    :param v: Optional preceding v character.

    :param epoch: Version epoch. Implicitly zero but hidden by default.

    :param pre_tag: Pre-release identifier, typically `a`, `b`, or `rc`.
        Required to signify a pre-release.

    :param pre: Pre-release number. May be ``''`` to signify an
        implicit pre-release number.

    :param post: Post-release number. May be ``''`` to signify an
        implicit post release number.

    :param dev: Developmental release number. May be ``''`` to signify an
        implicit development release number.

    :param local: Local version segment.

    :param pre_sep1: Specify an alternate separator before the pre-release
        segment. The normal form is `None`.

    :param pre_sep2: Specify an alternate separator between the identifier and
        number. The normal form is `None`.

    :param post_sep1: Specify an alternate separator before the post release
        segment. The normal form is ``'.'``.

    :param post_sep2: Specify an alternate separator between the identifier and
        number. The normal form is `None`.

    :param dev_sep1: Specify an alternate separator before the development
        release segment. The normal form is ``'.'``.

    :param dev_sep2: Specify an alternate separator between the identifier and
        number. The normal form is `None`.

    :param post_tag: Specify alternate post release identifier `rev` or `r`.
        May be `None` to signify an implicit post release.
    """

    __slots__ = (
        "_frozen",
        "_key",
        "dev",
        "dev_implicit",
        "dev_sep1",
        "dev_sep2",
        "dev_tag",
        "epoch",
        "epoch_implicit",
        "local",
        "post",
        "post_implicit",
        "post_sep1",
        "post_sep2",
        "post_tag",
        "pre",
        "pre_implicit",
        "pre_sep1",
        "pre_sep2",
        "pre_tag",
        "release",
        "v",
    )

    _frozen: bool
    _key: Any
    v: Literal["v", "V"] | None
    epoch: int
    epoch_implicit: bool
    release: NonEmptyTuple[int]
    pre_sep1: Separator | None
    pre_tag: str | None
    pre_sep2: Separator | None
    pre: int | None
    pre_implicit: bool
    post_sep1: Separator | None
    post_tag: str | None
    post_sep2: Separator | None
    post: int | None
    post_implicit: bool
    dev_sep1: Separator | None
    dev_tag: str | None
    dev_sep2: Separator | None
    dev: int | None
    dev_implicit: bool
    local: str | None

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_frozen", False):
            raise AttributeError(f"{type(self).__name__} is immutable")
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"{type(self).__name__} is immutable")

    def __getstate__(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__slots__}

    def __setstate__(self, state: dict[str, Any]) -> None:
        for name, value in state.items():
            object.__setattr__(self, name, value)

    def __init__(
        self,
        *,
        v: Literal["v", "V"] | bool | None = None,
        epoch: ImplicitZero | int = IMPLICIT_ZERO,
        release: int | Iterable[int],
        pre_sep1: Separator | None = None,
        pre_tag: str | None = None,
        pre_sep2: Separator | None = None,
        pre: ImplicitZero | int | None = None,
        post_sep1: Separator | None | UnsetType = UNSET,
        post_tag: str | None | UnsetType = UNSET,
        post_sep2: Separator | None | UnsetType = UNSET,
        post: ImplicitZero | int | None = None,
        dev_sep1: Separator | None | UnsetType = UNSET,
        dev_tag: str | None = None,
        dev_sep2: Separator | None | UnsetType = UNSET,
        dev: ImplicitZero | int | None = None,
        local: str | None = None,
    ) -> None:
        self._frozen = False
        match v:
            case True:
                self.v = "v"
            case False:
                self.v = None
            case "v" | "V" | None:
                self.v = v
            case _:
                raise TypeError("v must be 'v', 'V', bool, or None")
        _validate_numeric_component("epoch", epoch, allow_implicit=True)
        if epoch == IMPLICIT_ZERO:
            self.epoch = 0
            self.epoch_implicit = True
        else:
            self.epoch = epoch
            self.epoch_implicit = False
        if isinstance(release, Iterable) and not isinstance(release, str):
            release = tuple(release)
        elif isinstance(release, int):
            release = (release,)
        if not isinstance(release, tuple):
            raise TypeError(
                f"release must be an int or iterable of ints (got {release!r})"
            )
        for i, number in enumerate(release):
            _validate_numeric_component(("release", i), number)
        if not release:
            raise ValueError("'release' cannot be empty")
        self.release = release
        if pre is not None:
            _validate_numeric_component("pre", pre, allow_implicit=True)
        if pre_sep1 is not None:
            _validate_separator("pre_sep1", pre_sep1)
        if pre_sep2 is not None:
            _validate_separator("pre_sep2", pre_sep2)
        if pre_tag is None:
            if pre is not None:
                raise ValueError("Must set pre_tag if pre is given.")
            if pre_sep1 is not None or pre_sep2 is not None:
                raise ValueError("Cannot set pre_sep1 or pre_sep2 without pre_tag.")
        else:
            _validate_pre_tag(pre_tag)
            if pre is None:
                raise ValueError("Must set pre if pre_tag is given.")
        self.pre_tag = pre_tag

        if pre == IMPLICIT_ZERO:
            self.pre = 0
            self.pre_implicit = True
        else:
            self.pre = pre
            self.pre_implicit = False
        self.pre_sep1 = pre_sep1
        self.pre_sep2 = pre_sep2

        if post is not None:
            _validate_numeric_component("post", post, allow_implicit=True)
        if post_sep1 is not None and post_sep1 is not UNSET:
            _validate_separator("post_sep1", post_sep1)
        if post_sep2 is not None and post_sep2 is not UNSET:
            _validate_separator("post_sep2", post_sep2)

        got_post_tag = post_tag is not UNSET
        got_post = post is not None
        got_post_sep1 = post_sep1 is not UNSET
        got_post_sep2 = post_sep2 is not UNSET

        # post_tag relies on post
        if got_post_tag and not got_post:
            raise ValueError("Must set post if post_tag is given.")

        if got_post:
            if not got_post_tag:
                # user gets the default for post_tag
                post_tag = "post"
            if post == IMPLICIT_ZERO:
                self.post_implicit = True
                self.post = 0
            else:
                self.post_implicit = False
                self.post = post
        else:
            self.post_implicit = False
            self.post = None

        # Validate parameters for implicit post-release (post_tag=None).
        # An implicit post-release is e.g. '1-2' (== '1.post2')
        if post_tag is None:
            if self.post_implicit:
                raise ValueError(
                    "Implicit post releases (post_tag=None) require a numerical "
                    "value for 'post' argument."
                )

            if got_post_sep1 or got_post_sep2:
                raise ValueError(
                    "post_sep1 and post_sep2 cannot be set for implicit post "
                    "releases (post_tag=None)"
                )

            if self.pre_implicit and self.pre_sep2 is None:
                raise ValueError(
                    "post_tag cannot be None with an implicit pre-release "
                    "(pre='') unless pre_sep2 is not None."
                )

            self.post_sep1 = "-"
        elif post_tag is UNSET:
            if got_post_sep1 or got_post_sep2:
                raise ValueError("Cannot set post_sep1 or post_sep2 without post_tag.")

            post_tag = None
            self.post_sep1 = None if self.post is None else "."
        else:
            assert not isinstance(post_tag, UnsetType)
            _validate_post_tag(post_tag)
            if not got_post_sep1:
                self.post_sep1 = None if self.post is None else "."
            else:
                assert not isinstance(post_sep1, UnsetType)
                self.post_sep1 = post_sep1

        if not got_post_sep2:
            self.post_sep2 = None
        else:
            assert not isinstance(post_sep2, UnsetType)
            self.post_sep2 = post_sep2

        assert not isinstance(post_tag, UnsetType)
        self.post_tag = post_tag

        if dev is not None:
            _validate_numeric_component("dev", dev, allow_implicit=True)
        if dev_sep1 is not None and dev_sep1 is not UNSET:
            _validate_separator("dev_sep1", dev_sep1)
        if dev_sep2 is not None and dev_sep2 is not UNSET:
            _validate_separator("dev_sep2", dev_sep2)

        got_dev_sep1 = dev_sep1 is not UNSET
        got_dev_sep2 = dev_sep2 is not UNSET

        if dev == IMPLICIT_ZERO:
            self.dev_implicit = True
            self.dev = 0
        elif dev is not None:
            self.dev_implicit = False
            self.dev = dev
        else:
            self.dev_implicit = False
            self.dev = None
            if got_dev_sep1:
                raise ValueError("Cannot set dev_sep1 without dev.")
            if got_dev_sep2:
                raise ValueError("Cannot set dev_sep2 without dev.")

        if not got_dev_sep1:
            self.dev_sep1 = None if self.dev is None else "."
        else:
            assert not isinstance(dev_sep1, UnsetType)
            self.dev_sep1 = dev_sep1

        if not got_dev_sep2:
            self.dev_sep2 = None
        else:
            assert not isinstance(dev_sep2, UnsetType)
            self.dev_sep2 = dev_sep2

        if dev_tag is not None:
            _validate_dev_tag(dev_tag)
        self.dev_tag = dev_tag

        if local is not None and not isinstance(local, str):
            raise TypeError(f"local must be a string (got {local!r})")
        self.local = local

        # Compute comparison key
        self._key = _cmpkey(
            self.epoch,
            self.release,
            _normalize_pre_tag(self.pre_tag),
            self.pre,
            self.post,
            self.dev,
            self.local,
        )
        self._frozen = True

    @classmethod
    def parse(cls, version: str, *, strict: bool = False) -> Version:
        """
        Parse a version string.

        :param version: Version number as defined in PEP 440.
        :param strict: Enable strict parsing of the canonical PEP 440 format.
        :raises ParseError: If version is not valid for the given value of `strict`.
        """
        return Parser(version, strict=strict).parse()

    def __str__(self) -> str:
        parts: list[str] = []

        if self.v:
            parts.append(self.v)

        if not self.epoch_implicit:
            parts.append(f"{self.epoch}!")

        parts.append(".".join(str(x) for x in self.release))

        if self.pre_tag is not None:
            if self.pre_sep1:
                parts.append(self.pre_sep1)
            parts.append(self.pre_tag)
            if self.pre_sep2:
                parts.append(self.pre_sep2)
            if not self.pre_implicit:
                parts.append(str(self.pre))

        if self.post_tag is None and self.post is not None:
            parts.append(f"-{self.post}")
        elif self.post_tag is not None:
            if self.post_sep1:
                parts.append(self.post_sep1)
            parts.append(self.post_tag)
            if self.post_sep2:
                parts.append(self.post_sep2)
            if not self.post_implicit:
                parts.append(str(self.post))

        if self.dev is not None:
            if self.dev_sep1 is not None:
                parts.append(self.dev_sep1)
            parts.append(self.dev_tag if self.dev_tag is not None else "dev")
            if self.dev_sep2:
                parts.append(self.dev_sep2)
            if not self.dev_implicit:
                parts.append(str(self.dev))

        if self.local is not None:
            parts.append(f"+{self.local}")

        return "".join(parts)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {str(self)!r}>"

    def __hash__(self) -> int:
        return hash(self._key)

    def __lt__(self, other: Any) -> Any:
        return self._compare(other, operator.lt)

    def __le__(self, other: Any) -> Any:
        return self._compare(other, operator.le)

    def __eq__(self, other: Any) -> Any:
        return self._compare(other, operator.eq)

    def __ge__(self, other: Any) -> Any:
        return self._compare(other, operator.ge)

    def __gt__(self, other: Any) -> Any:
        return self._compare(other, operator.gt)

    def __ne__(self, other: Any) -> Any:
        return self._compare(other, operator.ne)

    def _compare(self, other: Any, method: Callable[[Any, Any], bool]) -> Any:
        if not isinstance(other, Version):
            return NotImplemented

        return method(self._key, other._key)

    @property
    def public(self) -> str:
        """A string representing the public version portion of this
        Version instance (without the local segment).
        """
        return str(self).split("+", 1)[0]

    @property
    def is_prerelease(self) -> bool:
        """A boolean value indicating whether this Version instance
        represents a pre-release and/or development release.
        """
        return self.dev is not None or self.pre is not None

    @property
    def is_alpha(self) -> bool:
        """A boolean value indicating whether this Version instance
        represents an alpha pre-release.
        """
        return _normalize_pre_tag(self.pre_tag) == "a"

    @property
    def is_beta(self) -> bool:
        """A boolean value indicating whether this Version instance
        represents a beta pre-release.
        """
        return _normalize_pre_tag(self.pre_tag) == "b"

    @property
    def is_release_candidate(self) -> bool:
        """A boolean value indicating whether this Version instance
        represents a release candidate pre-release.
        """
        return _normalize_pre_tag(self.pre_tag) == "rc"

    @property
    def is_postrelease(self) -> bool:
        """A boolean value indicating whether this Version instance
        represents a post-release.
        """
        return self.post is not None

    @property
    def is_devrelease(self) -> bool:
        """A boolean value indicating whether this Version instance
        represents a development release.
        """
        return self.dev is not None

    def _attrs_as_init(self) -> dict[str, Any]:
        """Convert current attributes to a dict suitable for __init__."""
        d: dict[str, Any] = dict(
            release=self.release,
            v=self.v,
            epoch=IMPLICIT_ZERO if self.epoch_implicit else self.epoch,
            local=self.local,
        )

        if self.pre is not None:
            d["pre"] = IMPLICIT_ZERO if self.pre_implicit else self.pre
            d["pre_tag"] = self.pre_tag
            d["pre_sep1"] = self.pre_sep1
            d["pre_sep2"] = self.pre_sep2

        if self.post is not None:
            d["post"] = IMPLICIT_ZERO if self.post_implicit else self.post
            d["post_tag"] = self.post_tag
            if self.post_tag is not None:
                d["post_sep1"] = self.post_sep1
                d["post_sep2"] = self.post_sep2

        if self.dev is not None:
            d["dev"] = IMPLICIT_ZERO if self.dev_implicit else self.dev
            d["dev_tag"] = self.dev_tag
            d["dev_sep1"] = self.dev_sep1
            d["dev_sep2"] = self.dev_sep2

        return d

    def replace(
        self,
        release: int | Iterable[int] | UnsetType = UNSET,
        v: Literal["v", "V"] | None | UnsetType = UNSET,
        epoch: ImplicitZero | int | UnsetType = UNSET,
        pre_tag: str | None | UnsetType = UNSET,
        pre: ImplicitZero | int | None | UnsetType = UNSET,
        post: ImplicitZero | int | None | UnsetType = UNSET,
        dev: ImplicitZero | int | None | UnsetType = UNSET,
        local: str | None | UnsetType = UNSET,
        pre_sep1: Separator | None | UnsetType = UNSET,
        pre_sep2: Separator | None | UnsetType = UNSET,
        post_sep1: Separator | None | UnsetType = UNSET,
        post_sep2: Separator | None | UnsetType = UNSET,
        dev_sep1: Separator | None | UnsetType = UNSET,
        dev_sep2: Separator | None | UnsetType = UNSET,
        post_tag: str | None | UnsetType = UNSET,
        dev_tag: str | None | UnsetType = UNSET,
    ) -> Version:
        """Return a new Version instance with the same attributes,
        except for those given as keyword arguments. Arguments have the same
        meaning as they do when constructing a new Version instance manually.
        """
        kwargs: dict[str, Any] = dict(
            release=release,
            v=v,
            epoch=epoch,
            pre_tag=pre_tag,
            pre=pre,
            post=post,
            dev=dev,
            local=local,
            pre_sep1=pre_sep1,
            pre_sep2=pre_sep2,
            post_sep1=post_sep1,
            post_sep2=post_sep2,
            dev_sep1=dev_sep1,
            dev_sep2=dev_sep2,
            post_tag=post_tag,
            dev_tag=dev_tag,
        )
        kwargs = {k: v for k, v in kwargs.items() if v is not UNSET}
        d = self._attrs_as_init()

        if kwargs.get("post_tag", UNSET) is None:
            # ensure we don't carry over separators for new implicit post
            # release. By popping from d, there will still be an error if the
            # user tries to set them in kwargs
            d.pop("post_sep1", None)
            d.pop("post_sep2", None)

        if kwargs.get("post", UNSET) is None:
            kwargs["post_tag"] = UNSET
            d.pop("post_sep1", None)
            d.pop("post_sep2", None)

        if kwargs.get("pre", UNSET) is None:
            kwargs["pre_tag"] = None
            d.pop("pre_sep1", None)
            d.pop("pre_sep2", None)

        if kwargs.get("dev", UNSET) is None:
            d.pop("dev_sep1", None)
            d.pop("dev_sep2", None)
            d.pop("dev_tag", None)

        d.update(kwargs)
        return Version(**d)

    def _set_release(
        self,
        index: int,
        value: int | None = None,
        bump: bool = True,
        width: int | None = None,
    ) -> Version:
        """Helper method for release-related bump operations."""
        if not isinstance(index, int):
            raise TypeError("index must be an integer")

        if index < 0:
            raise ValueError("index cannot be negative")

        release = list(self.release)
        new_len = index + 1

        if len(release) < new_len:
            release.extend(itertools.repeat(0, new_len - len(release)))

        def new_parts(i: int, n: int) -> int:
            if i < index:
                return n
            if i == index:
                return _release_target_part(n, value=value, width=width)
            if bump:
                if isinstance(n, ReleaseInt):
                    return n.zero_like()
                return 0
            return n

        new_release = list(itertools.starmap(new_parts, enumerate(release)))
        return self.replace(release=new_release)

    def bump_epoch(self, *, by: int = 1, width: int | None = None) -> Version:
        """Return a new Version instance with the epoch number bumped.

        :param by: How much to bump the number by.
        :param width: Minimum width for the resulting epoch number.
        :raises TypeError: `by` is not an integer.
        """
        check_by(by, self.epoch)

        epoch = by - 1 if self.epoch is None else self.epoch + by
        if width is not None:
            epoch = ReleaseInt(epoch, width=width)
        return self.replace(epoch=epoch)

    def bump_release(self, *, index: int, width: int | None = None) -> Version:
        """Return a new Version instance with the release number bumped at
        the given `index`.

        :param index: Index of the release number tuple to bump. It is not
            limited to the current size of the tuple. Intermediate indices
            will be set to zero.
        :param width: Minimum width for the resulting release number at `index`.
        :raises TypeError: `index` is not an integer.
        :raises ValueError: `index` is negative.
        """
        return self._set_release(index=index, width=width)

    def bump_release_to(
        self, *, index: int, value: int, width: int | None = None
    ) -> Version:
        """Return a new Version instance with the release number bumped at
        the given `index` to `value`. May be used for CalVer.

        :param index: Index of the release number tuple to bump.
        :param value: Value to bump to. Subsequent indices will be set to zero.
        :param width: Minimum width for the resulting release number at `index`.
        :raises TypeError: `index` is not an integer.
        :raises ValueError: `index` is negative.
        """
        return self._set_release(index=index, value=value, width=width)

    def set_release(self, *, index: int, value: int) -> Version:
        """Return a new Version instance with the release number at the given
        `index` set to `value`.

        :param index: Index of the release number tuple to set.
        :param value: Value to set.
        :raises TypeError: `index` is not an integer.
        :raises ValueError: `index` is negative.
        """
        return self._set_release(index=index, value=value, bump=False)

    def bump_pre(
        self, tag: str | None = None, *, by: int = 1, width: int | None = None
    ) -> Version:
        """Return a new Version instance with the pre-release number bumped.

        :param tag: Pre-release tag. Required if not already set.
        :param by: How much to bump the number by.
        :param width: Minimum width for the resulting pre-release number.
        :raises ValueError: Trying to call bump_pre(tag=None) on a Version
            that is not already a pre-release.
        :raises ValueError: Calling with a tag not equal to the current pre_tag.
        :raises TypeError: `by` is not an integer.
        """
        check_by(by, self.pre)

        pre = by - 1 if self.pre is None else self.pre + by
        if width is not None:
            pre = ReleaseInt(pre, width=width)

        if self.pre_tag is None:
            if tag is None:
                raise ValueError("Cannot bump without pre_tag. Use .bump_pre('<tag>')")
        else:
            # This is an error because different tags have different meanings
            if tag is not None and self.pre_tag.lower() != tag.lower():
                raise ValueError(
                    f"Cannot bump with pre_tag mismatch ({self.pre_tag} != {tag}). "
                    f"Use .replace(pre_tag={tag!r})"
                )
            tag = self.pre_tag

        return self.replace(pre=pre, pre_tag=tag)

    @overload
    def bump_post(
        self, tag: str | None, *, by: int = 1, width: int | None = None
    ) -> Version: ...

    @overload
    def bump_post(self, *, by: int = 1, width: int | None = None) -> Version: ...

    def bump_post(
        self,
        tag: str | None | UnsetType = UNSET,
        *,
        by: int = 1,
        width: int | None = None,
    ) -> Version:
        """Return a new Version instance with the post release number bumped.

        :param tag: Post release tag. Will preserve the current tag by default,
            or use 'post' if the instance is not already a post release.
        :param by: How much to bump the number by.
        :param width: Minimum width for the resulting post-release number.
        :raises TypeError: `by` is not an integer.
        """
        check_by(by, self.post)

        post = by - 1 if self.post is None else self.post + by
        if width is not None:
            post = ReleaseInt(post, width=width)
        if tag is UNSET and self.post is not None:
            tag = self.post_tag
        return self.replace(post=post, post_tag=tag)

    def bump_dev(self, *, by: int = 1, width: int | None = None) -> Version:
        """Return a new Version instance with the development release number
        bumped.

        :param by: How much to bump the number by.
        :param width: Minimum width for the resulting development release number.
        :raises TypeError: `by` is not an integer.
        """
        check_by(by, self.dev)

        dev = by - 1 if self.dev is None else self.dev + by
        if width is not None:
            dev = ReleaseInt(dev, width=width)
        return self.replace(dev=dev)

    def normalize(self) -> Version:
        """Return a new Version instance with normalized values.

        Normalizes pre-release tags, local version, and removes the v prefix.
        """
        return Version(
            release=[int(x) for x in self.release],
            epoch=IMPLICIT_ZERO if self.epoch == 0 else int(self.epoch),
            pre_tag=_normalize_pre_tag(self.pre_tag),
            pre=None if self.pre is None else int(self.pre),
            post=None if self.post is None else int(self.post),
            dev=None if self.dev is None else int(self.dev),
            local=_normalize_local(self.local),
        )

    def base_version(self) -> Version:
        """Return a new Version instance for the base version.

        The base version is the public version without any pre or post release
        markers.
        """
        return self.replace(pre=None, post=None, dev=None, local=None)

    def truncate(self, *, min_length: int = 1) -> Version:
        """Return a new Version instance with trailing zeros removed from the
        release segment.

        :param min_length: Minimum number of parts to keep.
        :raises TypeError: `min_length` is not an integer.
        :raises ValueError: `min_length` is not positive.
        """
        if not isinstance(min_length, int):
            raise TypeError("min_length must be an integer")

        if min_length < 1:
            raise ValueError("min_length must be positive")

        release = list(self.release)
        if len(release) < min_length:
            release.extend(itertools.repeat(0, min_length - len(release)))

        last_nonzero = max(
            last((i for i, n in enumerate(release) if n), default=0),
            min_length - 1,
        )
        return self.replace(release=release[: last_nonzero + 1])


def is_ascii_digit(c: str) -> bool:
    return "0" <= c <= "9"


def is_ascii_alphanumeric(s: str) -> bool:
    return s.isalnum() and s.isascii()


def is_strict_number(s: str) -> bool:
    """Check if a number string is valid in strict mode (no leading zeros)."""
    if not s:
        return False
    # "0" is valid, "01" is not
    if len(s) > 1 and s[0] == "0":
        return False
    return True


def is_strict_local_alpha(s: str) -> bool:
    """Check if a local part is a valid alpha segment in strict mode.

    Pattern: [0-9]*[a-z][a-z0-9]*
    Must contain at least one lowercase letter.
    """
    if not s:
        return False
    # Must be ASCII alphanumeric
    if not s.isascii() or not s.isalnum():
        return False
    # Must contain at least one lowercase letter
    if not any(c.islower() for c in s):
        return False
    # Find the first letter; the lowercase-letter check above guarantees one exists.
    first_letter_idx = next(i for i, c in enumerate(s) if c.isalpha())
    # First letter and all after must be lowercase alphanumeric
    for c in s[first_letter_idx:]:
        if not (c.islower() or c.isdigit()):
            return False
    return True


@dataclass(slots=True)
class _Cursor:
    text: str
    index: int = 0
    start: int = 0
    end: int = field(init=False)
    text_lower: str = field(init=False)

    def __post_init__(self) -> None:
        self.end = len(self.text)
        assert 0 <= self.start <= self.index <= self.end <= len(self.text)
        self.text_lower = self.text.lower()

    def is_done(self) -> bool:
        return self.index >= self.end

    def reset(self, offset: int) -> None:
        assert self.start <= offset <= self.end
        self.index = offset

    def match(self, string: str, *, case_sensitive: bool = False) -> str | None:
        if self.is_at(string, case_sensitive=case_sensitive):
            found = self.text[self.index : self.index + len(string)]
            self.index += len(string)
            return found
        return None

    def match_any(
        self, strings: tuple[str, ...], *, case_sensitive: bool = False
    ) -> str | None:
        for string in strings:
            if self.is_at(string, case_sensitive=case_sensitive):
                found = self.text[self.index : self.index + len(string)]
                self.index += len(string)
                return found
        return None

    def is_at(self, string: str, *, case_sensitive: bool = False) -> bool:
        haystack = self.text if case_sensitive else self.text_lower
        return self.index + len(string) <= self.end and haystack.startswith(
            string, self.index
        )

    def is_at_any(
        self, strings: tuple[str, ...], *, case_sensitive: bool = False
    ) -> bool:
        return any(
            self.is_at(string, case_sensitive=case_sensitive) for string in strings
        )

    def take_while(self, predicate: Callable[[str], bool]) -> str:
        start = self.index
        while not self.is_done() and predicate(self.text[self.index]):
            self.index += 1
        return self.text[start : self.index]

    def checkpoint(self) -> _CursorCheckpoint:
        return _CursorCheckpoint(self, self.index)


@dataclass(slots=True)
class _CursorCheckpoint:
    cursor: _Cursor
    index: int
    committed: bool = False

    def commit(self) -> None:
        self.committed = True

    def __enter__(self) -> _CursorCheckpoint:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if not self.committed:
            self.cursor.reset(self.index)


@dataclass(slots=True)
class _ParseDiagnostics:
    index: int = -1
    expected: tuple[str, ...] = ()

    def expect(self, index: int, expected: str | Iterable[str]) -> None:
        if isinstance(expected, str):
            expected = (expected,)

        if index > self.index:
            self.index = index
            self.expected = _dedupe_ordered(expected)
        elif index == self.index:
            self.expected = _dedupe_ordered((*self.expected, *expected))

    def error(self, version: str) -> UnexpectedInputError | None:
        if self.index < 0 or not self.expected:
            return None
        return UnexpectedInputError(
            version=version,
            index=self.index,
            expected=self.expected,
        )


@dataclass(slots=True)
class _PreSegment:
    tag: str
    number: int
    sep_before: Separator | None = None
    sep_after_tag: Separator | None = None
    implicit_number: bool = False


@dataclass(slots=True)
class _PostSegment:
    number: int
    tag: str | None = "post"
    sep_before: Separator | None = None
    sep_after_tag: Separator | None = None
    implicit_number: bool = False


@dataclass(slots=True)
class _DevSegment:
    number: int
    tag: str | None = None
    sep_before: Separator | None = None
    sep_after_tag: Separator | None = None
    implicit_number: bool = False


SegmentT = TypeVar("SegmentT", _PreSegment, _PostSegment, _DevSegment)


@dataclass(slots=True)
class _ParsedVersion:
    release: Iterable[int]
    v: Literal["v", "V"] | None = None
    epoch: int = 0
    epoch_implicit: bool = True
    pre: _PreSegment | None = None
    post: _PostSegment | None = None
    dev: _DevSegment | None = None
    local: str | None = None

    def into_version(self) -> Version:
        kwargs: dict[str, Any] = dict(
            v=self.v,
            epoch=IMPLICIT_ZERO if self.epoch_implicit else self.epoch,
            release=self.release,
            local=self.local,
        )

        if self.pre is not None:
            kwargs["pre_sep1"] = self.pre.sep_before
            kwargs["pre_tag"] = self.pre.tag
            kwargs["pre_sep2"] = self.pre.sep_after_tag
            kwargs["pre"] = (
                IMPLICIT_ZERO if self.pre.implicit_number else self.pre.number
            )

        if self.post is not None:
            kwargs["post"] = (
                IMPLICIT_ZERO if self.post.implicit_number else self.post.number
            )
            kwargs["post_tag"] = self.post.tag
            if self.post.tag is not None:
                kwargs["post_sep1"] = self.post.sep_before
                kwargs["post_sep2"] = self.post.sep_after_tag

        if self.dev is not None:
            kwargs["dev"] = (
                IMPLICIT_ZERO if self.dev.implicit_number else self.dev.number
            )
            kwargs["dev_tag"] = self.dev.tag
            kwargs["dev_sep1"] = self.dev.sep_before
            kwargs["dev_sep2"] = self.dev.sep_after_tag

        return Version(**kwargs)


class _SegmentKind(Enum):
    PRE = auto()
    POST = auto()
    DEV = auto()


def _validate_strict_local_part(parts: list[str], part: str) -> None:
    if part.isdigit():
        if not is_strict_number(part):
            raise InvalidLocalError(
                part,
                "leading zeros",
                replacement=str(int(part)),
            )
    elif not is_strict_local_alpha(part):
        replacement = part.lower() if is_strict_local_alpha(part.lower()) else None
        raise InvalidLocalError(
            part,
            "must be lowercase alphanumeric",
            replacement=replacement,
        )


def _validate_strict_number(digits: str, context: str | None = None) -> None:
    if not is_strict_number(digits):
        raise LeadingZerosError(digits, context)


class Parser:
    """PEP 440 version parser.

    In permissive mode it preserves original spelling and accepts the broader
    set of PEP 440 spellings. In strict mode it enforces the canonical form.
    """

    def __init__(self, version: str, *, strict: bool = False) -> None:
        self.strict = strict
        self.version = version
        self.cursor = _Cursor(self.version)
        self.diagnostics = _ParseDiagnostics()

    @property
    def allowed_separators(self) -> tuple[Separator, ...]:
        return SEPARATOR_STRICT if self.strict else SEPARATOR

    @property
    def pre_tags(self) -> tuple[str, ...]:
        return PRE_TAG_STRICT if self.strict else PRE_TAG

    @property
    def post_tags(self) -> tuple[str, ...]:
        return POST_TAG_STRICT if self.strict else POST_TAG

    def parse(self) -> Version:
        self.skip_surrounding_whitespace()
        v = self.parse_v_prefix()
        epoch, epoch_implicit, release = self.parse_epoch_and_release()
        pre = self.parse_pre()
        post = self.parse_post()
        dev = self.parse_dev()
        local = self.parse_local()
        self.skip_surrounding_whitespace()
        self.finish(
            expected=self.expected_after_segments(pre, post, dev, local),
            allow_non_strict_pre_tag=pre is None
            and post is None
            and dev is None
            and local is None,
        )

        return _ParsedVersion(
            v=v,
            epoch=epoch,
            epoch_implicit=epoch_implicit,
            release=release,
            pre=pre,
            post=post,
            dev=dev,
            local=local,
        ).into_version()

    def skip_surrounding_whitespace(self) -> None:
        self.cursor.take_while(str.isspace)

    def parse_v_prefix(self) -> Literal["v", "V"] | None:
        prefix = cast(Literal["v", "V"] | None, self.cursor.match("v"))
        if prefix is None:
            return None
        if self.strict:
            raise VPrefixNotAllowedError
        return prefix

    def parse_epoch_and_release(self) -> tuple[int, bool, list[int]]:
        first_number = self.parse_number("release")
        if first_number is None:
            raise NoLeadingNumberError(
                version=self.version,
                index=self.cursor.index,
            )

        epoch = 0
        epoch_implicit = True
        release_number = first_number

        with self.cursor.checkpoint() as attempt:
            if self.cursor.match("!") is not None:
                parsed_release_number = self.parse_number("release")
                if parsed_release_number is None:
                    raise NoLeadingNumberError(
                        version=self.version,
                        index=self.cursor.index,
                    )

                release_number = parsed_release_number
                attempt.commit()
                epoch = first_number
                epoch_implicit = False

        return epoch, epoch_implicit, self.parse_release_tail(release_number)

    def parse_release_tail(self, first_release_number: int) -> list[int]:
        release = [first_release_number]
        while True:
            with self.cursor.checkpoint() as attempt:
                if self.cursor.match(".") is None:
                    break
                release_number = self.parse_number("release")
                if release_number is None:
                    non_strict_separator_error = (
                        self.non_strict_separator_error_at_index(
                            index=attempt.index,
                            separator=".",
                            tag_index=self.cursor.index,
                        )
                    )
                    if non_strict_separator_error is not None:
                        raise non_strict_separator_error
                    non_strict_error = self.non_strict_segment_error_at_cursor(
                        after_release_separator=True,
                    )
                    if non_strict_error is not None:
                        raise non_strict_error
                    if not self.separator_can_start_following_segment():
                        self.diagnostics.expect(
                            self.cursor.index,
                            self.expected_after_release_separator(),
                        )
                    break
                attempt.commit()
            release.append(release_number)
        return release

    def parse_number(self, context: str | None = None) -> int | None:
        digits = self.cursor.take_while(is_ascii_digit)
        if not digits:
            return None
        if self.strict:
            _validate_strict_number(digits, context)
            return int(digits)
        return ReleaseInt(digits)

    def parse_pre(self) -> _PreSegment | None:
        return self.parse_segment(
            kind=_SegmentKind.PRE,
            tags=self.pre_tags,
            context="pre-release",
            allow_leading_separator=not self.strict,
            allow_number_separator=not self.strict,
            allow_implicit_number=not self.strict,
            segment_type=_PreSegment,
        )

    def parse_post(self) -> _PostSegment | None:
        if not self.strict:
            with self.cursor.checkpoint() as attempt:
                if self.cursor.match("-") is not None:
                    number = self.parse_number("post-release")
                    if number is not None:
                        attempt.commit()
                        return _PostSegment(tag=None, number=number)

        return self.parse_segment(
            kind=_SegmentKind.POST,
            tags=self.post_tags,
            context="post-release",
            allow_leading_separator=not self.strict,
            require_leading_separator=self.strict,
            allow_number_separator=not self.strict,
            allow_implicit_number=not self.strict,
            segment_type=_PostSegment,
        )

    def parse_dev(self) -> _DevSegment | None:
        return self.parse_segment(
            kind=_SegmentKind.DEV,
            tags=("dev",),
            context="development release",
            allow_leading_separator=not self.strict,
            require_leading_separator=self.strict,
            allow_number_separator=not self.strict,
            allow_implicit_number=not self.strict,
            segment_type=_DevSegment,
        )

    def parse_local(self) -> str | None:
        if self.cursor.match("+") is None:
            return None

        precursor = "+"
        parts: list[str] = []
        while True:
            part = self.cursor.take_while(is_ascii_alphanumeric)
            if not part:
                raise LocalEmptyError(precursor=precursor)
            if self.strict:
                _validate_strict_local_part(parts, part)
            parts.append(part)
            separator = self.match_separator()
            if separator is None:
                if (
                    self.strict
                    and not self.cursor.is_done()
                    and self.cursor.text[self.cursor.index] in "-_"
                ):
                    raise StrictSegmentError(
                        version=self.version,
                        index=self.cursor.index,
                        message=(
                            f"Local version separator "
                            f"{self.cursor.text[self.cursor.index]!r} is not "
                            f"allowed in strict mode at position "
                            f"{self.cursor.index}; use '.' in strict mode"
                        ),
                    )
                break
            parts.append(separator)
            precursor = separator

        return "".join(parts)

    def parse_segment(
        self,
        *,
        kind: _SegmentKind,
        tags: tuple[str, ...],
        context: str,
        allow_leading_separator: bool = False,
        require_leading_separator: bool = False,
        allow_number_separator: bool = False,
        allow_implicit_number: bool = False,
        segment_type: type[SegmentT],
    ) -> SegmentT | None:
        with self.cursor.checkpoint() as attempt:
            sep_before = None
            if allow_leading_separator or require_leading_separator:
                sep_before = self.match_separator()
            if require_leading_separator and sep_before is None:
                return None

            tag_start = self.cursor.index
            tag = self.match_tags(tags)
            if tag is None:
                return None

            sep_after_tag = None
            number = None
            with self.cursor.checkpoint() as number_attempt:
                candidate_sep_after_tag = None
                if allow_number_separator:
                    candidate_sep_after_tag = self.match_separator()
                number = self.parse_number(context)
                if number is not None or (
                    candidate_sep_after_tag is not None
                    and not self.separator_belongs_to_next_segment(kind)
                ):
                    sep_after_tag = candidate_sep_after_tag
                    number_attempt.commit()

            implicit_number = number is None
            if implicit_number:
                if not allow_implicit_number:
                    if (
                        self.strict
                        and self.cursor.index < len(self.version)
                        and self.version[self.cursor.index] in SEPARATOR
                    ):
                        number_separator_error = (
                            self.non_strict_number_separator_error_at_index(
                                index=self.cursor.index,
                                context=context,
                            )
                        )
                        if number_separator_error is not None:
                            raise number_separator_error
                    if kind is _SegmentKind.PRE:
                        non_strict_pre_tag = self.non_strict_pre_tag_at_index(tag_start)
                        if non_strict_pre_tag is not None:
                            raise StrictPreTagError(
                                version=self.version,
                                index=tag_start,
                                tag=non_strict_pre_tag,
                            )
                    raise ImplicitNumberError(
                        context,
                        version=self.version,
                        index=self.cursor.index,
                    )
                number = 0
            assert number is not None

            attempt.commit()
            return segment_type(
                tag=tag,
                number=number,
                sep_before=sep_before,
                sep_after_tag=sep_after_tag,
                implicit_number=implicit_number,
            )

    def match_tags(self, tags: tuple[str, ...]) -> str | None:
        return self.cursor.match_any(tags, case_sensitive=self.strict)

    def match_separator(self) -> Separator | None:
        return cast(
            Separator | None,
            self.cursor.match_any(self.allowed_separators),
        )

    def separator_belongs_to_next_segment(self, current: _SegmentKind) -> bool:
        return self.is_at_tag(self.following_tags(current))

    def separator_can_start_following_segment(self) -> bool:
        if self.strict:
            return self.is_at_tag((*self.post_tags, "dev"))
        return self.is_at_tag((*self.pre_tags, *self.post_tags, "dev"))

    def expected_after_release_separator(self) -> tuple[str, ...]:
        expected = ["a release number"]
        if not self.strict:
            expected.append("a pre-release tag")
        expected.append("a post-release tag")
        expected.append("'dev'")
        return tuple(expected)

    def following_tags(self, current: _SegmentKind) -> tuple[str, ...]:
        if current is _SegmentKind.PRE:
            return *self.post_tags, "dev"
        if current is _SegmentKind.POST:
            return ("dev",)
        return ()

    def is_at_tag(self, tags: tuple[str, ...]) -> bool:
        return self.cursor.is_at_any(tags)

    def non_strict_pre_tag_at_cursor(self) -> str | None:
        return self.non_strict_pre_tag_at_index(self.cursor.index)

    def non_strict_pre_tag_at_index(self, index: int) -> str | None:
        if not self.strict:
            return None

        version_lower = self.version.lower()
        for tag in PRE_TAG:
            if not version_lower.startswith(tag, index):
                continue
            found = self.version[index : index + len(tag)]
            if tag not in PRE_TAG_STRICT or found != tag:
                return found

        return None

    def non_strict_segment_error_at_cursor(
        self,
        *,
        after_release_separator: bool,
    ) -> StrictParseError | None:
        if not self.strict:
            return None

        index = self.cursor.index
        non_strict_pre_tag = self.non_strict_pre_tag_at_index(index)
        if non_strict_pre_tag is not None:
            return StrictPreTagError(
                version=self.version,
                index=index,
                tag=non_strict_pre_tag,
            )

        if after_release_separator:
            return self.non_strict_tag_error_at_index(
                index=index,
                kind="post-release",
                tags=POST_TAG,
                strict_tags=POST_TAG_STRICT,
                canonical_tag="post",
            ) or self.non_strict_tag_error_at_index(
                index=index,
                kind="development release",
                tags=DEV_TAG,
                strict_tags=DEV_TAG,
                canonical_tag="dev",
            )

        separator = self.cursor.text[index] if index < len(self.version) else ""
        tag_index = index + 1 if separator in SEPARATOR else index
        separator_error = None
        if separator == "-":
            implicit_post_error = self.non_strict_implicit_post_error_at_index(
                index=index,
            )
            if implicit_post_error is not None:
                return implicit_post_error

        if separator in "-_.":
            separator_error = self.non_strict_separator_error_at_index(
                index=index,
                separator=separator,
                tag_index=tag_index,
            )
            if separator_error is not None:
                return separator_error

        missing_separator_error = self.non_strict_missing_separator_error_at_index(
            index=tag_index,
        )
        if missing_separator_error is not None:
            return missing_separator_error

        return self.non_strict_tag_error_at_index(
            index=tag_index,
            kind="post-release",
            tags=POST_TAG,
            strict_tags=POST_TAG_STRICT,
            canonical_tag="post",
        ) or self.non_strict_tag_error_at_index(
            index=tag_index,
            kind="development release",
            tags=DEV_TAG,
            strict_tags=DEV_TAG,
            canonical_tag="dev",
        )

    def non_strict_separator_error_at_index(
        self,
        *,
        index: int,
        separator: str,
        tag_index: int,
    ) -> StrictSegmentError | None:
        if not self.strict:
            return None

        pre_tag = self.pre_tag_at_index(tag_index)
        if pre_tag is not None:
            normalized_tag = _normalize_pre_tag(pre_tag)
            if normalized_tag is not None and normalized_tag != pre_tag:
                fix = f"omit the separator and use {normalized_tag!r} in strict mode"
            else:
                fix = "omit the separator in strict mode"
            return StrictSegmentError(
                version=self.version,
                index=index,
                message=(
                    f"Separator {separator!r} before pre-release tag {pre_tag!r} "
                    f"is not allowed in strict mode at position {index}; "
                    f"{fix}"
                ),
            )

        if separator == ".":
            return None

        post_tag = self.tag_at_index(tag_index, POST_TAG)
        if post_tag is not None:
            return StrictSegmentError(
                version=self.version,
                index=index,
                message=(
                    f"Separator {separator!r} before post-release tag {post_tag!r} "
                    f"is not allowed in strict mode at position {index}; "
                    "use '.' in strict mode"
                ),
            )

        dev_tag = self.tag_at_index(tag_index, DEV_TAG)
        if dev_tag is not None:
            return StrictSegmentError(
                version=self.version,
                index=index,
                message=(
                    f"Separator {separator!r} before development release tag "
                    f"{dev_tag!r} is not allowed in strict mode at position "
                    f"{index}; use '.' in strict mode"
                ),
            )

        return None

    def non_strict_number_separator_error_at_index(
        self,
        *,
        index: int,
        context: str,
    ) -> StrictSegmentError | None:
        if not self.strict:
            return None

        separator = self.version[index]
        number_start = index + 1
        if number_start >= len(self.version) or not is_ascii_digit(
            self.version[number_start]
        ):
            return None

        return StrictSegmentError(
            version=self.version,
            index=index,
            message=(
                f"Separator {separator!r} before the {context} number is not "
                f"allowed in strict mode at position {index}; omit the "
                "separator in strict mode"
            ),
        )

    def non_strict_implicit_post_error_at_index(
        self,
        *,
        index: int,
    ) -> StrictSegmentError | None:
        if not self.strict:
            return None

        number_start = index + 1
        number_end = number_start
        while number_end < len(self.version) and is_ascii_digit(
            self.version[number_end]
        ):
            number_end += 1

        if number_end == number_start:
            return None

        number = self.version[number_start:number_end]
        canonical_number = str(int(number))
        return StrictSegmentError(
            version=self.version,
            index=index,
            message=(
                f"Implicit post-release shorthand '-{number}' is not allowed "
                f"in strict mode at position {index}; use "
                f"'.post{canonical_number}' in strict mode"
            ),
        )

    def non_strict_tag_error_at_index(
        self,
        *,
        index: int,
        kind: str,
        tags: tuple[str, ...],
        strict_tags: tuple[str, ...],
        canonical_tag: str,
    ) -> StrictSegmentError | None:
        if not self.strict:
            return None

        tag = self.tag_at_index(index, tags)
        if tag is None:
            return None
        if tag.lower() in strict_tags and tag == tag.lower():
            return None
        return StrictSegmentError(
            version=self.version,
            index=index,
            message=(
                f"{kind.capitalize()} tag {tag!r} is not allowed in strict "
                f"mode at position {index}; use {canonical_tag!r} in strict mode"
            ),
        )

    def non_strict_missing_separator_error_at_index(
        self,
        *,
        index: int,
    ) -> StrictSegmentError | None:
        if not self.strict:
            return None

        post_tag = self.tag_at_index(index, POST_TAG)
        if post_tag is not None:
            return StrictSegmentError(
                version=self.version,
                index=index,
                message=(
                    f"Post-release tag {post_tag!r} without a leading '.' is "
                    f"not allowed in strict mode at position {index}; "
                    "use '.post' in strict mode"
                ),
            )

        dev_tag = self.tag_at_index(index, DEV_TAG)
        if dev_tag is not None:
            return StrictSegmentError(
                version=self.version,
                index=index,
                message=(
                    f"Development release tag {dev_tag!r} without a leading '.' "
                    f"is not allowed in strict mode at position {index}; "
                    "use '.dev' in strict mode"
                ),
            )

        return None

    def pre_tag_at_index(self, index: int) -> str | None:
        return self.tag_at_index(index, PRE_TAG)

    def tag_at_index(self, index: int, tags: tuple[str, ...]) -> str | None:
        version_lower = self.version.lower()
        for tag in tags:
            if version_lower.startswith(tag, index):
                return self.version[index : index + len(tag)]
        return None

    def expected_after_segments(
        self,
        pre: _PreSegment | None,
        post: _PostSegment | None,
        dev: _DevSegment | None,
        local: str | None,
    ) -> tuple[str, ...]:
        if local is not None:
            return ("end of version",)
        if dev is not None:
            return (self.local_segment_expected(), "end of version")
        if post is not None:
            return (
                self.dev_segment_expected(),
                self.local_segment_expected(),
                "end of version",
            )
        if pre is not None:
            return (
                self.post_segment_expected(),
                self.dev_segment_expected(),
                self.local_segment_expected(),
                "end of version",
            )
        return (
            self.pre_segment_expected(),
            self.post_segment_expected(),
            self.dev_segment_expected(),
            self.local_segment_expected(),
            "end of version",
        )

    def pre_segment_expected(self) -> str:
        if self.strict:
            return "a pre-release segment ('a', 'b', or 'rc')"
        return "a pre-release segment"

    def post_segment_expected(self) -> str:
        if self.strict:
            return "a post-release segment ('.post')"
        return "a post-release segment"

    def dev_segment_expected(self) -> str:
        if self.strict:
            return "a development release segment ('.dev')"
        return "a development release segment"

    def local_segment_expected(self) -> str:
        return "a local version segment ('+')"

    def finish(
        self,
        *,
        expected: Iterable[str],
        allow_non_strict_pre_tag: bool,
    ) -> None:
        if not self.cursor.is_done():
            diagnostic = self.diagnostics.error(self.version)
            if diagnostic is not None and diagnostic.index >= self.cursor.index:
                raise diagnostic
            if allow_non_strict_pre_tag:
                non_strict_error = self.non_strict_segment_error_at_cursor(
                    after_release_separator=False,
                )
                if non_strict_error is not None:
                    raise non_strict_error
            raise UnexpectedInputError(
                version=self.version,
                index=self.cursor.index,
                expected=expected,
            )
